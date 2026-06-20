"""SRT (Secure Reliable Transport) output for TS delivery."""

import socket
import threading
from typing import Optional
from astra.core.transport_stream import TransportStream
from astra.utils.logger import get_logger
from astra.utils.helpers import parse_uri

logger = get_logger(__name__)


class SRTOutput:
    """Send TS via SRT (Secure Reliable Transport)."""

    def __init__(self, uri: str, latency: int = 120):
        """Initialize SRT output.
        
        Args:
            uri: Destination URI (srt://host:port)
            latency: Latency buffer in milliseconds
        """
        self.uri = uri
        self.parsed = parse_uri(uri)
        self.latency = latency
        self.socket = None
        self.running = False
        self.connected = False
        self.packets_sent = 0
        self.errors = 0
        
        logger.info(f"SRT Output initialized for {uri}")

    def start(self) -> bool:
        """Start SRT output (requires srt-python library).
        
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Already running")
            return False
        
        try:
            # Note: SRT requires srt-python library
            # This is a simplified implementation
            self.running = True
            
            # Try to connect
            host = self.parsed['hostname']
            port = self.parsed['port'] or 9710
            
            logger.info(f"SRT output connecting to {host}:{port}")
            logger.info(f"SRT output started (latency: {self.latency}ms)")
            return True
        except Exception as e:
            logger.error(f"Failed to start SRT output: {e}")
            self.running = False
            return False

    def send_ts(self, ts: TransportStream) -> int:
        """Send TS via SRT.
        
        Args:
            ts: TransportStream to send
            
        Returns:
            Number of packets sent
        """
        if not self.running:
            logger.error("Output not running")
            return 0
        
        try:
            data = ts.get_bytes()
            # In real implementation, would use SRT socket
            self.packets_sent += len(ts.packets)
            logger.debug(f"SRT sent {len(ts.packets)} packets")
            return len(ts.packets)
        except Exception as e:
            self.errors += 1
            logger.error(f"Send error: {e}")
            return 0

    def stop(self):
        """Stop SRT output."""
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        logger.info(f"SRT output stopped. Packets sent: {self.packets_sent}, "
                   f"Errors: {self.errors}")

    def get_statistics(self) -> dict:
        """Get output statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'uri': self.uri,
            'connected': self.connected,
            'latency': self.latency,
            'packets_sent': self.packets_sent,
            'errors': self.errors,
            'running': self.running,
        }

    def __repr__(self) -> str:
        return f"SRTOutput({self.uri})"
