"""
V2 Protocol packet encoding and decoding.

Packet Structure:
[SOP, FLAGS, TID?, SID?, DID, CID, SEQ, ERR?, DATA..., CHK, EOP]
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Optional, Callable, List

from r2d2.protocol.constants import (
    SOP, EOP, ESCAPE,
    ESCAPED_SOP, ESCAPED_EOP, ESCAPED_ESCAPE,
    PacketFlags, ErrorCode,
)
from r2d2.exceptions import PacketError, ChecksumError


def compute_checksum(data: bytes | bytearray) -> int:
    """Compute checksum for packet data.

    The checksum is: 0xFF - (sum of bytes & 0xFF)
    """
    return 0xFF - (sum(data) & 0xFF)


def escape_data(data: bytes | bytearray) -> bytearray:
    """Escape special bytes in packet data."""
    result = bytearray()
    for byte in data:
        if byte == ESCAPE:
            result.extend([ESCAPE, ESCAPED_ESCAPE])
        elif byte == SOP:
            result.extend([ESCAPE, ESCAPED_SOP])
        elif byte == EOP:
            result.extend([ESCAPE, ESCAPED_EOP])
        else:
            result.append(byte)
    return result


def unescape_data(data: bytes | bytearray) -> bytearray:
    """Unescape special bytes in packet data."""
    result = bytearray()
    it = iter(data)
    for byte in it:
        if byte == ESCAPE:
            next_byte = next(it, None)
            if next_byte == ESCAPED_ESCAPE:
                result.append(ESCAPE)
            elif next_byte == ESCAPED_SOP:
                result.append(SOP)
            elif next_byte == ESCAPED_EOP:
                result.append(EOP)
            else:
                raise PacketError(f"Invalid escape sequence: 0x{ESCAPE:02X} 0x{next_byte:02X}")
        else:
            result.append(byte)
    return result


@dataclass
class Packet:
    """A V2 protocol packet."""

    flags: PacketFlags
    did: int  # Device ID
    cid: int  # Command ID
    seq: int  # Sequence number
    data: bytes
    tid: Optional[int] = None  # Target ID
    sid: Optional[int] = None  # Source ID
    err: Optional[ErrorCode] = None  # Error code (responses only)

    @property
    def is_response(self) -> bool:
        """Check if this is a response packet."""
        return bool(self.flags & PacketFlags.IS_RESPONSE)

    @property
    def id(self) -> tuple[int, int, int]:
        """Get packet ID tuple (DID, CID, SEQ) for matching responses."""
        return (self.did, self.cid, self.seq)

    def check_error(self) -> None:
        """Raise CommandError if response contains an error."""
        from r2d2.exceptions import CommandError
        if self.err is not None and self.err != ErrorCode.SUCCESS:
            raise CommandError(self.err.message, self.err.value)

    def encode(self) -> bytearray:
        """Encode packet to bytes for transmission."""
        # Build unescaped packet body
        body = bytearray([self.flags])

        if self.flags & PacketFlags.HAS_TARGET_ID:
            body.append(self.tid or 0)

        if self.flags & PacketFlags.HAS_SOURCE_ID:
            body.append(self.sid or 0)

        body.extend([self.did, self.cid, self.seq])

        if self.flags & PacketFlags.IS_RESPONSE:
            body.append(self.err or ErrorCode.SUCCESS)

        body.extend(self.data)

        # Add checksum
        body.append(compute_checksum(body))

        # Escape and frame
        result = bytearray([SOP])
        result.extend(escape_data(body))
        result.append(EOP)

        return result

    @classmethod
    def decode(cls, data: bytes | bytearray) -> Packet:
        """Decode packet from received bytes."""
        if len(data) < 6:
            raise PacketError(f"Packet too short: {len(data)} bytes")

        if data[0] != SOP:
            raise PacketError(f"Invalid SOP: 0x{data[0]:02X}")

        if data[-1] != EOP:
            raise PacketError(f"Invalid EOP: 0x{data[-1]:02X}")

        # Unescape body (between SOP and EOP)
        body = unescape_data(data[1:-1])

        # Verify checksum
        *payload, checksum = body
        expected_checksum = compute_checksum(payload)
        if checksum != expected_checksum:
            raise ChecksumError(
                f"Checksum mismatch: got 0x{checksum:02X}, expected 0x{expected_checksum:02X}"
            )

        # Parse fields
        payload = list(payload)
        flags = PacketFlags(payload.pop(0))

        tid = None
        if flags & PacketFlags.HAS_TARGET_ID:
            tid = payload.pop(0)

        sid = None
        if flags & PacketFlags.HAS_SOURCE_ID:
            sid = payload.pop(0)

        did = payload.pop(0)
        cid = payload.pop(0)
        seq = payload.pop(0)

        err = None
        if flags & PacketFlags.IS_RESPONSE:
            err = ErrorCode(payload.pop(0))

        return cls(
            flags=flags,
            did=did,
            cid=cid,
            seq=seq,
            data=bytes(payload),
            tid=tid,
            sid=sid,
            err=err,
        )


class PacketBuilder:
    """Builder for creating command packets with auto-incrementing sequence numbers."""

    def __init__(self):
        self._seq = 0

    def _next_seq(self) -> int:
        """Get next sequence number (wraps at 255)."""
        seq = self._seq
        self._seq = (self._seq + 1) % 256
        return seq

    def build(
        self,
        did: int,
        cid: int,
        data: bytes | bytearray = b"",
        tid: Optional[int] = None,
    ) -> Packet:
        """Build a command packet.

        Args:
            did: Device ID
            cid: Command ID
            data: Command data payload
            tid: Target ID (for multi-processor robots)

        Returns:
            Encoded packet ready for transmission
        """
        flags = PacketFlags.REQUESTS_RESPONSE | PacketFlags.IS_ACTIVITY

        sid = None
        if tid is not None:
            flags |= PacketFlags.HAS_TARGET_ID | PacketFlags.HAS_SOURCE_ID
            sid = 0x01

        return Packet(
            flags=flags,
            did=did,
            cid=cid,
            seq=self._next_seq(),
            data=bytes(data),
            tid=tid,
            sid=sid,
        )


class PacketCollector:
    """Collects incoming bytes and assembles complete packets."""

    def __init__(self, callback: Callable[[Packet], None]):
        """
        Args:
            callback: Function to call when a complete packet is received
        """
        self._callback = callback
        self._buffer: List[int] = []

    def add(self, data: bytes | bytearray) -> None:
        """Add received bytes, calling callback for each complete packet."""
        for byte in data:
            self._buffer.append(byte)

            if byte == EOP:
                if len(self._buffer) >= 6:
                    try:
                        packet = Packet.decode(bytes(self._buffer))
                        self._callback(packet)
                    except (PacketError, ChecksumError) as e:
                        # Log error but continue
                        pass
                self._buffer = []

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer = []
