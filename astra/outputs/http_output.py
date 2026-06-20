"""HTTP Streaming output for TS delivery."""

import socket
import threading
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from astra.core.transport_stream import TransportStream
from astra.utils.logger import get_logger
from astra.utils.helpers import parse_uri

logger = get_logger(__name__)


class HTTPStreamHandler(BaseHTTPRequestHandler):
    """HTTP request handler for TS streaming."""
    
    # Class variable to share TS data
    ts_data = None
    
    def do_GET(self):
        """Handle GET request."""
        if self.path == '/stream' or self.path == '/':
            if self.ts_data:
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp2t')
                self.send_header('Content-Length', len(self.ts_data))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(self.ts_data)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class HTTPStreamingOutput:
    """Send TS via HTTP streaming."""

    def __init__(self, uri: str, host: str = '0.0.0.0', port: int = 8000):
        """Initialize HTTP streaming output.
        
        Args:
            uri: Output URI
            host: HTTP server host
            port: HTTP server port
        """
        self.uri = uri
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        self.packets_sent = 0
        self.errors = 0
        
        logger.info(f"HTTP Streaming Output initialized: {host}:{port}")

    def start(self) -> bool:
        """Start HTTP server.
        
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Already running")
            return False
        
        try:
            self.server = HTTPServer((self.host, self.port), HTTPStreamHandler)
            self.running = True
            
            self.server_thread = threading.Thread(
                target=self._server_loop,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info(f"HTTP server started: http://{self.host}:{self.port}/stream")
            return True
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            self.running = False
            return False

    def _server_loop(self):
        """Run HTTP server loop."""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
        finally:
            self.running = False

    def send_ts(self, ts: TransportStream) -> int:
        """Send TS via HTTP.
        
        Args:
            ts: TransportStream to send
            
        Returns:
            Number of packets sent
        """
        if not self.running:
            logger.error("Output not running")
            return 0
        
        try:
            HTTPStreamHandler.ts_data = ts.get_bytes()
            self.packets_sent += len(ts.packets)
            logger.debug(f"HTTP stream updated: {len(ts.packets)} packets")
            return len(ts.packets)
        except Exception as e:
            self.errors += 1
            logger.error(f"Send error: {e}")
            return 0

    def stop(self):
        """Stop HTTP server."""
        self.running = False
        if self.server:
            try:
                self.server.shutdown()
            except:
                pass
        logger.info(f"HTTP output stopped. Packets sent: {self.packets_sent}, "
                   f"Errors: {self.errors}")

    def get_statistics(self) -> dict:
        """Get output statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'uri': self.uri,
            'host': self.host,
            'port': self.port,
            'packets_sent': self.packets_sent,
            'errors': self.errors,
            'running': self.running,
        }

    def __repr__(self) -> str:
        return f"HTTPStreamingOutput({self.host}:{self.port})"
