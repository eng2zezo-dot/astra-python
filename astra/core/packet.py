"""Transport Stream Packet handling."""

import struct
from typing import Optional, List
from dataclasses import dataclass
from enum import IntEnum


class AdaptationFieldFlag(IntEnum):
    """Adaptation field flags."""
    NO_ADAPTATION = 0
    ADAPTATION_ONLY = 1
    PAYLOAD_ONLY = 2
    ADAPTATION_AND_PAYLOAD = 3


@dataclass
class AdaptationField:
    """TS Packet Adaptation Field."""
    length: int
    discontinuity: bool = False
    random_access: bool = False
    elementary_stream_priority: bool = False
    pcr_flag: bool = False
    opcr_flag: bool = False
    splicing_point_flag: bool = False
    transport_private_data_flag: bool = False
    adaptation_field_extension_flag: bool = False
    pcr: Optional[int] = None
    opcr: Optional[int] = None
    splice_countdown: Optional[int] = None
    private_data: bytes = b''


class TSPacket:
    """MPEG-2 Transport Stream Packet (188 bytes)."""

    PACKET_SIZE = 188
    SYNC_BYTE = 0x47

    def __init__(self, data: bytes = None):
        """Initialize TS packet.
        
        Args:
            data: Raw 188-byte packet data
        """
        if data is None:
            data = bytearray(self.PACKET_SIZE)
            data[0] = self.SYNC_BYTE
        elif len(data) != self.PACKET_SIZE:
            raise ValueError(f"TS packet must be exactly {self.PACKET_SIZE} bytes")
        
        self.data = bytearray(data)

    @property
    def sync_byte(self) -> int:
        """Get sync byte."""
        return self.data[0]

    @property
    def transport_error_indicator(self) -> bool:
        """Get transport error indicator."""
        return bool(self.data[1] & 0x80)

    @transport_error_indicator.setter
    def transport_error_indicator(self, value: bool):
        if value:
            self.data[1] |= 0x80
        else:
            self.data[1] &= 0x7F

    @property
    def payload_unit_start_indicator(self) -> bool:
        """Get payload unit start indicator."""
        return bool(self.data[1] & 0x40)

    @payload_unit_start_indicator.setter
    def payload_unit_start_indicator(self, value: bool):
        if value:
            self.data[1] |= 0x40
        else:
            self.data[1] &= 0xBF

    @property
    def transport_priority(self) -> bool:
        """Get transport priority."""
        return bool(self.data[1] & 0x20)

    @transport_priority.setter
    def transport_priority(self, value: bool):
        if value:
            self.data[1] |= 0x20
        else:
            self.data[1] &= 0xDF

    @property
    def pid(self) -> int:
        """Get Packet Identifier (13 bits)."""
        return ((self.data[1] & 0x1F) << 8) | self.data[2]

    @pid.setter
    def pid(self, value: int):
        if not 0 <= value <= 0x1FFF:
            raise ValueError(f"PID must be 0-8191, got {value}")
        self.data[1] = (self.data[1] & 0xE0) | ((value >> 8) & 0x1F)
        self.data[2] = value & 0xFF

    @property
    def scrambling_control(self) -> int:
        """Get scrambling control (2 bits)."""
        return (self.data[3] >> 6) & 0x03

    @scrambling_control.setter
    def scrambling_control(self, value: int):
        if not 0 <= value <= 3:
            raise ValueError(f"Scrambling control must be 0-3, got {value}")
        self.data[3] = (self.data[3] & 0x3F) | ((value & 0x03) << 6)

    @property
    def adaptation_field_control(self) -> AdaptationFieldFlag:
        """Get adaptation field control (2 bits)."""
        return AdaptationFieldFlag((self.data[3] >> 4) & 0x03)

    @adaptation_field_control.setter
    def adaptation_field_control(self, value: AdaptationFieldFlag):
        self.data[3] = (self.data[3] & 0x0F) | ((value & 0x03) << 4)

    @property
    def continuity_counter(self) -> int:
        """Get continuity counter (4 bits)."""
        return self.data[3] & 0x0F

    @continuity_counter.setter
    def continuity_counter(self, value: int):
        if not 0 <= value <= 15:
            raise ValueError(f"Continuity counter must be 0-15, got {value}")
        self.data[3] = (self.data[3] & 0xF0) | (value & 0x0F)

    @property
    def payload(self) -> bytes:
        """Get packet payload."""
        afc = self.adaptation_field_control
        if afc == AdaptationFieldFlag.NO_ADAPTATION:
            return bytes(self.data[4:])
        elif afc == AdaptationFieldFlag.PAYLOAD_ONLY:
            return bytes(self.data[4:])
        elif afc == AdaptationFieldFlag.ADAPTATION_ONLY:
            return b''
        else:  # ADAPTATION_AND_PAYLOAD
            adaptation_length = self.data[4]
            return bytes(self.data[5 + adaptation_length:])

    @payload.setter
    def payload(self, value: bytes):
        """Set packet payload."""
        afc = self.adaptation_field_control
        if afc == AdaptationFieldFlag.NO_ADAPTATION or afc == AdaptationFieldFlag.PAYLOAD_ONLY:
            if len(value) > 184:
                raise ValueError("Payload too large")
            self.data[4:4+len(value)] = value
        elif afc == AdaptationFieldFlag.ADAPTATION_AND_PAYLOAD:
            adaptation_length = self.data[4]
            start = 5 + adaptation_length
            if len(value) > self.PACKET_SIZE - start:
                raise ValueError("Payload too large")
            self.data[start:start+len(value)] = value

    def parse_adaptation_field(self) -> Optional[AdaptationField]:
        """Parse adaptation field if present."""
        afc = self.adaptation_field_control
        if afc not in (AdaptationFieldFlag.ADAPTATION_ONLY, AdaptationFieldFlag.ADAPTATION_AND_PAYLOAD):
            return None
        
        length = self.data[4]
        if length == 0:
            return AdaptationField(length=0)
        
        flags = self.data[5]
        af = AdaptationField(
            length=length,
            discontinuity=bool(flags & 0x80),
            random_access=bool(flags & 0x40),
            elementary_stream_priority=bool(flags & 0x20),
            pcr_flag=bool(flags & 0x10),
            opcr_flag=bool(flags & 0x08),
            splicing_point_flag=bool(flags & 0x04),
            transport_private_data_flag=bool(flags & 0x02),
            adaptation_field_extension_flag=bool(flags & 0x01),
        )
        
        offset = 6
        
        # Parse PCR if present
        if af.pcr_flag and length >= 6:
            pcr_base = (self.data[offset] << 25) | (self.data[offset+1] << 17) | \
                       (self.data[offset+2] << 9) | (self.data[offset+3] << 1)
            pcr_ext = ((self.data[offset+4] & 0x01) << 8) | self.data[offset+5]
            af.pcr = (pcr_base << 9) | pcr_ext
            offset += 6
        
        # Parse OPCR if present
        if af.opcr_flag and length >= offset - 5 + 6:
            opcr_base = (self.data[offset] << 25) | (self.data[offset+1] << 17) | \
                        (self.data[offset+2] << 9) | (self.data[offset+3] << 1)
            opcr_ext = ((self.data[offset+4] & 0x01) << 8) | self.data[offset+5]
            af.opcr = (opcr_base << 9) | opcr_ext
            offset += 6
        
        # Parse splice countdown if present
        if af.splicing_point_flag and length >= offset - 5 + 1:
            af.splice_countdown = self.data[offset]
            offset += 1
        
        # Get private data if present
        if af.transport_private_data_flag and offset < 5 + length:
            private_data_length = self.data[offset]
            if offset + 1 + private_data_length <= 5 + length:
                af.private_data = bytes(self.data[offset+1:offset+1+private_data_length])
        
        return af

    def is_valid(self) -> bool:
        """Check if packet is valid (sync byte)."""
        return self.sync_byte == self.SYNC_BYTE

    def get_bytes(self) -> bytes:
        """Get packet as bytes."""
        return bytes(self.data)

    def __repr__(self) -> str:
        return (f"TSPacket(PID={self.pid:04x}, CC={self.continuity_counter}, "
                f"Scrambling={self.scrambling_control}, Payload={len(self.payload)}b)")
