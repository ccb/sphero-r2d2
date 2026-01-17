"""
Unit tests for checksum calculation.

The V2 protocol uses a simple checksum: 0xFF - (sum of bytes & 0xFF)
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from spherov2.helper import packet_chk


class TestChecksum:
    """Tests for packet_chk() function."""

    def test_empty_payload(self):
        """Empty payload should return 0xFF."""
        assert packet_chk([]) == 0xFF

    def test_single_byte_zero(self):
        """Single byte 0x00 should return 0xFF."""
        assert packet_chk([0x00]) == 0xFF

    def test_single_byte_ff(self):
        """Single byte 0xFF should return 0x00."""
        assert packet_chk([0xFF]) == 0x00

    def test_single_byte_01(self):
        """Single byte 0x01 should return 0xFE."""
        assert packet_chk([0x01]) == 0xFE

    def test_two_bytes_sum_under_256(self):
        """Two bytes summing to less than 256."""
        # 0x10 + 0x20 = 0x30 = 48
        # 0xFF - 48 = 207 = 0xCF
        assert packet_chk([0x10, 0x20]) == 0xCF

    def test_two_bytes_sum_over_256(self):
        """Two bytes summing to more than 256 (tests & 0xFF)."""
        # 0x80 + 0x90 = 0x110 = 272
        # 272 & 0xFF = 0x10 = 16
        # 0xFF - 16 = 239 = 0xEF
        assert packet_chk([0x80, 0x90]) == 0xEF

    def test_all_ff_bytes(self):
        """Multiple 0xFF bytes."""
        # 4 * 0xFF = 1020
        # 1020 & 0xFF = 0xFC = 252
        # 0xFF - 252 = 3
        assert packet_chk([0xFF, 0xFF, 0xFF, 0xFF]) == 0x03

    def test_typical_packet_header(self):
        """Test with a typical packet header structure."""
        # FLAGS=0x0A, DID=0x17, CID=0x0F, SEQ=0x01
        payload = [0x0A, 0x17, 0x0F, 0x01]
        # Sum = 10 + 23 + 15 + 1 = 49 = 0x31
        # 0xFF - 0x31 = 0xCE = 206
        assert packet_chk(payload) == 0xCE

    def test_large_payload(self):
        """Test with a larger payload (255 bytes of 0x01)."""
        payload = [0x01] * 255
        # Sum = 255
        # 0xFF - 255 = 0
        assert packet_chk(payload) == 0x00

    def test_bytearray_input(self):
        """Test that bytearray works as input."""
        payload = bytearray([0x10, 0x20, 0x30])
        # Sum = 16 + 32 + 48 = 96 = 0x60
        # 0xFF - 0x60 = 0x9F = 159
        assert packet_chk(payload) == 0x9F

    def test_checksum_verification(self):
        """Verify that checksum can be verified by including it in sum."""
        payload = [0x0A, 0x17, 0x0F, 0x01]
        chk = packet_chk(payload)
        # Adding checksum to payload should make sum & 0xFF equal 0xFF
        full_sum = (sum(payload) + chk) & 0xFF
        assert full_sum == 0xFF


class TestChecksumEdgeCases:
    """Edge case tests for checksum calculation."""

    def test_max_single_packet_payload(self):
        """Test maximum practical payload size."""
        # V2 packets can have up to ~255 bytes of data
        payload = list(range(256))  # 0x00 to 0xFF
        # Sum of 0..255 = 255 * 256 / 2 = 32640
        # 32640 & 0xFF = 0x80 = 128
        # 0xFF - 128 = 127 = 0x7F
        assert packet_chk(payload) == 0x7F

    def test_alternating_bytes(self):
        """Test alternating 0x00 and 0xFF bytes."""
        payload = [0x00, 0xFF] * 10
        # Sum = 10 * 0xFF = 2550
        # 2550 & 0xFF = 0xF6 = 246
        # 0xFF - 246 = 9
        assert packet_chk(payload) == 0x09

    def test_escape_bytes_in_payload(self):
        """Checksum doesn't care about escape sequences - raw bytes."""
        # These are escape-related bytes, but checksum treats them as regular bytes
        payload = [0xAB, 0x8D, 0xD8]
        # Sum = 171 + 141 + 216 = 528
        # 528 & 0xFF = 0x10 = 16
        # 0xFF - 16 = 239 = 0xEF
        assert packet_chk(payload) == 0xEF
