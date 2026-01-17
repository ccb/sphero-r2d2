"""
R2D2 - A modern Python library for controlling Sphero R2-D2 robots.

This library provides an async-first, type-safe interface for controlling
Sphero R2-D2 robots via Bluetooth Low Energy (BLE).

Example:
    >>> import asyncio
    >>> from r2d2 import R2D2, scan
    >>>
    >>> async def main():
    ...     robots = await scan()
    ...     async with R2D2(robots[0]) as r2:
    ...         await r2.dome.set_position(90)
    ...         await r2.drive.roll(heading=0, speed=100, duration=2.0)
    >>>
    >>> asyncio.run(main())
"""

__version__ = "2.0.0-alpha"

from r2d2.robot import R2D2
from r2d2.scanner import scan, scan_one
from r2d2.fleet import Fleet
from r2d2.exceptions import (
    R2D2Error,
    ConnectionError,
    CommandError,
    TimeoutError,
)

__all__ = [
    "R2D2",
    "Fleet",
    "scan",
    "scan_one",
    "R2D2Error",
    "ConnectionError",
    "CommandError",
    "TimeoutError",
]
