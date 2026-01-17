"""
LED component for R2D2 lighting control.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Tuple

from r2d2.components.base import Component
from r2d2.protocol.constants import DeviceId, IOCommand, LED

if TYPE_CHECKING:
    from r2d2.robot import R2D2


# Type alias for RGB color
Color = Tuple[int, int, int]


class LEDComponent(Component):
    """Controls R2D2 LEDs."""

    async def set_all(
        self,
        front: Color | None = None,
        back: Color | None = None,
        logic_displays: int | None = None,
        holo_projector: int | None = None,
    ) -> None:
        """Set multiple LEDs at once.

        Args:
            front: Front LED RGB tuple (0-255 each)
            back: Back LED RGB tuple (0-255 each)
            logic_displays: Logic display brightness (0-255)
            holo_projector: Holographic projector brightness (0-255)

        Example:
            >>> await r2.leds.set_all(front=(255, 0, 0), back=(0, 0, 255))
        """
        mask = 0
        values = []

        if front is not None:
            mask |= (1 << LED.FRONT_RED) | (1 << LED.FRONT_GREEN) | (1 << LED.FRONT_BLUE)
            values.extend(front)

        if logic_displays is not None:
            mask |= 1 << LED.LOGIC_DISPLAYS
            values.append(logic_displays)

        if back is not None:
            mask |= (1 << LED.BACK_RED) | (1 << LED.BACK_GREEN) | (1 << LED.BACK_BLUE)
            values.extend(back)

        if holo_projector is not None:
            mask |= 1 << LED.HOLO_PROJECTOR
            values.append(holo_projector)

        if mask:
            data = struct.pack(">I", mask) + bytes(values)
            await self._send_command(
                DeviceId.IO,
                IOCommand.SET_ALL_LEDS_32_BIT_MASK,
                data,
            )

    async def set_front(self, r: int, g: int, b: int) -> None:
        """Set front LED color.

        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
        """
        await self.set_all(front=(r, g, b))

    async def set_back(self, r: int, g: int, b: int) -> None:
        """Set back LED color.

        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
        """
        await self.set_all(back=(r, g, b))

    async def set_logic_displays(self, brightness: int) -> None:
        """Set logic display brightness.

        Args:
            brightness: Brightness (0-255)
        """
        await self.set_all(logic_displays=brightness)

    async def set_holo_projector(self, brightness: int) -> None:
        """Set holographic projector brightness.

        Args:
            brightness: Brightness (0-255)
        """
        await self.set_all(holo_projector=brightness)

    async def off(self) -> None:
        """Turn off all LEDs."""
        await self.set_all(
            front=(0, 0, 0),
            back=(0, 0, 0),
            logic_displays=0,
            holo_projector=0,
        )

    # Convenience color methods

    async def red(self) -> None:
        """Set front LED to red."""
        await self.set_front(255, 0, 0)

    async def green(self) -> None:
        """Set front LED to green."""
        await self.set_front(0, 255, 0)

    async def blue(self) -> None:
        """Set front LED to blue."""
        await self.set_front(0, 0, 255)

    async def white(self) -> None:
        """Set front LED to white."""
        await self.set_front(255, 255, 255)
