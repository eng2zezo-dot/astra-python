"""Configuration management for Astra Headend."""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import asdict
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manage Astra Headend configuration."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize config manager.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.headend = None
        
        if config_file:
            self.load_config(config_file)
        
        logger.info("Config Manager initialized")

    def load_config(self, file_path: str) -> bool:
        """Load configuration from file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            True if loaded successfully
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"Config file not found: {file_path}")
                return False
            
            with open(path, 'r') as f:
                if path.suffix.lower() == '.yaml' or path.suffix.lower() == '.yml':
                    self.config = yaml.safe_load(f) or {}
                elif path.suffix.lower() == '.json':
                    self.config = json.load(f)
                else:
                    logger.error(f"Unsupported config format: {path.suffix}")
                    return False
            
            logger.info(f"Loaded config from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False

    def save_config(self, file_path: str) -> bool:
        """Save configuration to file.
        
        Args:
            file_path: Path to save configuration
            
        Returns:
            True if saved successfully
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                if path.suffix.lower() == '.yaml' or path.suffix.lower() == '.yml':
                    yaml.dump(self.config, f, default_flow_style=False)
                elif path.suffix.lower() == '.json':
                    json.dump(self.config, f, indent=2)
                else:
                    logger.error(f"Unsupported config format: {path.suffix}")
                    return False
            
            logger.info(f"Saved config to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation: "section.key")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default

    def set(self, key: str, value: Any):
        """Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Configuration value
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"Set config {key} = {value}")

    def apply_to_headend(self, headend) -> bool:
        """Apply configuration to Headend instance.
        
        Args:
            headend: AstraHeadend instance
            
        Returns:
            True if applied successfully
        """
        try:
            self.headend = headend
            
            # Load channels
            channels_config = self.config.get('channels', {})
            for channel_name, channel_data in channels_config.items():
                from astra.core.headend import Channel
                channel = Channel(
                    name=channel_name,
                    service_id=channel_data.get('service_id'),
                    video_pid=channel_data.get('video_pid'),
                    audio_pids=channel_data.get('audio_pids', []),
                    pmt_pid=channel_data.get('pmt_pid'),
                )
                headend.add_channel(channel)
            
            # Load input sources
            sources_config = self.config.get('inputs', {})
            for source_name, source_data in sources_config.items():
                from astra.core.headend import InputSource, SourceType
                source = InputSource(
                    name=source_name,
                    source_type=SourceType(source_data.get('type')),
                    uri=source_data.get('uri'),
                    adapter=source_data.get('adapter'),
                    frequency=source_data.get('frequency'),
                    symbol_rate=source_data.get('symbol_rate'),
                )
                headend.add_input_source(source)
            
            # Load output targets
            outputs_config = self.config.get('outputs', {})
            for output_name, output_data in outputs_config.items():
                from astra.core.headend import OutputTarget, OutputType
                output = OutputTarget(
                    name=output_name,
                    output_type=OutputType(output_data.get('type')),
                    uri=output_data.get('uri'),
                    channels=output_data.get('channels', []),
                )
                headend.add_output_target(output)
            
            logger.info("Configuration applied to Headend")
            return True
        except Exception as e:
            logger.error(f"Error applying config: {e}")
            return False

    def export_from_headend(self, headend) -> Dict:
        """Export Headend configuration.
        
        Args:
            headend: AstraHeadend instance
            
        Returns:
            Configuration dictionary
        """
        self.config = headend.to_dict()
        return self.config.copy()

    def get_all(self) -> Dict:
        """Get all configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()

    def __repr__(self) -> str:
        return f"ConfigManager(file={self.config_file})"
