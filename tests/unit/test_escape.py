"""
Unit tests for escape sequence handling.

V2 Protocol Escape Sequences:
- 0x8D (SOP) -> 0xAB 0x05
- 0xD8 (EOP) -> 0xAB 0x50
- 0xAB (ESC) -> 0xAB 0x23
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from spherov2.controls.v2 import Packet
from spherov2.controls import PacketDecodingException


class TestEscapeConstants:
    """Verify escape sequence constants are correct."""

    def test_escape_byte(self):
        assert Packet.Encoding.escape == 0xAB

    def test_start_byte(self):
        assert Packet.Encoding.start == 0x8D

    def test_end_byte(self):
        assert Packet.Encoding.end == 0xD8

    def test_escaped_escape(self):
        assert Packet.Encoding.escaped_escape == 0x23

    def test_escaped_start(self):
        assert Packet.Encoding.escaped_start == 0x05

    def test_escaped_end(self):
        assert Packet.Encoding.escaped_end == 0x50


class TestPacketEscaping:
    """Test that packet building correctly escapes special bytes."""

    def test_no_escaping_needed(self):
        """Packet with no special bytes in payload."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x00, 0x10, 0x20])
        )
        built = packet.build()
        # Should start with SOP and end with EOP
        assert built[0] == Packet.Encoding.start
        assert built[-1] == Packet.Encoding.end
        # No escape bytes should be present in middle (unless in payload)
        middle = built[1:-1]
        # Count escape sequences - should be 0 for this payload
        escape_count = sum(1 for i, b in enumerate(middle) if b == Packet.Encoding.escape)
        assert escape_count == 0

    def test_escape_byte_in_data(self):
        """Packet with 0xAB (escape byte) in payload."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0xAB])  # Escape byte in data
        )
        built = packet.build()
        # Should contain 0xAB 0x23 sequence
        found = False
        for i in range(len(built) - 1):
            if built[i] == 0xAB and built[i + 1] == 0x23:
                found = True
                break
        assert found, "Escape byte should be escaped as 0xAB 0x23"

    def test_start_byte_in_data(self):
        """Packet with 0x8D (start byte) in payload."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x8D])  # Start byte in data
        )
        built = packet.build()
        # Should contain 0xAB 0x05 sequence
        found = False
        for i in range(len(built) - 1):
            if built[i] == 0xAB and built[i + 1] == 0x05:
                found = True
                break
        assert found, "Start byte should be escaped as 0xAB 0x05"

    def test_end_byte_in_data(self):
        """Packet with 0xD8 (end byte) in payload."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0xD8])  # End byte in data
        )
        built = packet.build()
        # Should contain 0xAB 0x50 sequence
        found = False
        for i in range(len(built) - 1):
            if built[i] == 0xAB and built[i + 1] == 0x50:
                found = True
                break
        assert found, "End byte should be escaped as 0xAB 0x50"

    def test_multiple_escapes_in_data(self):
        """Packet with multiple special bytes in payload."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0xAB, 0x8D, 0xD8])  # All three special bytes
        )
        built = packet.build()
        # Count escape sequences
        escape_sequences = 0
        i = 0
        while i < len(built) - 1:
            if built[i] == 0xAB and built[i + 1] in [0x23, 0x05, 0x50]:
                escape_sequences += 1
                i += 2
            else:
                i += 1
        # Should have at least 3 escape sequences (one for each special byte in data)
        # May have more if checksum or other header bytes need escaping
        assert escape_sequences >= 3

    def test_consecutive_escape_bytes(self):
        """Packet with consecutive escape bytes in payload."""
        packet = Packet(
            flags=Packet.Flags.requests_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0xAB, 0xAB, 0xAB])
        )
        built = packet.build()
        # Should have escape sequence for each 0xAB
        escape_count = 0
        i = 0
        while i < len(built) - 1:
            if built[i] == 0xAB and built[i + 1] == 0x23:
                escape_count += 1
                i += 2
            else:
                i += 1
        assert escape_count >= 3


class TestPacketUnescaping:
    """Test that packet parsing correctly unescapes special bytes."""

    def test_unescape_escape_byte(self):
        """Parse packet with escaped escape byte."""
        # Build a raw packet with 0xAB 0x23 (escaped escape)
        # Simple packet: SOP, FLAGS, DID, CID, SEQ, [escaped 0xAB in data], CHK, EOP
        # We'll use parse_response which expects a complete packet

        # Build a valid packet first, then verify round-trip
        original = Packet(
            flags=Packet.Flags.requests_response | Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0xAB]),  # This will be escaped in build()
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)
        assert parsed.data == bytearray([0xAB])

    def test_unescape_start_byte(self):
        """Parse packet with escaped start byte."""
        original = Packet(
            flags=Packet.Flags.requests_response | Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x8D]),
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)
        assert parsed.data == bytearray([0x8D])

    def test_unescape_end_byte(self):
        """Parse packet with escaped end byte."""
        original = Packet(
            flags=Packet.Flags.requests_response | Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0xD8]),
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)
        assert parsed.data == bytearray([0xD8])

    def test_invalid_escape_sequence(self):
        """Invalid escape sequence should raise exception."""
        # Build invalid packet: SOP, FLAGS, DID, CID, SEQ, 0xAB 0xFF (invalid), CHK, EOP
        # This is tricky to test directly since we need to craft a malformed packet
        invalid_packet = bytearray([
            0x8D,  # SOP
            0x03,  # FLAGS (is_response | requests_response)
            0x17,  # DID
            0x0F,  # CID
            0x01,  # SEQ
            0x00,  # ERR (success)
            0xAB, 0xFF,  # Invalid escape sequence
            0x00,  # Fake CHK (will fail anyway)
            0xD8   # EOP
        ])
        with pytest.raises(PacketDecodingException):
            Packet.parse_response(invalid_packet)


class TestEscapeRoundTrip:
    """Test round-trip encoding/decoding with various payloads."""

    def test_roundtrip_empty_data(self):
        """Round-trip with empty data."""
        original = Packet(
            flags=Packet.Flags.requests_response | Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x42,
            tid=None,
            sid=None,
            data=bytearray(),
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)
        assert parsed.did == original.did
        assert parsed.cid == original.cid
        assert parsed.seq == original.seq
        assert parsed.data == original.data

    def test_roundtrip_all_special_bytes(self):
        """Round-trip with all special bytes in data."""
        original = Packet(
            flags=Packet.Flags.requests_response | Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=bytearray([0x8D, 0xD8, 0xAB, 0x8D, 0xD8, 0xAB]),
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)
        assert parsed.data == original.data

    def test_roundtrip_max_payload(self):
        """Round-trip with large payload containing special bytes."""
        # Create payload with all byte values
        data = bytearray(range(256))
        original = Packet(
            flags=Packet.Flags.requests_response | Packet.Flags.is_response,
            did=0x17,
            cid=0x0F,
            seq=0x01,
            tid=None,
            sid=None,
            data=data,
            err=Packet.Error.success
        )
        built = original.build()
        parsed = Packet.parse_response(built)
        assert parsed.data == original.data
