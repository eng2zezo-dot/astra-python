"""TS Remapping - Change PIDs and Service IDs."""

from typing import Dict, List, Optional
from collections import defaultdict
from astra.core.transport_stream import TransportStream
from astra.core.packet import TSPacket
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class PIDRemapper:
    """Remap PIDs in Transport Stream."""

    def __init__(self, transport_stream: TransportStream):
        """Initialize remapper.
        
        Args:
            transport_stream: TransportStream to remap
        """
        self.ts = transport_stream
        self.pid_map: Dict[int, int] = {}  # old_pid -> new_pid
        self.service_id_map: Dict[int, int] = {}  # old_sid -> new_sid

    def add_pid_mapping(self, old_pid: int, new_pid: int):
        """Add PID mapping.
        
        Args:
            old_pid: Old PID
            new_pid: New PID
        """
        if new_pid in self.pid_map.values():
            logger.warning(f"New PID {new_pid:04x} already in use")
        
        self.pid_map[old_pid] = new_pid
        logger.debug(f"Added PID mapping: {old_pid:04x} -> {new_pid:04x}")

    def add_service_id_mapping(self, old_sid: int, new_sid: int):
        """Add Service ID mapping.
        
        Args:
            old_sid: Old Service ID
            new_sid: New Service ID
        """
        self.service_id_map[old_sid] = new_sid
        logger.debug(f"Added SID mapping: {old_sid} -> {new_sid}")

    def apply_pid_remapping(self) -> int:
        """Apply PID remapping to TS.
        
        Returns:
            Number of packets remapped
        """
        count = 0
        for packet in self.ts.packets:
            if packet.pid in self.pid_map:
                packet.pid = self.pid_map[packet.pid]
                count += 1
        
        logger.info(f"Applied PID remapping: {count} packets")
        return count

    def apply_service_id_remapping(self) -> int:
        """Apply Service ID remapping (requires PMT parsing).
        
        Returns:
            Number of services remapped
        """
        # This requires parsing PMT sections
        logger.info("Service ID remapping (simplified - requires PMT parsing)")
        return 0

    def get_pid_map(self) -> Dict[int, int]:
        """Get current PID mappings.
        
        Returns:
            Dictionary of PID mappings
        """
        return self.pid_map.copy()

    def reset(self):
        """Reset all mappings."""
        self.pid_map.clear()
        self.service_id_map.clear()
        logger.info("Remapper reset")

    def __repr__(self) -> str:
        return f"PIDRemapper(mappings={len(self.pid_map)})"
