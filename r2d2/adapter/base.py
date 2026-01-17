"""
Abstract base adapter interface.

All adapters (BLE, TCP, Mock) implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class Adapter(ABC):
    """Abstract base class for robot communication adapters."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the robot."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the robot."""
        pass

    @abstractmethod
    async def write(self, data: bytes) -> None:
        """Write data to the robot.

        Args:
            data: Bytes to send
        """
        pass

    @abstractmethod
    def set_response_callback(self, callback: Callable[[bytes], None]) -> None:
        """Set callback for received data.

        Args:
            callback: Function to call with received bytes
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected."""
        pass

    @property
    @abstractmethod
    def address(self) -> str:
        """Get the robot's address/identifier."""
        pass

    @property
    def name(self) -> Optional[str]:
        """Get the robot's name (if known)."""
        return None
