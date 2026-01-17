"""
Adapter layer for robot communication.

Provides abstraction over different transport mechanisms (BLE, TCP, Mock).
"""

from r2d2.adapter.base import Adapter
from r2d2.adapter.bleak_adapter import BleakAdapter

__all__ = ["Adapter", "BleakAdapter"]
