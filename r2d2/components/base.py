"""
Base component class.

All robot components inherit from this base class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from r2d2.robot import R2D2


class Component:
    """Base class for robot components."""

    def __init__(self, robot: R2D2):
        """
        Args:
            robot: Parent R2D2 instance
        """
        self._robot = robot

    async def _send_command(
        self,
        did: int,
        cid: int,
        data: bytes = b"",
        timeout: float | None = None,
    ) -> bytes:
        """Send a command and wait for response.

        Args:
            did: Device ID
            cid: Command ID
            data: Command data
            timeout: Response timeout (uses default if None)

        Returns:
            Response data bytes
        """
        return await self._robot._send_command(did, cid, data, timeout)
