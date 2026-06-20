"""RTSP server for TS streaming."""

import socket
import threading
from typing import Optional
from astra.core.transport_stream import TransportStream
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class RTSPServer:
    """RTSP server for streaming TS content."""

    def __init__(self, host: str = '0.0.0.0', port: int = 554):
        """Initialize RTSP server.
        
        Args:
            host: Server host
            port: Server port (default 554 for RTSP)
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.packets_sent = 0
        self.errors = 0
        self.streams = {}  # stream_name -> stream_data
        
        logger.info(f"RTSP Server initialized: {host}:{port}")

    def start(self) -> bool:
        """Start RTSP server.
        
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Already running")
            return False
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            
            self.server_thread = threading.Thread(
                target=self._server_loop,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info(f"RTSP server started: rtsp://{self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start RTSP server: {e}")
            self.running = False
            return False

    def _server_loop(self):
        """Main server loop."""
        try:
            while self.running:
                try:
                    client, addr = self.server_socket.accept()
                    logger.debug(f"RTSP client connected: {addr}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client, addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
        except Exception as e:
            logger.error(f"Server loop error: {e}")
        finally:
            self.running = False

    def _handle_client(self, client_socket: socket.socket, addr):
        """Handle individual RTSP client.
        
        Args:
            client_socket: Client socket
            addr: Client address
        """
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # Parse RTSP request (simplified)
                request = data.decode('utf-8', errors='ignore')
                
                if 'DESCRIBE' in request:
                    response = self._handle_describe(request)
                elif 'SETUP' in request:
                    response = self._handle_setup(request)
                elif 'PLAY' in request:
                    response = self._handle_play(request)
                elif 'TEARDOWN' in request:
                    response = self._handle_teardown(request)
                else:
                    response = "RTSP/1.0 400 Bad Request\r\n\r\n"
                
                client_socket.sendall(response.encode())
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _handle_describe(self, request: str) -> str:
        """Handle DESCRIBE request.
        
        Args:
            request: RTSP request
            
        Returns:
            RTSP response
        """
        response = (
            "RTSP/1.0 200 OK\r\n"
            "CSeq: 1\r\n"
            "Content-Type: application/sdp\r\n"
            "\r\n"
            "v=0\r\n"
            "o=astra 0 0 IN IP4 127.0.0.1\r\n"
            "s=Astra Stream\r\n"
            "t=0 0\r\n"
            "m=video 0 RTP/AVP 96\r\n"
        )
        return response

    def _handle_setup(self, request: str) -> str:
        """Handle SETUP request.
        
        Args:
            request: RTSP request
            
        Returns:
            RTSP response
        """
        response = (
            "RTSP/1.0 200 OK\r\n"
            "CSeq: 2\r\n"
            "Transport: RTP/AVP;unicast;client_port=5000-5001\r\n"
            "Session: 12345\r\n"
            "\r\n"
        )
        return response

    def _handle_play(self, request: str) -> str:
        """Handle PLAY request.
        
        Args:
            request: RTSP request
            
        Returns:
            RTSP response
        """
        response = (
            "RTSP/1.0 200 OK\r\n"
            "CSeq: 3\r\n"
            "Range: npt=0-\r\n"
            "Session: 12345\r\n"
            "\r\n"
        )
        return response

    def _handle_teardown(self, request: str) -> str:
        """Handle TEARDOWN request.
        
        Args:
            request: RTSP request
            
        Returns:
            RTSP response
        """
        response = (
            "RTSP/1.0 200 OK\r\n"
            "CSeq: 4\r\n"
            "Session: 12345\r\n"
            "\r\n"
        )
        return response

    def add_stream(self, name: str, ts: TransportStream):
        """Add stream to RTSP server.
        
        Args:
            name: Stream name
            ts: TransportStream
        """
        self.streams[name] = ts
        logger.info(f"Added RTSP stream: {name}")

    def stop(self):
        """Stop RTSP server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info(f"RTSP server stopped. Total packets sent: {self.packets_sent}")

    def get_statistics(self) -> dict:
        """Get server statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'host': self.host,
            'port': self.port,
            'streams': len(self.streams),
            'packets_sent': self.packets_sent,
            'errors': self.errors,
            'running': self.running,
        }

    def __repr__(self) -> str:
        return f"RTSPServer({self.host}:{self.port})"
