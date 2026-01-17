"""
Sensor component for R2D2 sensor streaming.

Note: Full sensor streaming implementation is TODO.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, Callable, List

from r2d2.components.base import Component

if TYPE_CHECKING:
    from r2d2.robot import R2D2


class SensorComponent(Component):
    """Controls R2D2 sensor streaming.

    TODO: Full implementation of sensor streaming.
    """

    def __init__(self, robot: R2D2):
        super().__init__(robot)
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._enabled_sensors: set[str] = set()

    async def enable(self, *sensors: str) -> None:
        """Enable sensor streaming.

        Args:
            sensors: Sensor names to enable ('accelerometer', 'gyroscope', etc.)

        Example:
            >>> await r2.sensors.enable('accelerometer', 'gyroscope')
        """
        # TODO: Implement sensor streaming
        for sensor in sensors:
            self._enabled_sensors.add(sensor)

    async def disable(self, *sensors: str) -> None:
        """Disable specific sensors.

        Args:
            sensors: Sensor names to disable
        """
        for sensor in sensors:
            self._enabled_sensors.discard(sensor)

    async def disable_all(self) -> None:
        """Disable all sensor streaming."""
        self._enabled_sensors.clear()

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a sensor data listener.

        Args:
            callback: Function to call with sensor data dict
        """
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a sensor data listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
