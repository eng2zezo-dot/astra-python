"""Astra Headend main system."""

import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from astra.utils.logger import get_logger

logger = get_logger(__name__)


class SourceType(Enum):
    """Input source types."""
    DVB_S = "dvb-s"      # Satellite
    DVB_C = "dvb-c"      # Cable
    DVB_T = "dvb-t"      # Terrestrial
    IPTV = "iptv"        # IP TV
    RTSP = "rtsp"        # RTSP stream
    SAT_IP = "sat-ip"    # SAT>IP


class OutputType(Enum):
    """Output delivery types."""
    UDP = "udp"
    HTTP = "http"
    HLS = "hls"
    SRT = "srt"
    RTSP = "rtsp"
    FILE = "file"


@dataclass
class Channel:
    """TV Channel configuration."""
    name: str
    service_id: int
    video_pid: Optional[int] = None
    audio_pids: List[int] = field(default_factory=list)
    subtitle_pids: List[int] = field(default_factory=list)
    pmt_pid: Optional[int] = None
    enabled: bool = True
    scrambled: bool = False
    target_pid: Optional[int] = None  # For remapping
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'service_id': self.service_id,
            'video_pid': self.video_pid,
            'audio_pids': self.audio_pids,
            'subtitle_pids': self.subtitle_pids,
            'pmt_pid': self.pmt_pid,
            'enabled': self.enabled,
            'scrambled': self.scrambled,
            'target_pid': self.target_pid,
        }


@dataclass
class InputSource:
    """Input source configuration."""
    name: str
    source_type: SourceType
    uri: str
    enabled: bool = True
    backup_uri: Optional[str] = None
    retry_count: int = 3
    retry_interval: int = 5  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    
    # DVB specific
    adapter: Optional[int] = None
    frequency: Optional[int] = None
    symbol_rate: Optional[int] = None
    modulation: Optional[str] = None
    fec: Optional[str] = None
    
    # Additional parameters
    extra_params: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.source_type.value,
            'uri': self.uri,
            'enabled': self.enabled,
            'backup_uri': self.backup_uri,
            'adapter': self.adapter,
            'frequency': self.frequency,
            'symbol_rate': self.symbol_rate,
            'modulation': self.modulation,
            'fec': self.fec,
        }


@dataclass
class OutputTarget:
    """Output target configuration."""
    name: str
    output_type: OutputType
    uri: str
    enabled: bool = True
    bitrate: Optional[int] = None
    channels: List[str] = field(default_factory=list)  # Channel names
    created_at: datetime = field(default_factory=datetime.now)
    
    # Additional parameters
    extra_params: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.output_type.value,
            'uri': self.uri,
            'enabled': self.enabled,
            'bitrate': self.bitrate,
            'channels': self.channels,
        }


class AstraHeadend:
    """Main Astra Headend system."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Astra Headend.
        
        Args:
            config_path: Path to configuration file
        """
        self.channels: Dict[str, Channel] = {}
        self.input_sources: Dict[str, InputSource] = {}
        self.output_targets: Dict[str, OutputTarget] = {}
        
        self.running = False
        self.lock = threading.RLock()
        self.start_time = None
        
        # Statistics
        self.stats = {
            'packets_received': 0,
            'packets_sent': 0,
            'errors': 0,
            'uptime': 0,
        }
        
        logger.info("Astra Headend initialized")

    def add_channel(self, channel: Channel) -> bool:
        """Add a TV channel.
        
        Args:
            channel: Channel configuration
            
        Returns:
            True if added successfully
        """
        with self.lock:
            if channel.name in self.channels:
                logger.warning(f"Channel '{channel.name}' already exists")
                return False
            
            self.channels[channel.name] = channel
            logger.info(f"Added channel: {channel.name} (SID: {channel.service_id})")
            return True

    def remove_channel(self, name: str) -> bool:
        """Remove a TV channel.
        
        Args:
            name: Channel name
            
        Returns:
            True if removed successfully
        """
        with self.lock:
            if name not in self.channels:
                logger.warning(f"Channel '{name}' not found")
                return False
            
            del self.channels[name]
            logger.info(f"Removed channel: {name}")
            return True

    def get_channel(self, name: str) -> Optional[Channel]:
        """Get channel by name.
        
        Args:
            name: Channel name
            
        Returns:
            Channel object or None if not found
        """
        return self.channels.get(name)

    def list_channels(self) -> List[Channel]:
        """List all channels.
        
        Returns:
            List of channels
        """
        with self.lock:
            return list(self.channels.values())

    def add_input_source(self, source: InputSource) -> bool:
        """Add an input source.
        
        Args:
            source: Input source configuration
            
        Returns:
            True if added successfully
        """
        with self.lock:
            if source.name in self.input_sources:
                logger.warning(f"Input source '{source.name}' already exists")
                return False
            
            self.input_sources[source.name] = source
            logger.info(f"Added input source: {source.name} ({source.source_type.value})")
            return True

    def remove_input_source(self, name: str) -> bool:
        """Remove an input source.
        
        Args:
            name: Source name
            
        Returns:
            True if removed successfully
        """
        with self.lock:
            if name not in self.input_sources:
                logger.warning(f"Input source '{name}' not found")
                return False
            
            del self.input_sources[name]
            logger.info(f"Removed input source: {name}")
            return True

    def list_input_sources(self) -> List[InputSource]:
        """List all input sources.
        
        Returns:
            List of input sources
        """
        with self.lock:
            return list(self.input_sources.values())

    def add_output_target(self, target: OutputTarget) -> bool:
        """Add an output target.
        
        Args:
            target: Output target configuration
            
        Returns:
            True if added successfully
        """
        with self.lock:
            if target.name in self.output_targets:
                logger.warning(f"Output target '{target.name}' already exists")
                return False
            
            self.output_targets[target.name] = target
            logger.info(f"Added output target: {target.name} ({target.output_type.value})")
            return True

    def remove_output_target(self, name: str) -> bool:
        """Remove an output target.
        
        Args:
            name: Target name
            
        Returns:
            True if removed successfully
        """
        with self.lock:
            if name not in self.output_targets:
                logger.warning(f"Output target '{name}' not found")
                return False
            
            del self.output_targets[name]
            logger.info(f"Removed output target: {name}")
            return True

    def list_output_targets(self) -> List[OutputTarget]:
        """List all output targets.
        
        Returns:
            List of output targets
        """
        with self.lock:
            return list(self.output_targets.values())

    def start(self):
        """Start the Headend system."""
        with self.lock:
            if self.running:
                logger.warning("Headend is already running")
                return
            
            self.running = True
            self.start_time = time.time()
            logger.info("Astra Headend started")

    def stop(self):
        """Stop the Headend system."""
        with self.lock:
            if not self.running:
                logger.warning("Headend is not running")
                return
            
            self.running = False
            logger.info("Astra Headend stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get system status.
        
        Returns:
            Status dictionary
        """
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            'running': self.running,
            'uptime': uptime,
            'channels': len(self.channels),
            'input_sources': len(self.input_sources),
            'output_targets': len(self.output_targets),
            'stats': self.stats.copy(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            'channels': {k: v.to_dict() for k, v in self.channels.items()},
            'input_sources': {k: v.to_dict() for k, v in self.input_sources.items()},
            'output_targets': {k: v.to_dict() for k, v in self.output_targets.items()},
        }

    def __repr__(self) -> str:
        return (f"AstraHeadend(channels={len(self.channels)}, "
                f"sources={len(self.input_sources)}, "
                f"outputs={len(self.output_targets)}, "
                f"running={self.running})")
