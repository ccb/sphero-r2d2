"""
Unit tests for V2 packet encoding and decoding.

Packet Structure:
[SOP, FLAGS, TID?, SID?, DID, CID, SEQ, ERR?, DATA..., CHK, EOP]

SOP = 0x8D (Start of Packet)
EOP = 0xD8 (End of Packet)
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from spherov2.controls.v2 import Packet
from spherov2.controls import PacketDecodingException


class TestPacketFlags:
    """Test Packet.Flags enum values."""

    def test_is_response_flag(self):
        assert Packet.Flags.is_response == 0b1

    def test_requests_response_flag(self):
        assert Packet.Flags.requests_response == 0b10

    def test_requests_only_error_response_flag(self):
        assert Packet.Flags.requests_only_error_response == 0b100

    def test_is_activity_flag(self):
        assert Packet.Flags.is_activity == 0b1000

    def test_has_target_id_flag(self):
        assert Packet.Flags.has_target_id == 0b10000

    def test_has_source_id_flag(self):
        assert Packet.Flags.has_source_id == 0b100000

    def test_extended_flags_flag(self):
        assert Packet.Flags.extended_flags == 0b10000000

    def test_flags_can_be_combined(self):
        combined = Packet.Flags.requests_response | Packet.Flags.is_activity
        assert combined == 0b1010


class TestPacketError:
    """Test Packet.Error enum values."""

    def test_success(self):
        assert Packet.Error.success == 0x00

    def test_bad_device_id(self):
        assert Packet.Error.bad_device_id == 0x01

    def test_bad_command_id(self):
        assert Packet.Error.bad_command_id == 0x02

    def test_not_yet_implemented(self):
        assert Packet.Error.not_yet_implemented == 0x03

    def test_command_is_restricted(self):
        assert Packet.Error.command_is_restricted == 0x04

    def test_bad_data_length(self):
        assert Packet.Error.bad_data_length == 0x05

    def test_command_failed(self):
        assert Packet.Error.command_failed == 0x06

    def test_bad_parameter_value(self):
        assert Packet.Error.bad_parameter_value == 0x07

    def test_busy(self):
        assert Packet.Error.busy == 0x08

    def test_bad_target_id(self):
        assert Packet.Error.bad_target_id == 0x09

    def test_target_unavailable(self):
        assert Packet.Error.target_unavailable == 0x0A


class TestPacketBuild:
    """Test Packet.build() method."""

    def test_build_simple_command(self):
        """Build a simple command packet without TID/SID."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,  # Animatronic
            cid=0x0F,  # Set head position
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x00, 0x00, 0x00, 0x00])  # 4 bytes for float
        )
        built = packet.build()

        # Should start with SOP
        assert built[0] == 0x8D
        # Should end with EOP
        assert built[-1] == 0xD8
        # Length should be: SOP + FLAGS + DID + CID + SEQ + DATA(4) + CHK + EOP
        # = 1 + 1 + 1 + 1 + 1 + 4 + 1 + 1 = 11 (minimum, may be more with escaping)
        assert len(built) >= 11

    def test_build_with_target_id(self):
        """Build packet with target ID."""
        packet = Packet(
            flags=Packet.Flags.requests_response | Packet.Flags.has_target_id | Packet.Flags.has_source_id,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=0x02,
            sid=0x01,
            data=bytearray()
        )
        built = packet.build()
        assert built[0] == 0x8D
        assert built[-1] == 0xD8

    def test_build_response_packet(self):
        """Build a response packet (with error field)."""
        packet = Packet(
            flags=Packet.Flags.is_response | Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x42]),
            err=Packet.Error.success
        )
        built = packet.build()
        assert built[0] == 0x8D
        assert built[-1] == 0xD8

    def test_build_empty_data(self):
        """Build packet with empty data payload."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x13,  # Power
            cid=0x10,  # Get battery state
            seq=0x00,
            tid=None,
            sid=None,
            data=bytearray()
        )
        built = packet.build()
        assert built[0] == 0x8D
        assert built[-1] == 0xD8


class TestPacketParse:
    """Test Packet.parse_response() method."""

    def test_parse_simple_response(self):
        """Parse a simple response packet."""
        # Build then parse
        original = Packet(
            flags=Packet.Flags.is_response | Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x42,
            tid=None,
            sid=None,
            data=bytearray([0x01, 0x02, 0x03]),
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)

        assert parsed.did == 0x17
        assert parsed.cid == 0x0F
        assert parsed.seq == 0x42
        assert parsed.err == Packet.Error.success
        assert parsed.data == bytearray([0x01, 0x02, 0x03])

    def test_parse_with_error(self):
        """Parse response with error code."""
        original = Packet(
            flags=Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray(),
            err=Packet.Error.bad_parameter_value
        )
        built = original.build()
        parsed = Packet.parse_response(built)

        assert parsed.err == Packet.Error.bad_parameter_value

    def test_parse_with_target_source_ids(self):
        """Parse packet with TID and SID."""
        original = Packet(
            flags=Packet.Flags.is_response | Packet.Flags.has_target_id | Packet.Flags.has_source_id,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=0x02,
            sid=0x01,
            data=bytearray([0xAA, 0xBB]),
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)

        assert parsed.tid == 0x02
        assert parsed.sid == 0x01
        assert parsed.data == bytearray([0xAA, 0xBB])

    def test_parse_invalid_sop(self):
        """Invalid start of packet should raise exception."""
        invalid = bytearray([0x00, 0x02, 0x17, 0x0F, 0x01, 0x00, 0xD8])
        with pytest.raises(PacketDecodingException):
            Packet.parse_response(invalid)

    def test_parse_invalid_eop(self):
        """Invalid end of packet should raise exception."""
        invalid = bytearray([0x8D, 0x02, 0x17, 0x0F, 0x01, 0x00, 0x00])
        with pytest.raises(PacketDecodingException):
            Packet.parse_response(invalid)

    def test_parse_bad_checksum(self):
        """Bad checksum should raise exception."""
        # Manually construct packet with wrong checksum
        raw = bytearray([
            0x8D,  # SOP
            0x03,  # FLAGS
            0x17,  # DID
            0x0F,  # CID
            0x01,  # SEQ
            0x00,  # ERR
            0xFF,  # Wrong CHK
            0xD8   # EOP
        ])
        with pytest.raises(PacketDecodingException):
            Packet.parse_response(raw)


class TestPacketId:
    """Test Packet.id property."""

    def test_packet_id(self):
        """Packet ID is tuple of (DID, CID, SEQ)."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x42,
            tid=None,
            sid=None,
            data=bytearray()
        )
        assert packet.id == (0x17, 0x0F, 0x42)

    def test_packet_id_used_for_response_matching(self):
        """Command and response should have matching IDs."""
        command = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x42,
            tid=None,
            sid=None,
            data=bytearray()
        )
        response = Packet(
            flags=Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x42,
            tid=None,
            sid=None,
            data=bytearray(),
            err=Packet.Error.success
        )
        assert command.id == response.id


