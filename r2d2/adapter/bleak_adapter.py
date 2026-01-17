"""
BLE adapter using Bleak library.

This is the primary adapter for communicating with R2D2 over Bluetooth Low Energy.
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional, Any

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from r2d2.adapter.base import Adapter
from r2d2.protocol.constants import (
    API_V2_UUID,
    HANDSHAKE_UUID,
    HANDSHAKE_DATA,
    COMMAND_SAFE_INTERVAL,
)
from r2d2.exceptions import ConnectionError, DisconnectedError


class BleakAdapter(Adapter):
    """BLE adapter using Bleak library for asyncio-native BLE communication."""

    def __init__(
        self,
        device: BLEDevice | str,
        name: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """
        Args:
            device: BLEDevice from scanning, or address string
            name: Robot name (for display purposes)
            timeout: Connection timeout in seconds
        """
        if isinstance(device, str):
            self._address = device
            self._name = name
        else:
            self._address = device.address
            self._name = name or device.name

        self._timeout = timeout
        self._client: Optional[BleakClient] = None
        self._callback: Optional[Callable[[bytes], None]] = None
        self._connected = False
        self._write_lock = asyncio.Lock()

    @property
    def address(self) -> str:
        return self._address

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None and self._client.is_connected

    async def connect(self) -> None:
        """Connect to the robot and perform handshake."""
        if self._connected:
            return

        try:
            self._client = BleakClient(self._address, timeout=self._timeout)
            await self._client.connect()

            # Perform handshake
            await self._client.write_gatt_char(HANDSHAKE_UUID, HANDSHAKE_DATA)

            # Set up notification handler
            await self._client.start_notify(API_V2_UUID, self._on_notify)

            self._connected = True

        except Exception as e:
            self._connected = False
            if self._client:
                try:
                    await self._client.disconnect()
                except:
                    pass
                self._client = None
            raise ConnectionError(f"Failed to connect to {self._name or self._address}", e)

    async def disconnect(self) -> None:
        """Disconnect from the robot."""
        if self._client:
            try:
                await self._client.stop_notify(API_V2_UUID)
            except:
                pass
            try:
                await self._client.disconnect()
            except:
                pass
            self._client = None
        self._connected = False

    async def write(self, data: bytes) -> None:
        """Write data to the robot, handling packet fragmentation."""
        if not self.is_connected:
            raise DisconnectedError("Not connected to robot")

        async with self._write_lock:
            # Fragment data into 20-byte chunks (BLE MTU)
            remaining = data
            while remaining:
                chunk = remaining[:20]
                remaining = remaining[20:]

                await self._client.write_gatt_char(API_V2_UUID, chunk, response=True)

                # Add delay between chunks
                if remaining:
                    await asyncio.sleep(COMMAND_SAFE_INTERVAL)

    def set_response_callback(self, callback: Callable[[bytes], None]) -> None:
        """Set callback for received data."""
        self._callback = callback

    def _on_notify(self, sender: Any, data: bytearray) -> None:
        """Handle incoming BLE notifications."""
        if self._callback:
            self._callback(bytes(data))
