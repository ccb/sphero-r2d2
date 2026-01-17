"""
Drive component for robot movement.
"""

from __future__ import annotations

import asyncio
import struct
from typing import TYPE_CHECKING

from r2d2.components.base import Component
from r2d2.protocol.constants import (
    DeviceId,
    DriveCommand,
    DriveFlags,
    RawMotorMode,
    StabilizationMode,
)

if TYPE_CHECKING:
    from r2d2.robot import R2D2


class DriveComponent(Component):
    """Controls robot movement."""

    def __init__(self, robot: R2D2):
        super().__init__(robot)
        self._current_heading = 0

    async def roll(
        self,
        heading: int,
        speed: int,
        duration: float | None = None,
    ) -> None:
        """Roll in a direction at a speed.

        Args:
            heading: Direction in degrees (0-359, 0=forward)
            speed: Speed (0-255, negative for reverse)
            duration: Optional duration in seconds (then stops)

        Example:
            >>> await r2.drive.roll(heading=0, speed=100)  # Forward
            >>> await r2.drive.roll(heading=180, speed=100)  # Backward
            >>> await r2.drive.roll(heading=90, speed=50, duration=2.0)  # Right for 2s
        """
        # Handle negative speed as reverse
        flags = DriveFlags.FORWARD
        if speed < 0:
            flags = DriveFlags.BACKWARD
            heading = (heading + 180) % 360
            speed = abs(speed)

        # Clamp speed
        speed = min(255, max(0, speed))

        # Normalize heading
        heading = heading % 360
        self._current_heading = heading

        # Build command data: speed (1), heading (2), flags (1)
        data = struct.pack(">BHB", speed, heading, flags)

        await self._send_command(
            DeviceId.DRIVE,
            DriveCommand.DRIVE_WITH_HEADING,
            data,
        )

        if duration is not None:
            await asyncio.sleep(duration)
            await self.stop()

    async def stop(self) -> None:
        """Stop all movement."""
        await self.roll(self._current_heading, 0)

    async def set_heading(self, heading: int) -> None:
        """Set direction without moving.

        Args:
            heading: Direction in degrees (0-359)
        """
        await self.roll(heading, 0)
        self._current_heading = heading

    async def reset_heading(self) -> None:
        """Reset heading to treat current orientation as 0."""
        await self._send_command(
            DeviceId.DRIVE,
            DriveCommand.RESET_YAW,
        )
        self._current_heading = 0

    async def set_raw_motors(
        self,
        left_mode: RawMotorMode,
        left_speed: int,
        right_mode: RawMotorMode,
        right_speed: int,
    ) -> None:
        """Direct motor control.

        Args:
            left_mode: Left motor mode (OFF, FORWARD, REVERSE)
            left_speed: Left motor speed (0-255)
            right_mode: Right motor mode
            right_speed: Right motor speed

        Example:
            >>> # Spin in place
            >>> await r2.drive.set_raw_motors(
            ...     RawMotorMode.FORWARD, 100,
            ...     RawMotorMode.REVERSE, 100
            ... )
        """
        left_speed = min(255, max(0, left_speed))
        right_speed = min(255, max(0, right_speed))

        data = bytes([left_mode, left_speed, right_mode, right_speed])

        await self._send_command(
            DeviceId.DRIVE,
            DriveCommand.SET_RAW_MOTORS,
            data,
        )

    async def set_stabilization(self, mode: StabilizationMode) -> None:
        """Set stabilization mode.

        Args:
            mode: Stabilization mode

        Example:
            >>> await r2.drive.set_stabilization(StabilizationMode.DISABLED)
        """
        await self._send_command(
            DeviceId.DRIVE,
            DriveCommand.SET_STABILIZATION,
            bytes([mode]),
        )

    # Convenience methods

    async def forward(self, speed: int = 100, duration: float | None = None) -> None:
        """Drive forward.

        Args:
            speed: Speed (0-255)
            duration: Optional duration in seconds
        """
        await self.roll(0, speed, duration)

    async def backward(self, speed: int = 100, duration: float | None = None) -> None:
        """Drive backward.

        Args:
            speed: Speed (0-255)
            duration: Optional duration in seconds
        """
        await self.roll(180, speed, duration)

    async def left(self, speed: int = 100, duration: float | None = None) -> None:
        """Drive left.

        Args:
            speed: Speed (0-255)
            duration: Optional duration in seconds
        """
        await self.roll(270, speed, duration)

    async def right(self, speed: int = 100, duration: float | None = None) -> None:
        """Drive right.

        Args:
            speed: Speed (0-255)
            duration: Optional duration in seconds
        """
        await self.roll(90, speed, duration)

    async def spin(self, direction: int = 1, speed: int = 100, duration: float | None = None) -> None:
        """Spin in place.

        Args:
            direction: 1 for clockwise, -1 for counter-clockwise
            speed: Rotation speed (0-255)
            duration: Optional duration in seconds
        """
        if direction >= 0:
            await self.set_raw_motors(
                RawMotorMode.FORWARD, speed,
                RawMotorMode.REVERSE, speed,
            )
        else:
            await self.set_raw_motors(
                RawMotorMode.REVERSE, speed,
                RawMotorMode.FORWARD, speed,
            )

        if duration is not None:
            await asyncio.sleep(duration)
            await self.stop()
