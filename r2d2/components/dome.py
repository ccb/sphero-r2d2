"""
Dome (head) component for R2D2.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from r2d2.components.base import Component
from r2d2.protocol.constants import DeviceId, AnimatronicCommand

if TYPE_CHECKING:
    from r2d2.robot import R2D2


class DomeComponent(Component):
    """Controls the R2D2 dome (head) rotation."""

    # Dome rotation limits
    MIN_ANGLE = -160.0
    MAX_ANGLE = 180.0

    async def set_position(self, angle: float) -> None:
        """Set dome position.

        Args:
            angle: Rotation angle in degrees (-160 to 180)

        Example:
            >>> await r2.dome.set_position(90)   # Turn right
            >>> await r2.dome.set_position(-90)  # Turn left
            >>> await r2.dome.set_position(0)    # Center
        """
        # Clamp to valid range
        angle = max(self.MIN_ANGLE, min(self.MAX_ANGLE, angle))

        data = struct.pack(">f", angle)

        await self._send_command(
            DeviceId.ANIMATRONIC,
            AnimatronicCommand.SET_HEAD_POSITION,
            data,
        )

    async def get_position(self) -> float:
        """Get current dome position.

        Returns:
            Current angle in degrees
        """
        response = await self._send_command(
            DeviceId.ANIMATRONIC,
            AnimatronicCommand.GET_HEAD_POSITION,
        )
        return struct.unpack(">f", response)[0]

    async def center(self) -> None:
        """Center the dome (position 0)."""
        await self.set_position(0)

    async def look_left(self, angle: float = 90) -> None:
        """Turn dome left.

        Args:
            angle: Degrees to turn (positive value)
        """
        await self.set_position(-abs(angle))

    async def look_right(self, angle: float = 90) -> None:
        """Turn dome right.

        Args:
            angle: Degrees to turn (positive value)
        """
        await self.set_position(abs(angle))
