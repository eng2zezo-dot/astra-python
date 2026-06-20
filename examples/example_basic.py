"""Basic example - Setting up channels and inputs."""

from astra.core.headend import AstraHeadend, Channel, InputSource, OutputTarget, SourceType, OutputType
from astra.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run basic example."""
    
    # Create Headend instance
    headend = AstraHeadend()
    
    # Add channels
    logger.info("Adding channels...")
    
    channel1 = Channel(
        name="BBC One",
        service_id=4101,
        video_pid=0x0100,
        audio_pids=[0x0101, 0x0102],
    )
    headend.add_channel(channel1)
    
    channel2 = Channel(
        name="BBC Two",
        service_id=4102,
        video_pid=0x0200,
        audio_pids=[0x0201],
    )
    headend.add_channel(channel2)
    
    # Add input sources
    logger.info("Adding input sources...")
    
    dvb_source = InputSource(
        name="Satellite Input",
        source_type=SourceType.DVB_S,
        uri="dvb://adapter0",
        adapter=0,
        frequency=11462000,
        symbol_rate=22000000,
    )
    headend.add_input_source(dvb_source)
    
    # Add output targets
    logger.info("Adding output targets...")
    
    udp_output = OutputTarget(
        name="UDP Multicast",
        output_type=OutputType.UDP,
        uri="udp://239.1.1.100:5000",
        channels=["BBC One", "BBC Two"],
    )
    headend.add_output_target(udp_output)
    
    # Display configuration
    logger.info("\nConfiguration:")
    config = headend.to_dict()
    
    print(f"Channels: {len(config['channels'])}")
    for name, ch in config['channels'].items():
        print(f"  - {name}: SID={ch['service_id']}")
    
    print(f"\nInput Sources: {len(config['input_sources'])}")
    for name, src in config['input_sources'].items():
        print(f"  - {name}: {src['type']}")
    
    print(f"\nOutput Targets: {len(config['output_targets'])}")
    for name, out in config['output_targets'].items():
        print(f"  - {name}: {out['type']}")
    
    # Start system
    headend.start()
    status = headend.get_status()
    print(f"\nSystem running: {status['running']}")
    print(f"Uptime: {status['uptime']:.1f}s")
    
    headend.stop()


if __name__ == '__main__':
    main()
