"""TS Filtering - Remove unwanted channels and PIDs."""

from typing import List, Set, Optional
from astra.core.transport_stream import TransportStream
from astra.core.packet import TSPacket
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class ChannelFilter:
    """Filter Transport Stream to keep only desired channels."""

    def __init__(self, transport_stream: TransportStream):
        """Initialize filter.
        
        Args:
            transport_stream: TransportStream to filter
        """
        self.ts = transport_stream
        self.keep_pids: Set[int] = set()
        self.remove_pids: Set[int] = set()
        self.keep_psi = True  # Keep PSI tables (PAT, PMT, SDT, etc.)
        self.psi_pids = {0x00, 0x01, 0x10, 0x11, 0x12, 0x13, 0x14}  # Common PSI PIDs

    def add_keep_pid(self, pid: int):
        """Add PID to keep list.
        
        Args:
            pid: PID to keep
        """
        self.keep_pids.add(pid)

    def add_keep_pids(self, pids: List[int]):
        """Add multiple PIDs to keep list.
        
        Args:
            pids: List of PIDs to keep
        """
        self.keep_pids.update(pids)

    def add_remove_pid(self, pid: int):
        """Add PID to remove list.
        
        Args:
            pid: PID to remove
        """
        self.remove_pids.add(pid)

    def add_remove_pids(self, pids: List[int]):
        """Add multiple PIDs to remove list.
        
        Args:
            pids: List of PIDs to remove
        """
        self.remove_pids.update(pids)

    def set_keep_psi(self, keep: bool):
        """Set whether to keep PSI tables.
        
        Args:
            keep: True to keep PSI tables
        """
        self.keep_psi = keep

    def apply(self) -> int:
        """Apply filter to TS.
        
        Returns:
            Number of packets kept
        """
        pids_to_keep = self.keep_pids.copy()
        
        if self.keep_psi:
            pids_to_keep.update(self.psi_pids)
        
        # Remove explicitly excluded PIDs
        pids_to_keep.difference_update(self.remove_pids)
        
        filtered = []
        for packet in self.ts.packets:
            if packet.pid in pids_to_keep:
                filtered.append(packet)
        
        before_count = len(self.ts.packets)
        self.ts.packets = filtered
        
        kept = len(self.ts.packets)
        removed = before_count - kept
        
        logger.info(f"Filter applied: kept {kept} packets, removed {removed}")
        logger.info(f"Keeping PIDs: {sorted(pids_to_keep)}")
        
        return kept

    def filter_by_service_id(self, service_ids: List[int]) -> int:
        """Filter by service ID (from PMT).
        
        Args:
            service_ids: List of service IDs to keep
            
        Returns:
            Number of packets kept
        """
        # This would require PMT parsing to map service IDs to PIDs
        # Simplified implementation
        logger.info(f"Filtering by service IDs: {service_ids}")
        return len(self.ts.packets)

    def remove_audio_pid(self, pid: int) -> int:
        """Remove audio PID.
        
        Args:
            pid: Audio PID to remove
            
        Returns:
            Number of packets removed
        """
        count = 0
        filtered = []
        for packet in self.ts.packets:
            if packet.pid != pid:
                filtered.append(packet)
            else:
                count += 1
        
        self.ts.packets = filtered
        logger.info(f"Removed audio PID {pid:04x}: {count} packets")
        return count

    def remove_subtitle_pid(self, pid: int) -> int:
        """Remove subtitle PID.
        
        Args:
            pid: Subtitle PID to remove
            
        Returns:
            Number of packets removed
        """
        count = 0
        filtered = []
        for packet in self.ts.packets:
            if packet.pid != pid:
                filtered.append(packet)
            else:
                count += 1
        
        self.ts.packets = filtered
        logger.info(f"Removed subtitle PID {pid:04x}: {count} packets")
        return count

    def remove_teletext(self) -> int:
        """Remove teletext PIDs (typically 0x18, 0x19).
        
        Returns:
            Number of packets removed
        """
        teletext_pids = {0x18, 0x19}
        count = 0
        filtered = []
        
        for packet in self.ts.packets:
            if packet.pid not in teletext_pids:
                filtered.append(packet)
            else:
                count += 1
        
        self.ts.packets = filtered
        logger.info(f"Removed teletext: {count} packets")
        return count

    def __repr__(self) -> str:
        return (f"ChannelFilter(keep={len(self.keep_pids)}, "
                f"remove={len(self.remove_pids)})")
