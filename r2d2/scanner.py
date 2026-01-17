"""
Robot discovery and scanning.

Uses Bleak to scan for R2D2 robots via BLE.
"""

from __future__ import annotations

from typing import List, Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from r2d2.exceptions import NotFoundError, ScanError


# R2D2 advertises with name prefix "D2-"
R2D2_NAME_PREFIX = "D2-"


async def scan(timeout: float = 10.0) -> List[BLEDevice]:
    """Scan for all R2D2 robots.

    Args:
        timeout: Scan duration in seconds

    Returns:
        List of discovered R2D2 devices

    Example:
        >>> robots = await scan()
        >>> for robot in robots:
        ...     print(f"Found: {robot.name}")
    """
    try:
        devices = await BleakScanner.discover(timeout=timeout)
        r2d2_devices = [
            d for d in devices
            if d.name and d.name.startswith(R2D2_NAME_PREFIX)
        ]
        return r2d2_devices
    except Exception as e:
        raise ScanError(f"Scan failed: {e}", e)


async def scan_one(
    name: Optional[str] = None,
    timeout: float = 10.0,
) -> BLEDevice:
    """Scan for a specific R2D2 robot or the first one found.

    Args:
        name: Specific robot name to find (e.g., "D2-55E3")
        timeout: Scan duration in seconds

    Returns:
        The discovered R2D2 device

    Raises:
        NotFoundError: If no matching robot is found

    Example:
        >>> robot = await scan_one(name="D2-55E3")
        >>> print(f"Found: {robot.name} at {robot.address}")
    """
    if name:
        # Look for specific robot
        def match_filter(device: BLEDevice, adv_data) -> bool:
            return adv_data.local_name == name

        try:
            device = await BleakScanner.find_device_by_filter(
                match_filter,
                timeout=timeout,
            )
        except Exception as e:
            raise ScanError(f"Scan failed: {e}", e)

        if device is None:
            raise NotFoundError(name=name, timeout=timeout)

        return device
    else:
        # Find first R2D2
        def match_filter(device: BLEDevice, adv_data) -> bool:
            return (
                adv_data.local_name is not None
                and adv_data.local_name.startswith(R2D2_NAME_PREFIX)
            )

        try:
            device = await BleakScanner.find_device_by_filter(
                match_filter,
                timeout=timeout,
            )
        except Exception as e:
            raise ScanError(f"Scan failed: {e}", e)

        if device is None:
            raise NotFoundError(timeout=timeout)

        return device
