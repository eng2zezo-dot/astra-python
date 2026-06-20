"""HLS (HTTP Live Streaming) output for TS delivery."""

import os
import time
import threading
from typing import Optional
from pathlib import Path
from astra.core.transport_stream import TransportStream
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class HLSOutput:
    """Generate HLS streams from TS."""

    def __init__(self, output_dir: str, segment_duration: int = 10, 
                 segment_count: int = 3, bitrate: Optional[int] = None):
        """Initialize HLS output.
        
        Args:
            output_dir: Directory to store HLS files
            segment_duration: Duration of each segment in seconds
            segment_count: Number of segments to keep
            bitrate: Optional bitrate in bps
        """
        self.output_dir = Path(output_dir)
        self.segment_duration = segment_duration
        self.segment_count = segment_count
        self.bitrate = bitrate
        self.running = False
        self.packets_sent = 0
        self.errors = 0
        self.segment_index = 0
        self.current_segment_data = bytearray()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"HLS Output initialized: {output_dir}")

    def start(self) -> bool:
        """Start HLS output.
        
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Already running")
            return False
        
        try:
            self.running = True
            logger.info(f"HLS output started: {self.output_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to start HLS output: {e}")
            return False

    def send_ts(self, ts: TransportStream) -> int:
        """Send TS and generate HLS segments.
        
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
            self.current_segment_data.extend(data)
            self.packets_sent += len(ts.packets)
            
            # Check if segment is ready
            # Simplified: use packet count instead of time
            packets_per_segment = (self.segment_duration * 20000000) // (188 * 8)  # Approximate
            
            if len(ts.packets) >= 100:  # Write segment after 100 packets
                self._write_segment()
                self.current_segment_data = bytearray()
            
            return len(ts.packets)
        except Exception as e:
            self.errors += 1
            logger.error(f"Send error: {e}")
            return 0

    def _write_segment(self):
        """Write HLS segment to file."""
        try:
            # Write segment file
            segment_file = self.output_dir / f"segment_{self.segment_index}.ts"
            with open(segment_file, 'wb') as f:
                f.write(self.current_segment_data)
            
            logger.debug(f"Wrote segment: {segment_file}")
            
            # Update playlist
            self._update_playlist()
            
            # Remove old segments
            self._cleanup_old_segments()
            
            self.segment_index += 1
        except Exception as e:
            logger.error(f"Error writing segment: {e}")
            self.errors += 1

    def _update_playlist(self):
        """Update HLS playlist file."""
        try:
            playlist_file = self.output_dir / "playlist.m3u8"
            
            lines = [
                '#EXTM3U',
                '#EXT-X-VERSION:3',
                f'#EXT-X-TARGETDURATION:{self.segment_duration}',
                '#EXT-X-MEDIA-SEQUENCE:0',
            ]
            
            # Add segments
            for i in range(max(0, self.segment_index - self.segment_count), self.segment_index):
                lines.append(f'#EXTINF:{self.segment_duration}.0,')
                lines.append(f'segment_{i}.ts')
            
            with open(playlist_file, 'w') as f:
                f.write('\n'.join(lines) + '\n')
            
            logger.debug(f"Updated playlist: {playlist_file}")
        except Exception as e:
            logger.error(f"Error updating playlist: {e}")

    def _cleanup_old_segments(self):
        """Remove old segment files."""
        try:
            # Remove segments older than segment_count
            for i in range(0, max(0, self.segment_index - self.segment_count)):
                segment_file = self.output_dir / f"segment_{i}.ts"
                if segment_file.exists():
                    segment_file.unlink()
                    logger.debug(f"Removed old segment: {segment_file}")
        except Exception as e:
            logger.error(f"Error cleaning segments: {e}")

    def stop(self):
        """Stop HLS output."""
        self.running = False
        
        # Write final segment
        if self.current_segment_data:
            self._write_segment()
        
        logger.info(f"HLS output stopped. Packets sent: {self.packets_sent}, "
                   f"Errors: {self.errors}")

    def get_statistics(self) -> dict:
        """Get output statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'output_dir': str(self.output_dir),
            'segment_index': self.segment_index,
            'packets_sent': self.packets_sent,
            'errors': self.errors,
            'running': self.running,
        }

    def __repr__(self) -> str:
        return f"HLSOutput({self.output_dir})"
