"""Unit tests for Astra Headend core components."""

import unittest
from astra.core.packet import TSPacket, AdaptationFieldFlag
from astra.core.transport_stream import TransportStream
from astra.processing.filter import ChannelFilter
from astra.processing.remapper import PIDRemapper


class TestTSPacket(unittest.TestCase):
    """Test TS Packet handling."""

    def test_packet_creation(self):
        """Test creating a new packet."""
        packet = TSPacket()
        self.assertEqual(packet.sync_byte, TSPacket.SYNC_BYTE)
        self.assertEqual(len(packet.get_bytes()), TSPacket.PACKET_SIZE)

    def test_packet_pid(self):
        """Test PID operations."""
        packet = TSPacket()
        packet.pid = 0x0100
        self.assertEqual(packet.pid, 0x0100)
        
        packet.pid = 0x1FFF  # Max PID
        self.assertEqual(packet.pid, 0x1FFF)

    def test_packet_scrambling(self):
        """Test scrambling control."""
        packet = TSPacket()
        packet.scrambling_control = 1
        self.assertEqual(packet.scrambling_control, 1)
        
        packet.scrambling_control = 0
        self.assertEqual(packet.scrambling_control, 0)

    def test_packet_continuity_counter(self):
        """Test continuity counter."""
        packet = TSPacket()
        for i in range(16):
            packet.continuity_counter = i
            self.assertEqual(packet.continuity_counter, i)


class TestTransportStream(unittest.TestCase):
    """Test Transport Stream handling."""

    def test_ts_creation(self):
        """Test creating a transport stream."""
        ts = TransportStream()
        self.assertEqual(len(ts.packets), 0)

    def test_add_packet(self):
        """Test adding packets."""
        ts = TransportStream()
        packet_data = bytearray(TSPacket.PACKET_SIZE)
        packet_data[0] = TSPacket.SYNC_BYTE
        
        result = ts.add_packet(bytes(packet_data))
        self.assertTrue(result)
        self.assertEqual(len(ts.packets), 1)

    def test_get_pids(self):
        """Test getting PIDs from stream."""
        ts = TransportStream()
        
        for pid in [0x100, 0x101, 0x100]:
            packet_data = bytearray(TSPacket.PACKET_SIZE)
            packet_data[0] = TSPacket.SYNC_BYTE
            packet_data[1] = (packet_data[1] & 0xE0) | ((pid >> 8) & 0x1F)
            packet_data[2] = pid & 0xFF
            ts.add_packet(bytes(packet_data))
        
        pids = ts.get_pids()
        self.assertEqual(len(pids), 2)
        self.assertIn(0x100, pids)
        self.assertIn(0x101, pids)


class TestChannelFilter(unittest.TestCase):
    """Test Channel Filter."""

    def setUp(self):
        """Set up test fixtures."""
        self.ts = TransportStream()
        
        # Add packets with different PIDs
        for pid in [0x100, 0x101, 0x102]:
            for _ in range(10):
                packet_data = bytearray(TSPacket.PACKET_SIZE)
                packet_data[0] = TSPacket.SYNC_BYTE
                packet_data[1] = (packet_data[1] & 0xE0) | ((pid >> 8) & 0x1F)
                packet_data[2] = pid & 0xFF
                self.ts.add_packet(bytes(packet_data))
    
    def test_filter_keep_pid(self):
        """Test filtering to keep specific PID."""
        filter_obj = ChannelFilter(self.ts)
        filter_obj.add_keep_pid(0x100)
        filter_obj.apply()
        
        # Should only have PID 0x100 + PSI PIDs
        pids = self.ts.get_pids()
        self.assertIn(0x100, pids)

    def test_filter_remove_pid(self):
        """Test filtering to remove specific PID."""
        filter_obj = ChannelFilter(self.ts)
        filter_obj.add_remove_pid(0x102)
        filter_obj.apply()
        
        pids = self.ts.get_pids()
        self.assertNotIn(0x102, pids)


class TestPIDRemapper(unittest.TestCase):
    """Test PID Remapper."""

    def setUp(self):
        """Set up test fixtures."""
        self.ts = TransportStream()
        
        # Add packets with specific PIDs
        for _ in range(10):
            packet_data = bytearray(TSPacket.PACKET_SIZE)
            packet_data[0] = TSPacket.SYNC_BYTE
            packet_data[1] = (packet_data[1] & 0xE0) | ((0x100 >> 8) & 0x1F)
            packet_data[2] = 0x100 & 0xFF
            self.ts.add_packet(bytes(packet_data))
    
    def test_pid_remapping(self):
        """Test remapping PIDs."""
        remapper = PIDRemapper(self.ts)
        remapper.add_pid_mapping(0x100, 0x200)
        remapper.apply_pid_remapping()
        
        pids = self.ts.get_pids()
        self.assertNotIn(0x100, pids)
        self.assertIn(0x200, pids)


if __name__ == '__main__':
    unittest.main()