class TestPacketManager:
    """Test Packet.Manager class."""

    def test_manager_creates_packets(self):
        """Manager creates valid packets."""
        manager = Packet.Manager()
        packet = manager.new_packet(did=0x17, cid=0x0F, data=[0x01, 0x02])

        assert packet.did == 0x17
        assert packet.cid == 0x0F
        assert packet.data == bytearray([0x01, 0x02])

    def test_manager_increments_sequence(self):
        """Manager increments sequence number for each packet."""
        manager = Packet.Manager()
        p1 = manager.new_packet(did=0x17, cid=0x0F)
        p2 = manager.new_packet(did=0x17, cid=0x0F)
        p3 = manager.new_packet(did=0x17, cid=0x0F)

        assert p2.seq == p1.seq + 1
        assert p3.seq == p2.seq + 1

    def test_manager_sequence_wraps(self):
        """Sequence number wraps at 255."""
        manager = Packet.Manager()
        # Create 256 packets to wrap
        for _ in range(254):
            manager.new_packet(did=0x17, cid=0x0F)
        p254 = manager.new_packet(did=0x17, cid=0x0F)
        p255 = manager.new_packet(did=0x17, cid=0x0F)  # This should wrap

        assert p254.seq == 254
        assert p255.seq == 0  # Wrapped

    def test_manager_with_target_id(self):
        """Manager creates packet with target ID when specified."""
        manager = Packet.Manager()
        packet = manager.new_packet(did=0x17, cid=0x0F, tid=0x02)

        assert packet.tid == 0x02
        assert packet.sid == 0x01  # Source ID is set to 0x01 when TID is provided
        assert packet.flags & Packet.Flags.has_target_id
        assert packet.flags & Packet.Flags.has_source_id

    def test_manager_sets_flags(self):
        """Manager sets appropriate flags."""
        manager = Packet.Manager()
        packet = manager.new_packet(did=0x17, cid=0x0F)

        assert packet.flags & Packet.Flags.requests_response
        assert packet.flags & Packet.Flags.is_activity


