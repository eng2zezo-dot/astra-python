"""Transport Stream processing and manipulation."""

import struct
from typing import Dict, List, Optional, Callable, Tuple
from collections import defaultdict
from astra.core.packet import TSPacket, AdaptationFieldFlag
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class TransportStream:
    """MPEG-2 Transport Stream processor."""

    def __init__(self):
        """Initialize Transport Stream."""
        self.packets: List[TSPacket] = []
        self.continuity_counters: Dict[int, int] = defaultdict(int)
        self.pid_handlers: Dict[int, List[Callable]] = defaultdict(list)
        self.packet_count = 0
        self.error_count = 0
        self.filtered_pids = set()

    def add_packet(self, data: bytes) -> bool:
        """Add a TS packet to the stream.
        
        Args:
            data: Raw 188-byte packet data
            
        Returns:
            True if packet is valid, False otherwise
        """
        try:
            packet = TSPacket(data)
            if not packet.is_valid():
                self.error_count += 1
                logger.warning(f"Invalid sync byte in packet")
                return False
            
            self.packets.append(packet)
            self.packet_count += 1
            
            # Check continuity counter
            self._check_continuity(packet)
            
            # Call registered handlers
            self._handle_packet(packet)
            
            return True
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error adding packet: {e}")
            return False

    def _check_continuity(self, packet: TSPacket):
        """Check packet continuity counter.
        
        Args:
            packet: TS packet to check
        """
        pid = packet.pid
        expected = (self.continuity_counters[pid] + 1) & 0x0F
        actual = packet.continuity_counter
        
        if packet.adaptation_field_control not in (AdaptationFieldFlag.NO_ADAPTATION,):
            # Update expected for packets with payload or adaptation field
            self.continuity_counters[pid] = actual
        
        if expected != actual and self.continuity_counters[pid] != 0:
            logger.debug(f"Continuity counter error on PID {pid:04x}: "
                        f"expected {expected}, got {actual}")

    def register_pid_handler(self, pid: int, handler: Callable[[TSPacket], None]):
        """Register a handler for specific PID.
        
        Args:
            pid: PID to register handler for
            handler: Callable to handle packets with this PID
        """
        self.pid_handlers[pid].append(handler)

    def _handle_packet(self, packet: TSPacket):
        """Call registered handlers for packet.
        
        Args:
            packet: TS packet to handle
        """
        pid = packet.pid
        for handler in self.pid_handlers[pid]:
            try:
                handler(packet)
            except Exception as e:
                logger.error(f"Error in PID handler for {pid:04x}: {e}")

    def filter_pids(self, keep_pids: List[int], add_psi: bool = True):
        """Filter TS to keep only specific PIDs.
        
        Args:
            keep_pids: List of PIDs to keep
            add_psi: Whether to keep PSI tables (PAT, PMT, SDT, etc.)
        """
        psi_pids = {0x00, 0x01, 0x10, 0x11, 0x12, 0x13, 0x14}  # Common PSI PIDs
        
        if add_psi:
            keep_pids = list(set(keep_pids) | psi_pids)
        
        self.filtered_pids = set(keep_pids)
        filtered_packets = []
        
        for packet in self.packets:
            if packet.pid in self.filtered_pids:
                filtered_packets.append(packet)
        
        self.packets = filtered_packets
        logger.info(f"Filtered TS: {len(self.packets)} packets, PIDs: {sorted(self.filtered_pids)}")

    def remap_pid(self, old_pid: int, new_pid: int) -> int:
        """Remap PID in all packets.
        
        Args:
            old_pid: Old PID to replace
            new_pid: New PID to use
            
        Returns:
            Number of packets remapped
        """
        count = 0
        for packet in self.packets:
            if packet.pid == old_pid:
                packet.pid = new_pid
                count += 1
        
        logger.info(f"Remapped PID {old_pid:04x} -> {new_pid:04x}: {count} packets")
        return count

    def remove_scrambling(self, pids: Optional[List[int]] = None):
        """Remove scrambling control from packets.
        
        Args:
            pids: List of PIDs to remove scrambling from. If None, all PIDs.
        """
        count = 0
        target_pids = set(pids) if pids else None
        
        for packet in self.packets:
            if target_pids is None or packet.pid in target_pids:
                if packet.scrambling_control != 0:
                    packet.scrambling_control = 0
                    count += 1
        
        logger.info(f"Removed scrambling from {count} packets")
        return count

    def set_scrambling(self, pids: List[int], control: int):
        """Set scrambling control on packets.
        
        Args:
            pids: List of PIDs to scramble
            control: Scrambling control value (1-3)
        """
        if not 1 <= control <= 3:
            raise ValueError(f"Scrambling control must be 1-3, got {control}")
        
        count = 0
        target_pids = set(pids)
        
        for packet in self.packets:
            if packet.pid in target_pids:
                packet.scrambling_control = control
                count += 1
        
        logger.info(f"Set scrambling {control} on {count} packets")
        return count

    def get_pids(self) -> List[int]:
        """Get list of unique PIDs in stream.
        
        Returns:
            Sorted list of PIDs
        """
        return sorted(set(p.pid for p in self.packets))

    def get_pid_statistics(self) -> Dict[int, Dict]:
        """Get statistics for each PID.
        
        Returns:
            Dictionary with PID statistics
        """
        stats = defaultdict(lambda: {
            'count': 0,
            'errors': 0,
            'scrambled': 0,
            'continuity_errors': 0
        })
        
        for packet in self.packets:
            pid = packet.pid
            stats[pid]['count'] += 1
            
            if packet.transport_error_indicator:
                stats[pid]['errors'] += 1
            
            if packet.scrambling_control != 0:
                stats[pid]['scrambled'] += 1
        
        return dict(stats)

    def get_bytes(self) -> bytes:
        """Get entire TS as bytes.
        
        Returns:
            Concatenated packet data
        """
        return b''.join(p.get_bytes() for p in self.packets)

    def clear(self):
        """Clear all packets."""
        self.packets.clear()
        self.continuity_counters.clear()
        self.packet_count = 0
        self.error_count = 0

    def get_statistics(self) -> Dict:
        """Get stream statistics.
        
        Returns:
            Dictionary with stream statistics
        """
        return {
            'total_packets': self.packet_count,
            'current_packets': len(self.packets),
            'errors': self.error_count,
            'unique_pids': len(self.get_pids()),
            'pids': self.get_pids(),
            'pid_stats': self.get_pid_statistics(),
        }

    def __len__(self) -> int:
        """Get number of packets in stream."""
        return len(self.packets)

    def __repr__(self) -> str:
        return f"TransportStream({len(self.packets)} packets, PIDs: {self.get_pids()})"
