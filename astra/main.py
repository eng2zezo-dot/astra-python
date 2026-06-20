"""Main application entry point for Astra Headend."""

import sys
import argparse
import time
from pathlib import Path

from astra.core.headend import AstraHeadend, Channel, InputSource, OutputTarget, SourceType, OutputType
from astra.api.rest_api import AstraAPI
from astra.config.config_manager import ConfigManager
from astra.monitoring.monitor import SystemMonitor
from astra.failover.backup_manager import BackupManager
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class AstraApplication:
    """Main Astra Headend Application."""

    def __init__(self, config_file: str = None):
        """Initialize application.
        
        Args:
            config_file: Path to configuration file
        """
        self.headend = AstraHeadend(config_file)
        self.config_manager = ConfigManager(config_file)
        self.api_server = None
        self.monitor = None
        self.backup_manager = None
        
        logger.info("Astra Headend Application initialized")

    def initialize(self, config_file: str = None) -> bool:
        """Initialize application from config.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            True if initialized successfully
        """
        try:
            if config_file:
                if self.config_manager.load_config(config_file):
                    self.config_manager.apply_to_headend(self.headend)
                else:
                    logger.warning("Failed to load config, continuing with defaults")
            
            # Initialize monitoring
            self.monitor = SystemMonitor(self.headend)
            self.monitor.start()
            
            # Initialize backup manager
            self.backup_manager = BackupManager()
            
            logger.info("Application initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False

    def start_api(self, host: str = '0.0.0.0', port: int = 5000):
        """Start REST API server.
        
        Args:
            host: API server host
            port: API server port
        """
        try:
            self.api_server = AstraAPI(self.headend, host, port)
            self.api_server.start()
            logger.info(f"REST API started: http://{host}:{port}")
        except Exception as e:
            logger.error(f"Error starting API: {e}")

    def start_system(self):
        """Start Headend system."""
        try:
            self.headend.start()
            logger.info("Headend system started")
        except Exception as e:
            logger.error(f"Error starting system: {e}")

    def stop_system(self):
        """Stop Headend system."""
        try:
            self.headend.stop()
            if self.monitor:
                self.monitor.stop()
            if self.backup_manager:
                self.backup_manager.stop()
            logger.info("Headend system stopped")
        except Exception as e:
            logger.error(f"Error stopping system: {e}")

    def show_status(self):
        """Display system status."""
        status = self.headend.get_status()
        print("\n" + "="*60)
        print("ASTRA HEADEND STATUS")
        print("="*60)
        print(f"Running: {status['running']}")
        print(f"Uptime: {status['uptime']:.1f}s")
        print(f"Channels: {status['channels']}")
        print(f"Input Sources: {status['input_sources']}")
        print(f"Output Targets: {status['output_targets']}")
        print("\nStatistics:")
        stats = status.get('stats', {})
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("="*60 + "\n")

    def show_channels(self):
        """Display all channels."""
        channels = self.headend.list_channels()
        print("\n" + "="*60)
        print("CHANNELS")
        print("="*60)
        for ch in channels:
            print(f"Name: {ch.name}")
            print(f"  Service ID: {ch.service_id}")
            print(f"  Video PID: {ch.video_pid}")
            print(f"  Audio PIDs: {ch.audio_pids}")
            print(f"  Enabled: {ch.enabled}")
            print()
        print("="*60 + "\n")

    def show_sources(self):
        """Display all input sources."""
        sources = self.headend.list_input_sources()
        print("\n" + "="*60)
        print("INPUT SOURCES")
        print("="*60)
        for src in sources:
            print(f"Name: {src.name}")
            print(f"  Type: {src.source_type.value}")
            print(f"  URI: {src.uri}")
            print(f"  Enabled: {src.enabled}")
            print()
        print("="*60 + "\n")

    def show_outputs(self):
        """Display all output targets."""
        outputs = self.headend.list_output_targets()
        print("\n" + "="*60)
        print("OUTPUT TARGETS")
        print("="*60)
        for out in outputs:
            print(f"Name: {out.name}")
            print(f"  Type: {out.output_type.value}")
            print(f"  URI: {out.uri}")
            print(f"  Channels: {out.channels}")
            print()
        print("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Astra Headend - MPEG-2 TS Processing System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config.yaml
  %(prog)s --api 0.0.0.0 5000
  %(prog)s --status
  %(prog)s --channels
        """
    )
    
    parser.add_argument('-c', '--config', help='Configuration file (YAML/JSON)')
    parser.add_argument('-a', '--api', nargs=2, metavar=('HOST', 'PORT'),
                       help='Start REST API server')
    parser.add_argument('-s', '--status', action='store_true',
                       help='Show system status')
    parser.add_argument('--channels', action='store_true',
                       help='List all channels')
    parser.add_argument('--sources', action='store_true',
                       help='List all input sources')
    parser.add_argument('--outputs', action='store_true',
                       help='List all output targets')
    parser.add_argument('--start', action='store_true',
                       help='Start the system')
    parser.add_argument('--stop', action='store_true',
                       help='Stop the system')
    parser.add_argument('-v', '--version', action='version', version='Astra 1.0')
    
    args = parser.parse_args()
    
    # Initialize application
    app = AstraApplication()
    app.initialize(args.config)
    
    try:
        # Handle commands
        if args.api:
            host = args.api[0]
            port = int(args.api[1])
            app.start_api(host, port)
        
        if args.start:
            app.start_system()
        
        if args.status:
            app.show_status()
        
        if args.channels:
            app.show_channels()
        
        if args.sources:
            app.show_sources()
        
        if args.outputs:
            app.show_outputs()
        
        if args.stop:
            app.stop_system()
        
        # If API is running and no stop command, keep running
        if args.api:
            print(f"\nAPI Server running at http://{args.api[0]}:{args.api[1]}")
            print("Press Ctrl+C to stop...\n")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
                app.stop_system()
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
