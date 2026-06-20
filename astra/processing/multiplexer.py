"""TS Multiplexing - Combine multiple streams."""

from typing import List, Dict, Optional
from astra.core.transport_stream import TransportStream
from astra.core.packet import TSPacket, AdaptationFieldFlag
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class Multiplexer:
    """Multiplex multiple TS streams into single output."""

    def __init__(self):
        """Initialize multiplexer."""
        self.input_streams: Dict[str, TransportStream] = {}
        self.output_stream = TransportStream()
        self.continuity_counters: Dict[int, int] = {}
        self.pid_remap: Dict[tuple, int] = {}  # (source_name, old_pid) -> new_pid

    def add_input_stream(self, name: str, stream: TransportStream):
        """Add input TS stream.
        
        Args:
            name: Stream identifier
            stream: TransportStream to add
        """
        self.input_streams[name] = stream
        logger.info(f"Added input stream: {name}")

    def remove_input_stream(self, name: str):
        """Remove input TS stream.
        
        Args:
            name: Stream identifier
        """
        if name in self.input_streams:
            del self.input_streams[name]
            logger.info(f"Removed input stream: {name}")

    def multiplex(self) -> TransportStream:
        """Multiplex all input streams.
        
        Returns:
            Multiplexed TransportStream
        """
        self.output_stream.clear()
        packets_added = 0
        
        for source_name, stream in self.input_streams.items():
            for packet in stream.packets:
                # Handle PID remapping if configured
                key = (source_name, packet.pid)
                if key in self.pid_remap:
                    packet.pid = self.pid_remap[key]
                
                # Update continuity counter to maintain order
                self._update_continuity(packet)
                
                self.output_stream.packets.append(packet)
                packets_added += 1
        
        logger.info(f"Multiplexed {packets_added} packets from "
                   f"{len(self.input_streams)} streams")
        return self.output_stream

    def _update_continuity(self, packet: TSPacket):
        """Update packet continuity counter.
        
        Args:
            packet: TS packet
        """
        pid = packet.pid
        
        if packet.adaptation_field_control not in (
            AdaptationFieldFlag.NO_ADAPTATION,
        ):
            expected = (self.continuity_counters.get(pid, 0) + 1) & 0x0F
            packet.continuity_counter = expected
            self.continuity_counters[pid] = expected

    def set_pid_remap(self, source: str, old_pid: int, new_pid: int):
        """Set PID remapping for specific source.
        
        Args:
            source: Source stream name
            old_pid: Old PID
            new_pid: New PID
        """
        self.pid_remap[(source, old_pid)] = new_pid
        logger.debug(f"Set remap for {source}: {old_pid:04x} -> {new_pid:04x}")

    def get_output_pids(self) -> List[int]:
        """Get all PIDs in output stream.
        
        Returns:
            List of PIDs
        """
        return self.output_stream.get_pids()

    def get_statistics(self) -> Dict:
        """Get multiplexing statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'input_streams': len(self.input_streams),
            'output_packets': len(self.output_stream.packets),
            'output_pids': self.output_stream.get_pids(),
            'remap_rules': len(self.pid_remap),
        }

    def __repr__(self) -> str:
        return f"Multiplexer(inputs={len(self.input_streams)})"
