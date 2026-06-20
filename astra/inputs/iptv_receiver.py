"""IPTV Receiver for IP-based streams."""

import socket
import threading
from typing import Optional, Callable
import requests
from urllib.parse import urlparse

from astra.utils.logger import get_logger
from astra.core.transport_stream import TransportStream
from astra.core.packet import TSPacket
from astra.utils.helpers import parse_uri, is_multicast_ip

logger = get_logger(__name__)


class IPTVReceiver:
    """Receives MPEG-2 TS from IPTV sources."""

    def __init__(self, uri: str):
        """Initialize IPTV receiver.
        
        Args:
            uri: Source URI (udp://, rtp://, http://, etc.)
        """
        self.uri = uri
        self.parsed = parse_uri(uri)
        self.socket = None
        self.running = False
        self.transport_stream = TransportStream()
        self.packet_count = 0
        self.error_count = 0
        self.on_packet: Optional[Callable[[TSPacket], None]] = None
        self.scheme = self.parsed['scheme'].lower()
        
        logger.info(f"IPTV Receiver initialized for {uri}")

    def start_receiving(self) -> bool:
        """Start receiving TS from IPTV.
        
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Already receiving")
            return False
        
        try:
            logger.info(f"Starting reception from {self.uri}")
            self.running = True
            
            if self.scheme in ('udp', 'rtp'):
                self.receive_thread = threading.Thread(
                    target=self._receive_udp_loop, daemon=True
                )
            elif self.scheme in ('http', 'https'):
                self.receive_thread = threading.Thread(
                    target=self._receive_http_loop, daemon=True
                )
            else:
                logger.error(f"Unsupported scheme: {self.scheme}")
                return False
            
            self.receive_thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start receiving: {e}")
            self.running = False
            return False

    def _receive_udp_loop(self):
        """Receive loop for UDP/RTP."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            host = self.parsed['hostname']
            port = self.parsed['port'] or 5000
            
            # Join multicast group if needed
            if is_multicast_ip(host):
                self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                      socket.inet_aton(host) + socket.inet_aton('0.0.0.0'))
            
            self.socket.bind(('', port))
            logger.info(f"Listening on {host}:{port}")
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(65536)
                    
                    # For RTP, skip RTP header (12 bytes minimum)
                    if self.scheme == 'rtp' and len(data) > 12:
                        data = data[12:]
                    
                    # Process TS packets
                    offset = 0
                    while offset + TSPacket.PACKET_SIZE <= len(data):
                        packet_data = data[offset:offset + TSPacket.PACKET_SIZE]
                        if self.transport_stream.add_packet(packet_data):
                            self.packet_count += 1
                            if self.on_packet:
                                packet = TSPacket(packet_data)
                                self.on_packet(packet)
                        else:
                            self.error_count += 1
                        offset += TSPacket.PACKET_SIZE
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error in UDP receive: {e}")
                    self.error_count += 1
        except Exception as e:
            logger.error(f"UDP receive loop error: {e}")
        finally:
            if self.socket:
                self.socket.close()

    def _receive_http_loop(self):
        """Receive loop for HTTP/HTTPS."""
        try:
            response = requests.get(self.uri, stream=True, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"HTTP error: {response.status_code}")
                self.running = False
                return
            
            logger.info(f"Connected to {self.uri}")
            
            buffer = b''
            for chunk in response.iter_content(chunk_size=188*10):
                if not self.running:
                    break
                
                buffer += chunk
                
                # Process complete packets
                while len(buffer) >= TSPacket.PACKET_SIZE:
                    # Find sync byte
                    sync_pos = -1
                    for i in range(len(buffer) - TSPacket.PACKET_SIZE):
                        if buffer[i] == 0x47:
                            sync_pos = i
                            break
                    
                    if sync_pos < 0:
                        buffer = b''
                        break
                    
                    if sync_pos > 0:
                        buffer = buffer[sync_pos:]
                    
                    packet_data = buffer[:TSPacket.PACKET_SIZE]
                    
                    if self.transport_stream.add_packet(packet_data):
                        self.packet_count += 1
                        if self.on_packet:
                            packet = TSPacket(packet_data)
                            self.on_packet(packet)
                    else:
                        self.error_count += 1
                    
                    buffer = buffer[TSPacket.PACKET_SIZE:]
        except Exception as e:
            logger.error(f"HTTP receive loop error: {e}")
        finally:
            self.running = False

    def stop_receiving(self):
        """Stop receiving TS."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        logger.info(f"Stopped reception. Total packets: {self.packet_count}, "
                   f"Errors: {self.error_count}")

    def get_statistics(self) -> dict:
        """Get reception statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'uri': self.uri,
            'scheme': self.scheme,
            'packets_received': self.packet_count,
            'errors': self.error_count,
            'ts_info': self.transport_stream.get_statistics(),
        }

    def __repr__(self) -> str:
        return f"IPTVReceiver(uri={self.uri}, running={self.running})"
