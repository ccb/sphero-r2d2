"""
Main R2D2 robot class.
"""

from __future__ import annotations

import asyncio
import struct
from typing import Optional, Dict, Any
from concurrent.futures import Future
from collections import defaultdict

from bleak.backends.device import BLEDevice

from r2d2.adapter import Adapter, BleakAdapter
from r2d2.protocol.packet import Packet, PacketBuilder, PacketCollector
from r2d2.protocol.constants import (
    DeviceId,
    PowerCommand,
    SystemInfoCommand,
    BatteryState,
    ErrorCode,
    DEFAULT_TIMEOUT,
    COMMAND_SAFE_INTERVAL,
)
from r2d2.exceptions import (
    R2D2Error,
    ConnectionError,
    TimeoutError,
    CommandError,
)
from r2d2.components.drive import DriveComponent
from r2d2.components.dome import DomeComponent
from r2d2.components.stance import StanceComponent
from r2d2.components.leds import LEDComponent
from r2d2.components.audio import AudioComponent
from r2d2.components.sensors import SensorComponent


class R2D2:
    """High-level interface for controlling a Sphero R2-D2 robot.

    Example:
        >>> async with R2D2(name="D2-55E3") as r2:
        ...     await r2.dome.set_position(90)
        ...     await r2.drive.roll(heading=0, speed=100, duration=2.0)
        ...     await r2.leds.set_front(255, 0, 0)
    """

    def __init__(
        self,
        device: BLEDevice | str | None = None,
        name: Optional[str] = None,
        adapter: Optional[Adapter] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Args:
            device: BLEDevice from scanning, or address string
            name: Robot name (used for scanning if device not provided)
            adapter: Custom adapter (default: BleakAdapter)
            timeout: Default command timeout
        """
        self._device = device
        self._name = name
        self._timeout = timeout
        self._adapter = adapter
        self._connected = False

        # Protocol handling
        self._packet_builder = PacketBuilder()
        self._packet_collector: Optional[PacketCollector] = None
        self._pending_responses: Dict[tuple, Future] = {}
        self._command_lock = asyncio.Lock()
        self._last_command_time = 0.0

        # Components
        self.drive = DriveComponent(self)
        self.dome = DomeComponent(self)
        self.stance = StanceComponent(self)
        self.leds = LEDComponent(self)
        self.audio = AudioComponent(self)
        self.sensors = SensorComponent(self)

    # Context manager support

    async def __aenter__(self) -> R2D2:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    # Connection management

    async def connect(self) -> None:
        """Connect to the robot."""
        if self._connected:
            return

        # Create adapter if needed
        if self._adapter is None:
            if self._device is None:
                # Need to scan for robot
                from r2d2.scanner import scan_one
                self._device = await scan_one(name=self._name, timeout=self._timeout)

            self._adapter = BleakAdapter(
                self._device,
                name=self._name,
                timeout=self._timeout,
            )

        # Set up packet collector
        self._packet_collector = PacketCollector(self._on_packet_received)
        self._adapter.set_response_callback(self._packet_collector.add)

        # Connect
        await self._adapter.connect()
        self._connected = True

        # Wake robot and initialize
        await self._wake()

    async def disconnect(self) -> None:
        """Disconnect from the robot."""
        if self._adapter:
            await self._adapter.disconnect()
        self._connected = False
        self._pending_responses.clear()

    @property
    def is_connected(self) -> bool:
        """Check if connected to robot."""
        return self._connected and self._adapter is not None and self._adapter.is_connected

    @property
    def name(self) -> Optional[str]:
        """Get robot name."""
        if self._adapter:
            return self._adapter.name
        return self._name

    @property
    def address(self) -> Optional[str]:
        """Get robot BLE address."""
        if self._adapter:
            return self._adapter.address
        return None

    # Robot info

    async def get_battery_voltage(self) -> float:
        """Get battery voltage in volts."""
        response = await self._send_command(
            DeviceId.POWER,
            PowerCommand.GET_BATTERY_VOLTAGE,
        )
        return struct.unpack(">H", response)[0] / 100.0

    async def get_battery_state(self) -> BatteryState:
        """Get battery state."""
        response = await self._send_command(
            DeviceId.POWER,
            PowerCommand.GET_BATTERY_STATE,
        )
        return BatteryState(response[0])

    async def get_battery_percentage(self) -> int:
        """Get battery percentage (0-100)."""
        response = await self._send_command(
            DeviceId.POWER,
            PowerCommand.GET_BATTERY_PERCENTAGE,
        )
        return response[0]

    async def get_firmware_version(self) -> str:
        """Get main app firmware version."""
        response = await self._send_command(
            DeviceId.SYSTEM_INFO,
            SystemInfoCommand.GET_MAIN_APP_VERSION,
        )
        major, minor, patch = struct.unpack(">HHH", response[:6])
        return f"{major}.{minor}.{patch}"

    # Internal methods

    async def _wake(self) -> None:
        """Wake robot from sleep."""
        await self._send_command(
            DeviceId.POWER,
            PowerCommand.WAKE,
        )

    async def _send_command(
        self,
        did: int,
        cid: int,
        data: bytes = b"",
        timeout: Optional[float] = None,
    ) -> bytes:
        """Send a command and wait for response.

        Args:
            did: Device ID
            cid: Command ID
            data: Command data
            timeout: Response timeout

        Returns:
            Response data bytes
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to robot")

        timeout = timeout or self._timeout

        async with self._command_lock:
            # Enforce command interval
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_command_time
            if elapsed < COMMAND_SAFE_INTERVAL:
                await asyncio.sleep(COMMAND_SAFE_INTERVAL - elapsed)

            # Build packet
            packet = self._packet_builder.build(did, cid, data)

            # Set up response future
            future: Future[Packet] = asyncio.get_event_loop().create_future()
            self._pending_responses[packet.id] = future

            try:
                # Send packet
                await self._adapter.write(packet.encode())
                self._last_command_time = asyncio.get_event_loop().time()

                # Wait for response
                response_packet = await asyncio.wait_for(future, timeout=timeout)

                # Check for errors
                response_packet.check_error()

                return response_packet.data

            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Command timed out (DID={did:#x}, CID={cid:#x})",
                    timeout=timeout,
                )
            finally:
                self._pending_responses.pop(packet.id, None)

    def _on_packet_received(self, packet: Packet) -> None:
        """Handle received packet."""
        # Match to pending request
        future = self._pending_responses.get(packet.id)
        if future and not future.done():
            future.set_result(packet)