class TestPacketCollector:
    """Test Packet.Collector class."""

    def test_collector_assembles_packet(self):
        """Collector assembles bytes into complete packet."""
        received_packets = []

        def callback(packet):
            received_packets.append(packet)

        collector = Packet.Collector(callback)

        # Build a valid packet
        original = Packet(
            flags=Packet.Flags.is_response | Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x42]),
            err=Packet.Error.success
        )
        built = original.build()

        # Feed bytes one at a time
        for byte in built:
            collector.add([byte])

        assert len(received_packets) == 1
        assert received_packets[0].did == 0x17
        assert received_packets[0].data == bytearray([0x42])

    def test_collector_handles_multiple_packets(self):
        """Collector handles multiple packets in sequence."""
        received_packets = []

        def callback(packet):
            received_packets.append(packet)

        collector = Packet.Collector(callback)

        # Build two packets
        p1 = Packet(
            flags=Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x01]),
            err=Packet.Error.success
        )
        p2 = Packet(
            flags=Packet.Flags.is_response,
            did=0x18,
            cid=0x10,
            seq=0x02,
            tid=None,
            sid=None,
            data=bytearray([0x02]),
            err=Packet.Error.success
        )

        # Feed both packets
        collector.add(p1.build())
        collector.add(p2.build())

        assert len(received_packets) == 2
        assert received_packets[0].did == 0x17
        assert received_packets[1].did == 0x18

    def test_collector_handles_chunked_data(self):
        """Collector handles packet data arriving in chunks."""
        received_packets = []

        def callback(packet):
            received_packets.append(packet)

        collector = Packet.Collector(callback)

        original = Packet(
            flags=Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x01, 0x02, 0x03, 0x04]),
            err=Packet.Error.success
        )
        built = original.build()

        # Feed in chunks of 3 bytes
        for i in range(0, len(built), 3):
            collector.add(built[i:i + 3])

        assert len(received_packets) == 1


class TestPacketRoundTrip:
    """Integration tests for full encode/decode round-trips."""

    def test_roundtrip_animatronic_command(self):
        """Round-trip an animatronic command (set dome position)."""
        import struct
        angle = 90.0
        data = bytearray(struct.pack('>f', angle))

        original = Packet(
            flags=Packet.Flags.is_response | Packet.Flags.requests_response,
            did=0x17,  # Animatronic
            cid=0x0F,  # Set head position
            seq=0x42,
            tid=None,
            sid=None,
            data=data,
            err=Packet.Error.success
        )

        built = original.build()
        parsed = Packet.parse_response(built)

        assert parsed.did == 0x17
        assert parsed.cid == 0x0F
        assert parsed.seq == 0x42
        parsed_angle = struct.unpack('>f', parsed.data)[0]
        assert abs(parsed_angle - 90.0) < 0.001

    def test_roundtrip_drive_command(self):
        """Round-trip a drive command."""
        # Speed, heading (2 bytes), flags
        data = bytearray([0x64, 0x00, 0xB4, 0x00])  # speed=100, heading=180, flags=0

        original = Packet(
            flags=Packet.Flags.is_response | Packet.Flags.requests_response,
            did=0x16,  # Drive
            cid=0x07,  # Drive with heading
            seq=0x10,
            tid=None,
            sid=None,
            data=data,
            err=Packet.Error.success
        )

        built = original.build()
        parsed = Packet.parse_response(built)

        assert parsed.did == 0x16
        assert parsed.cid == 0x07
        assert parsed.data == data

    def test_roundtrip_all_device_ids(self):
        """Round-trip packets for all R2D2 device IDs."""
        device_ids = [
            (0x00, "Core"),
            (0x13, "Power"),
            (0x16, "Drive"),
            (0x17, "Animatronic"),
            (0x18, "Sensor"),
            (0x1A, "IO"),
        ]

        for did, name in device_ids:
            original = Packet(
                flags=Packet.Flags.is_response,
                did=did,
                cid=0x01,
                seq=0x01,
                tid=None,
                sid=None,
                data=bytearray([0xAA, 0xBB]),
                err=Packet.Error.success
            )
            built = original.build()
            parsed = Packet.parse_response(built)
            assert parsed.did == did, f"Failed for {name} (DID={did:#x})"
