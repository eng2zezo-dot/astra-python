"""TS Scrambling/Encryption support."""

from typing import List, Optional
from astra.core.transport_stream import TransportStream
from astra.core.packet import TSPacket
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class Scrambler:
    """Handle TS packet scrambling/encryption."""

    # Scrambling control values
    SCRAMBLING_NOT_SCRAMBLED = 0
    SCRAMBLING_DVB_CSA1 = 1  # DVB CSA (CSA1)
    SCRAMBLING_DVB_CSA2 = 2  # DVB CSA (CSA2)
    SCRAMBLING_RESERVED = 3

    def __init__(self, transport_stream: TransportStream):
        """Initialize scrambler.
        
        Args:
            transport_stream: TransportStream to process
        """
        self.ts = transport_stream
        self.scramble_map: dict = {}  # pid -> scrambling_control
        self.ci_enabled = False  # Conditional Access enabled
        self.ecm_pid = None  # Entitlement Control Message PID
        self.emm_pid = None  # Entitlement Management Message PID

    def set_scrambling(self, pids: List[int], scrambling_control: int) -> int:
        """Set scrambling control for PIDs.
        
        Args:
            pids: List of PIDs to scramble
            scrambling_control: Scrambling method (1-3)
            
        Returns:
            Number of packets scrambled
        """
        if not 1 <= scrambling_control <= 3:
            raise ValueError(f"Invalid scrambling control: {scrambling_control}")
        
        target_pids = set(pids)
        count = 0
        
        for packet in self.ts.packets:
            if packet.pid in target_pids:
                packet.scrambling_control = scrambling_control
                self.scramble_map[packet.pid] = scrambling_control
                count += 1
        
        logger.info(f"Set scrambling {scrambling_control} on {count} packets")
        return count

    def remove_scrambling(self, pids: Optional[List[int]] = None) -> int:
        """Remove scrambling from packets.
        
        Args:
            pids: PIDs to descramble. If None, all PIDs.
            
        Returns:
            Number of packets descrambled
        """
        target_pids = set(pids) if pids else None
        count = 0
        
        for packet in self.ts.packets:
            if target_pids is None or packet.pid in target_pids:
                if packet.scrambling_control != 0:
                    packet.scrambling_control = 0
                    self.scramble_map[packet.pid] = 0
                    count += 1
        
        logger.info(f"Removed scrambling from {count} packets")
        return count

    def enable_ca(self, ecm_pid: int, emm_pid: int):
        """Enable Conditional Access.
        
        Args:
            ecm_pid: ECM (Entitlement Control Message) PID
            emm_pid: EMM (Entitlement Management Message) PID
        """
        self.ci_enabled = True
        self.ecm_pid = ecm_pid
        self.emm_pid = emm_pid
        logger.info(f"CA enabled: ECM={ecm_pid:04x}, EMM={emm_pid:04x}")

    def disable_ca(self):
        """Disable Conditional Access."""
        self.ci_enabled = False
        logger.info("CA disabled")

    def get_scrambling_status(self) -> dict:
        """Get scrambling status for all PIDs.
        
        Returns:
            Dictionary with PID scrambling status
        """
        status = {}
        for pid in self.ts.get_pids():
            scrambled = any(p.scrambling_control != 0 for p in self.ts.packets 
                          if p.pid == pid)
            status[f"{pid:04x}"] = {
                'pid': pid,
                'scrambled': scrambled,
                'control': self.scramble_map.get(pid, 0),
            }
        return status

    def __repr__(self) -> str:
        return f"Scrambler(ca_enabled={self.ci_enabled})"
