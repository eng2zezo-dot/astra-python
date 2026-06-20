"""UDP Multicast output for TS delivery."""

import socket
import threading
from typing import Optional, List
from astra.core.transport_stream import TransportStream
from astra.utils.logger import get_logger
from astra.utils.helpers import parse_uri, is_multicast_ip

logger = get_logger(__name__)


class UDPMulticastOutput:
    """Send TS via UDP Multicast."""

    def __init__(self, uri: str, ttl: int = 32, buffer_size: int = 65536):
        """Initialize UDP Multicast output.
        
        Args:
            uri: Destination URI (udp://239.1.1.1:5000)
            ttl: Time to live
            buffer_size: Send buffer size
        """
        self.uri = uri
        self.parsed = parse_uri(uri)
        self.ttl = ttl
        self.buffer_size = buffer_size
        self.socket = None
        self.running = False
        self.packets_sent = 0
        self.errors = 0
        
        # Validate multicast address
        host = self.parsed['hostname']
        if not is_multicast_ip(host):
            logger.warning(f"{host} is not a multicast address")
        
        logger.info(f"UDP Multicast Output initialized for {uri}")

    def start(self) -> bool:
        """Start UDP output.
        
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Already running")
            return False
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.buffer_size)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
            
            self.running = True
            logger.info(f"UDP Multicast output started: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to start UDP output: {e}")
            return False

    def send_ts(self, ts: TransportStream, rate_limit: Optional[int] = None) -> int:
        """Send TS via UDP.
        
        Args:
            ts: TransportStream to send
            rate_limit: Optional bitrate limit in bps
            
        Returns:
            Number of packets sent
        """
        if not self.running or not self.socket:
            logger.error("Output not running")
            return 0
        
        host = self.parsed['hostname']
        port = self.parsed['port'] or 5000
        
        try:
            data = ts.get_bytes()
            self.socket.sendto(data, (host, port))
            self.packets_sent += len(ts.packets)
            logger.debug(f"Sent {len(ts.packets)} packets to {host}:{port}")
            return len(ts.packets)
        except Exception as e:
            self.errors += 1
            logger.error(f"Send error: {e}")
            return 0

    def stop(self):
        """Stop UDP output."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        logger.info(f"UDP output stopped. Packets sent: {self.packets_sent}, "
                   f"Errors: {self.errors}")

    def get_statistics(self) -> dict:
        """Get output statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'uri': self.uri,
            'packets_sent': self.packets_sent,
            'errors': self.errors,
            'running': self.running,
        }

    def __repr__(self) -> str:
        return f"UDPMulticastOutput({self.uri})"
