"""
Stance component for R2D2 leg control.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from r2d2.components.base import Component
from r2d2.protocol.constants import DeviceId, AnimatronicCommand, LegAction, LegState

if TYPE_CHECKING:
    from r2d2.robot import R2D2


class StanceComponent(Component):
    """Controls R2D2 leg stance (bipod, tripod, waddle)."""

    async def set_stance(self, action: LegAction) -> None:
        """Set leg stance.

        Args:
            action: Leg action to perform

        Example:
            >>> await r2.stance.set_stance(LegAction.TRIPOD)
        """
        await self._send_command(
            DeviceId.ANIMATRONIC,
            AnimatronicCommand.PERFORM_LEG_ACTION,
            bytes([action]),
        )

    async def get_stance(self) -> LegState:
        """Get current leg state.

        Returns:
            Current leg state
        """
        response = await self._send_command(
            DeviceId.ANIMATRONIC,
            AnimatronicCommand.GET_LEG_ACTION,
        )
        return LegState(response[0])

    async def tripod(self) -> None:
        """Deploy third leg (tripod stance)."""
        await self.set_stance(LegAction.TRIPOD)

    async def bipod(self) -> None:
        """Retract third leg (bipod stance)."""
        await self.set_stance(LegAction.BIPOD)

    async def waddle(self, duration: float | None = None) -> None:
        """Start waddle mode.

        Args:
            duration: Optional duration in seconds (then stops)
        """
        await self.set_stance(LegAction.WADDLE)

        if duration is not None:
            await asyncio.sleep(duration)
            await self.stop_waddle()

    async def stop_waddle(self) -> None:
        """Stop waddle mode."""
        await self.set_stance(LegAction.STOP)
