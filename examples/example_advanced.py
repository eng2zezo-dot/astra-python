"""Advanced example - Using filters, remapping, and multiplexing."""

from astra.core.transport_stream import TransportStream
from astra.core.packet import TSPacket
from astra.processing.filter import ChannelFilter
from astra.processing.remapper import PIDRemapper
from astra.processing.multiplexer import Multiplexer
from astra.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run advanced processing example."""
    
    logger.info("Advanced Processing Example")
    logger.info("=" * 50)
    
    # Create transport streams
    ts1 = TransportStream()
    ts2 = TransportStream()
    
    # Simulate adding packets with different PIDs
    logger.info("\nSimulating TS data...")
    
    # Create dummy packets for testing
    for i in range(100):
        packet_data = bytearray(TSPacket.PACKET_SIZE)
        packet_data[0] = 0x47  # Sync byte
        # Alternate between PID 0x100 and 0x101
        pid = 0x100 if i % 2 == 0 else 0x101
        packet_data[1] = (packet_data[1] & 0xE0) | ((pid >> 8) & 0x1F)
        packet_data[2] = pid & 0xFF
        
        ts1.add_packet(bytes(packet_data))
    
    logger.info(f"Stream 1: {len(ts1.packets)} packets, PIDs: {ts1.get_pids()}")
    
    # Example 1: Filtering
    logger.info("\n--- Example 1: Filtering ---")
    filter1 = ChannelFilter(ts1)
    filter1.add_keep_pid(0x100)
    filtered_count = filter1.apply()
    logger.info(f"Filtered stream: {len(ts1.packets)} packets")
    
    # Example 2: PID Remapping
    logger.info("\n--- Example 2: PID Remapping ---")
    ts2.packets = ts1.packets.copy()
    remapper = PIDRemapper(ts2)
    remapper.add_pid_mapping(0x100, 0x200)
    remapped_count = remapper.apply_pid_remapping()
    logger.info(f"Remapped {remapped_count} packets: 0x100 -> 0x200")
    logger.info(f"New PIDs: {ts2.get_pids()}")
    
    # Example 3: Multiplexing
    logger.info("\n--- Example 3: Multiplexing ---")
    multiplexer = Multiplexer()
    multiplexer.add_input_stream("stream1", ts1)
    multiplexer.add_input_stream("stream2", ts2)
    
    output_ts = multiplexer.multiplex()
    logger.info(f"Multiplexed stream: {len(output_ts.packets)} packets")
    logger.info(f"Output PIDs: {output_ts.get_pids()}")
    
    # Display statistics
    logger.info("\nFinal Statistics:")
    stats = output_ts.get_pid_statistics()
    for pid, pid_stats in stats.items():
        logger.info(f"  PID {pid:04x}: {pid_stats['count']} packets")


if __name__ == '__main__':
    main()
