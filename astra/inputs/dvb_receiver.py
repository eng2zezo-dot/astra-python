"""DVB Receiver for DVB-S/C/T input."""

import socket
import struct
import threading
from typing import Optional, Callable
from datetime import datetime

from astra.utils.logger import get_logger
from astra.core.transport_stream import TransportStream
from astra.core.packet import TSPacket

logger = get_logger(__name__)


class DVBReceiver:
    """Receives MPEG-2 TS from DVB adapters."""

    def __init__(self, adapter: int = 0):
        """Initialize DVB receiver.
        
        Args:
            adapter: DVB adapter number (0, 1, 2, ...)
        """
        self.adapter = adapter
        self.device = f"/dev/dvb/adapter{adapter}/dvr0"
        self.socket = None
        self.running = False
        self.transport_stream = TransportStream()
        self.packet_count = 0
        self.error_count = 0
        self.on_packet: Optional[Callable[[TSPacket], None]] = None
        
        logger.info(f"DVB Receiver initialized for adapter {adapter}")

    def tune(self, frequency: int, symbol_rate: int, modulation: str = "QPSK",
             fec: str = "5/6") -> bool:
        """Tune to frequency.
        
        Args:
            frequency: Frequency in MHz
            symbol_rate: Symbol rate in symbols/second
            modulation: Modulation type (QPSK, PSK8, etc.)
            fec: Forward error correction (5/6, 3/4, etc.)
            
        Returns:
            True if tuned successfully
        """
        try:
            logger.info(f"Tuning DVB adapter {self.adapter} to {frequency} MHz, "
                       f"SR: {symbol_rate}, MOD: {modulation}, FEC: {fec}")
            # In a real implementation, this would use DVB API via file descriptor
            # For now, we'll simulate it
            self.frequency = frequency
            self.symbol_rate = symbol_rate
            self.modulation = modulation
            self.fec = fec
            return True
        except Exception as e:
            logger.error(f"Failed to tune: {e}")
            return False

    def start_receiving(self) -> bool:
        """Start receiving TS from DVB.
        
        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Already receiving")
            return False
        
        try:
            logger.info(f"Starting reception from {self.device}")
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start receiving: {e}")
            self.running = False
            return False

    def _receive_loop(self):
        """Main receiving loop."""
        try:
            with open(self.device, 'rb') as f:
                while self.running:
                    data = f.read(TSPacket.PACKET_SIZE)
                    if len(data) == TSPacket.PACKET_SIZE:
                        if self.transport_stream.add_packet(data):
                            self.packet_count += 1
                            if self.on_packet:
                                packet = TSPacket(data)
                                self.on_packet(packet)
                        else:
                            self.error_count += 1
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            self.running = False

    def stop_receiving(self):
        """Stop receiving TS."""
        self.running = False
        logger.info(f"Stopped reception. Total packets: {self.packet_count}, "
                   f"Errors: {self.error_count}")

    def get_signal_info(self) -> dict:
        """Get signal information.
        
        Returns:
            Signal information dictionary
        """
        # This would query DVB API for real signal info
        return {
            'adapter': self.adapter,
            'frequency': getattr(self, 'frequency', None),
            'symbol_rate': getattr(self, 'symbol_rate', None),
            'signal_strength': 0,  # 0-100
            'snr': 0,  # dB
            'ber': 0,  # Bit Error Rate
        }

    def get_statistics(self) -> dict:
        """Get reception statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'adapter': self.adapter,
            'packets_received': self.packet_count,
            'errors': self.error_count,
            'ts_info': self.transport_stream.get_statistics(),
        }

    def __repr__(self) -> str:
        return f"DVBReceiver(adapter={self.adapter}, running={self.running})"
