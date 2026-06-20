"""Configuration example - Loading and applying configuration."""

from astra.core.headend import AstraHeadend
from astra.config.config_manager import ConfigManager
from astra.utils.logger import get_logger
import json

logger = get_logger(__name__)


def main():
    """Run configuration example."""
    
    logger.info("Configuration Management Example")
    logger.info("=" * 50)
    
    # Create Headend instance
    headend = AstraHeadend()
    
    # Create ConfigManager
    config_manager = ConfigManager()
    
    # Configure programmatically
    config_manager.set('channels.BBC1.service_id', 4101)
    config_manager.set('channels.BBC1.video_pid', 0x100)
    config_manager.set('channels.BBC1.audio_pids', [0x101, 0x102])
    
    config_manager.set('channels.BBC2.service_id', 4102)
    config_manager.set('channels.BBC2.video_pid', 0x200)
    config_manager.set('channels.BBC2.audio_pids', [0x201])
    
    config_manager.set('inputs.SAT.type', 'dvb-s')
    config_manager.set('inputs.SAT.uri', 'dvb://adapter0')
    config_manager.set('inputs.SAT.frequency', 11462000)
    
    config_manager.set('outputs.UDP.type', 'udp')
    config_manager.set('outputs.UDP.uri', 'udp://239.1.1.100:5000')
    
    logger.info("\nConfiguration created programmatically")
    
    # Display configuration
    config = config_manager.get_all()
    logger.info("\nConfiguration:")
    logger.info(json.dumps(config, indent=2))
    
    # Save to file
    logger.info("\nSaving configuration...")
    config_manager.save_config('examples/generated_config.json')
    logger.info("Saved to examples/generated_config.json")
    
    # Apply to Headend
    logger.info("\nApplying configuration to Headend...")
    config_manager.apply_to_headend(headend)
    
    # Display Headend status
    status = headend.get_status()
    logger.info(f"\nHeadend Status:")
    logger.info(f"  Channels: {status['channels']}")
    logger.info(f"  Sources: {status['input_sources']}")
    logger.info(f"  Outputs: {status['output_targets']}")
    
    # List channels
    logger.info("\nChannels:")
    for ch in headend.list_channels():
        logger.info(f"  - {ch.name} (SID: {ch.service_id})")


if __name__ == '__main__':
    main()
