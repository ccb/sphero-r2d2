"""
Fleet management for controlling multiple robots.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, Callable, Any

from r2d2.robot import R2D2
from r2d2.scanner import scan


class Fleet:
    """Manage multiple R2D2 robots.

    Example:
        >>> async with Fleet() as fleet:
        ...     await fleet.scan()
        ...     await fleet.all(lambda r: r.leds.red())
        ...     await fleet.all(lambda r: r.dome.set_position(90))
    """

    def __init__(self):
        self._robots: List[R2D2] = []

    async def __aenter__(self) -> Fleet:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect_all()

    @property
    def robots(self) -> List[R2D2]:
        """Get list of managed robots."""
        return self._robots.copy()

    @property
    def count(self) -> int:
        """Get number of robots in fleet."""
        return len(self._robots)

    async def scan_and_connect(
        self,
        timeout: float = 10.0,
        max_robots: Optional[int] = None,
    ) -> int:
        """Scan for robots and connect to all found.

        Args:
            timeout: Scan timeout in seconds
            max_robots: Maximum number of robots to connect (None for all)

        Returns:
            Number of robots connected
        """
        devices = await scan(timeout=timeout)

        if max_robots:
            devices = devices[:max_robots]

        # Connect to all in parallel
        async def connect_one(device):
            robot = R2D2(device=device)
            try:
                await robot.connect()
                return robot
            except Exception as e:
                return None

        results = await asyncio.gather(*[connect_one(d) for d in devices])
        self._robots.extend([r for r in results if r is not None])

        return len(self._robots)

    def add(self, robot: R2D2) -> None:
        """Add a robot to the fleet."""
        if robot not in self._robots:
            self._robots.append(robot)

    def remove(self, robot: R2D2) -> None:
        """Remove a robot from the fleet."""
        if robot in self._robots:
            self._robots.remove(robot)

    async def disconnect_all(self) -> None:
        """Disconnect all robots."""
        await asyncio.gather(*[r.disconnect() for r in self._robots])
        self._robots.clear()

    async def all(self, action: Callable[[R2D2], Any]) -> List[Any]:
        """Execute an action on all robots in parallel.

        Args:
            action: Async function taking a robot and returning a result

        Returns:
            List of results from each robot

        Example:
            >>> # Set all LEDs to red
            >>> await fleet.all(lambda r: r.leds.red())
            >>>
            >>> # Get all battery levels
            >>> levels = await fleet.all(lambda r: r.get_battery_voltage())
        """
        return await asyncio.gather(*[action(r) for r in self._robots])

    async def sequential(self, action: Callable[[R2D2], Any]) -> List[Any]:
        """Execute an action on all robots sequentially.

        Args:
            action: Async function taking a robot

        Returns:
            List of results
        """
        results = []
        for robot in self._robots:
            results.append(await action(robot))
        return results

    def by_name(self, name: str) -> Optional[R2D2]:
        """Get robot by name.

        Args:
            name: Robot name (e.g., "D2-55E3")

        Returns:
            Robot if found, None otherwise
        """
        for robot in self._robots:
            if robot.name == name:
                return robot
        return None
