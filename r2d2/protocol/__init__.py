"""
Protocol layer for R2D2 communication.

Handles V2 packet encoding/decoding, command definitions, and constants.
"""

from r2d2.protocol.packet import Packet, PacketFlags, PacketBuilder
from r2d2.protocol.constants import (
    DeviceId,
    CommandId,
    ErrorCode,
    ESCAPE,
    SOP,
    EOP,
)

__all__ = [
    "Packet",
    "PacketFlags",
    "PacketBuilder",
    "DeviceId",
    "CommandId",
    "ErrorCode",
    "ESCAPE",
    "SOP",
    "EOP",
]
