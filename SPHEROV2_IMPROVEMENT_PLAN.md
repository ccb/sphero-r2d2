# Spherov2.py Improvement Plan

## Overview

This document outlines a comprehensive plan to create a modern, robust Python library for controlling Sphero R2-D2 robots. We are incorporating design patterns from the official Sphero SDK while focusing specifically on R2D2 hardware compatibility.

**Primary Goal**: Create a production-quality Python library optimized for the Sphero R2-D2 robot, capable of reliably controlling a fleet of 200 units.

**Secondary Goals**:
- Maintain support for other Sphero BLE toys (BB-8, BB-9E, Mini, BOLT) where feasible
- Modern async-first Python design
- Comprehensive documentation for educational use

**Non-Goals**:
- Backward API compatibility with the old spherov2.py (we can break the API freely)
- Support for legacy V1 protocol toys (Sphero 2.0, Ollie) - can be added later if needed

**Branch**: `feature/r2d2-v2` (from `spherov2-py/master`)

---

## Critical Constraints

### R2D2 Hardware Compatibility

We have **200 physical R2D2 units** that must continue to work. This is the non-negotiable constraint.

**Known R2D2 Characteristics**:
- Bluetooth Low Energy (BLE) communication
- V2 protocol with escape sequences
- Firmware versions may vary across units (need to document/test)
- Discontinued product - no firmware updates available
- Battery degradation on older units

**Compatibility Testing Requirements**:
- Test on multiple R2D2 units with different firmware versions
- Document minimum supported firmware version
- Test with degraded batteries (low voltage behavior)
- Test BLE range limits and reconnection behavior

### Multi-Robot Considerations

With 200 robots, we need to consider:
- **Concurrent connections**: How many R2D2s can one computer control simultaneously?
- **BLE adapter limitations**: Multiple adapters may be needed
- **Identification**: Reliable way to identify specific robots (by name, address)
- **Batch operations**: Efficiently send commands to multiple robots
- **Error isolation**: One robot failure shouldn't crash the whole system
- **Resource management**: Memory/thread usage with many connections

---

## Phase 0: Validation & Deep Exploration (Foundation)

**Priority**: CRITICAL
**Rationale**: Before making any changes, we must thoroughly understand the protocol, validate R2D2 compatibility, and identify any gaps in our understanding.

### 0.1 R2D2 Hardware Compatibility Audit

#### 0.1.1 Firmware Version Survey
- [ ] Connect to multiple R2D2 units and record firmware versions
- [ ] Document any behavioral differences between firmware versions
- [ ] Identify minimum firmware version for full functionality
- [ ] Test firmware version query command reliability

#### 0.1.2 BLE Characteristics Mapping
- [ ] Document all GATT services and characteristics used by R2D2
- [ ] Verify UUIDs match between units
- [ ] Test MTU negotiation behavior
- [ ] Document connection handshake sequence ("usetheforce...band")

#### 0.1.3 Command Compatibility Testing
Create a test script that exercises ALL R2D2 commands on physical hardware:

```python
# Test matrix for each R2D2 unit
tests = [
    # Movement
    ("roll", {"heading": 0, "speed": 50, "duration": 1}),
    ("stop", {}),
    ("set_heading", {"heading": 180}),

    # Animatronics
    ("set_dome_position", {"angle": 90}),
    ("set_dome_position", {"angle": -90}),
    ("set_stance", {"stance": "tripod"}),
    ("set_stance", {"stance": "bipod"}),
    ("waddle", {"enable": True}),

    # LEDs
    ("set_front_led", {"r": 255, "g": 0, "b": 0}),
    ("set_back_led", {"r": 0, "g": 255, "b": 0}),
    ("set_holo_projector", {"brightness": 255}),
    ("set_logic_displays", {"brightness": 255}),

    # Audio
    ("play_sound", {"sound": "happy"}),
    ("play_sound", {"sound": "sad"}),

    # Animations
    ("play_animation", {"animation": "charger_1"}),

    # Sensors
    ("get_dome_position", {}),
    ("stream_sensors", {"sensors": ["accelerometer", "gyroscope"]}),
]
```

#### 0.1.4 Timing Constraints
- [ ] Measure minimum safe command interval on R2D2
- [ ] Test rapid command sequences for reliability
- [ ] Identify commands that block vs. async commands
- [ ] Document animation/sound playback durations

### 0.2 Protocol Deep Dive

#### 0.2.1 Compare with Official SDK
- [ ] Extract V2 packet structure from official SDK
- [ ] Compare escape sequence handling (0xAB, 0x8D, 0xD8)
- [ ] Verify checksum calculation matches
- [ ] Compare flag byte semantics
- [ ] Document header structure (FLAGS, TID, SID, DID, CID, SEQ, ERR)

#### 0.2.2 R2D2-Specific Protocol Details
- [ ] Document all R2D2 Device IDs (DIDs):
  - Core (0x00)
  - Animatronic (0x17)
  - Sensor (0x18)
  - IO (0x1A)
  - Drive (0x16)
  - Power (0x13)
- [ ] Document all Command IDs (CIDs) per device
- [ ] Document parameter encodings (endianness, types)
- [ ] Document async notification packet formats

#### 0.2.3 Error Code Analysis
- [ ] Test each error code by triggering it intentionally
- [ ] Document which errors are recoverable
- [ ] Identify timeout behaviors
- [ ] Document busy/retry scenarios

### 0.3 Test Suite Development

#### 0.3.1 Unit Tests (No Hardware)
```
tests/
├── unit/
│   ├── test_packet_v2.py      # Packet encode/decode
│   ├── test_checksum.py       # Checksum calculation
│   ├── test_escape.py         # Escape sequence handling
│   ├── test_commands.py       # Command generation
│   └── test_sensor_parse.py   # Sensor data parsing
```

Test cases:
- [ ] Round-trip packet encoding/decoding
- [ ] Edge cases: empty payload, max payload (255 bytes)
- [ ] All escape sequence combinations
- [ ] Malformed packet detection
- [ ] Checksum failure detection

#### 0.3.2 Integration Tests (Hardware Required)
```
tests/
├── integration/
│   ├── test_connection.py     # Connect/disconnect lifecycle
│   ├── test_r2d2_movement.py  # Drive commands
│   ├── test_r2d2_dome.py      # Dome position control
│   ├── test_r2d2_stance.py    # Leg actions
│   ├── test_r2d2_leds.py      # LED control
│   ├── test_r2d2_audio.py     # Sound playback
│   ├── test_r2d2_sensors.py   # Sensor streaming
│   └── test_multi_robot.py    # Multiple R2D2 connections
```

#### 0.3.3 Mock Adapter for Offline Testing
```python
class MockR2D2Adapter:
    """Simulates R2D2 responses for testing without hardware."""

    def __init__(self):
        self.dome_position = 0.0
        self.stance = "bipod"
        self.leds = {...}

    async def write(self, uuid: str, data: bytes) -> None:
        packet = decode_packet(data)
        response = self._generate_response(packet)
        await self._notify_callback(response)

    def _generate_response(self, packet: Packet) -> bytes:
        # Simulate R2D2 responses based on command
        ...
```

### 0.4 Deliverables

- [ ] `docs/R2D2_PROTOCOL.md` - Complete R2D2 protocol specification
- [ ] `docs/R2D2_COMMANDS.md` - All R2D2 commands with parameters and examples
- [ ] `docs/FIRMWARE_COMPATIBILITY.md` - Firmware version compatibility notes
- [ ] `tests/` - Comprehensive test suite
- [ ] `VALIDATION_REPORT.md` - Hardware testing results from multiple units

---

## Phase 1: Core Architecture (Clean Slate)

**Priority**: High
**Dependencies**: Phase 0 complete

Since we're not constrained by backward compatibility, we can design the ideal architecture.

### 1.1 Design Principles

1. **Async-first**: Native asyncio throughout, with sync wrappers for convenience
2. **R2D2-optimized**: First-class R2D2 support, other toys as extensions
3. **Type-safe**: Full type hints, validated with mypy strict mode
4. **Explicit over implicit**: Clear error messages, no silent failures
5. **Fleet-ready**: Designed for controlling multiple robots

### 1.2 Package Structure

```
r2d2/                           # Renamed package for clarity
├── __init__.py                 # Public API exports
├── robot.py                    # Main R2D2 class
├── fleet.py                    # Multi-robot management
├── protocol/
│   ├── __init__.py
│   ├── packet.py               # V2 packet encode/decode
│   ├── commands.py             # Command definitions
│   ├── constants.py            # DIDs, CIDs, enums
│   └── errors.py               # Error codes
├── adapter/
│   ├── __init__.py
│   ├── base.py                 # Abstract adapter interface
│   ├── bleak.py                # BLE adapter using Bleak
│   ├── tcp.py                  # TCP relay adapter
│   └── mock.py                 # Mock adapter for testing
├── components/
│   ├── __init__.py
│   ├── drive.py                # Movement control
│   ├── dome.py                 # Head/dome control
│   ├── stance.py               # Leg control
│   ├── leds.py                 # LED control
│   ├── audio.py                # Sound/animation control
│   └── sensors.py              # Sensor streaming
├── utils/
│   ├── __init__.py
│   ├── logging.py              # Logging configuration
│   ├── filters.py              # Sensor data filters
│   └── validation.py           # Input validation
├── scanner.py                  # Robot discovery
├── exceptions.py               # Exception hierarchy
└── config.py                   # Configuration
```

### 1.3 Core R2D2 Class Design

```python
class R2D2:
    """High-level interface for controlling a Sphero R2-D2 robot."""

    def __init__(
        self,
        address: str | None = None,
        name: str | None = None,
        adapter: Adapter | None = None,
        config: R2D2Config | None = None,
    ):
        """
        Create an R2D2 instance.

        Args:
            address: BLE address (e.g., "AA:BB:CC:DD:EE:FF")
            name: Robot name for discovery (e.g., "D2-ABCD")
            adapter: Custom adapter (default: BleakAdapter)
            config: Configuration options
        """
        self.drive = DriveComponent(self)
        self.dome = DomeComponent(self)
        self.stance = StanceComponent(self)
        self.leds = LEDComponent(self)
        self.audio = AudioComponent(self)
        self.sensors = SensorComponent(self)

    # Async context manager
    async def __aenter__(self) -> 'R2D2':
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.disconnect()

    # Sync context manager (convenience wrapper)
    def __enter__(self) -> 'R2D2':
        asyncio.run(self.connect())
        return self

    def __exit__(self, *args) -> None:
        asyncio.run(self.disconnect())

    # Connection
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def reconnect(self) -> None: ...

    @property
    def is_connected(self) -> bool: ...

    @property
    def firmware_version(self) -> str: ...

    @property
    def battery_level(self) -> float: ...

# Usage examples:

# Async usage (recommended)
async def main():
    async with R2D2(name="D2-ABCD") as r2:
        await r2.dome.set_position(90)
        await r2.leds.set_front(255, 0, 0)
        await r2.audio.play_sound(R2D2.Sounds.HAPPY)
        await r2.drive.roll(heading=0, speed=100, duration=2.0)

# Sync usage (convenience)
with R2D2(name="D2-ABCD") as r2:
    r2.dome.set_position_sync(90)
    r2.drive.roll_sync(heading=0, speed=100, duration=2.0)
```

### 1.4 Fleet Management

```python
class R2D2Fleet:
    """Manage multiple R2D2 robots simultaneously."""

    def __init__(self, max_concurrent: int = 10):
        self.robots: Dict[str, R2D2] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def discover(
        self,
        timeout: float = 10.0,
        name_filter: str | None = None,
    ) -> List[R2D2Info]:
        """Discover available R2D2 robots."""
        ...

    async def connect(self, *addresses: str) -> None:
        """Connect to multiple robots concurrently."""
        async with asyncio.TaskGroup() as tg:
            for addr in addresses:
                tg.create_task(self._connect_one(addr))

    async def connect_all(self, timeout: float = 30.0) -> None:
        """Discover and connect to all available R2D2s."""
        ...

    async def broadcast(
        self,
        command: Callable[[R2D2], Awaitable[None]],
        parallel: bool = True,
    ) -> Dict[str, Result]:
        """
        Send a command to all connected robots.

        Args:
            command: Async function to call on each robot
            parallel: Execute in parallel (True) or sequentially (False)

        Returns:
            Dict mapping robot address to success/failure result

        Example:
            results = await fleet.broadcast(
                lambda r: r.leds.set_front(255, 0, 0)
            )
        """
        ...

    async def disconnect_all(self) -> None:
        """Disconnect from all robots."""
        ...

    def __getitem__(self, key: str) -> R2D2:
        """Get robot by address or name."""
        ...

    def __iter__(self) -> Iterator[R2D2]:
        """Iterate over connected robots."""
        ...

    def __len__(self) -> int:
        """Number of connected robots."""
        ...

# Usage:
async def light_show():
    fleet = R2D2Fleet(max_concurrent=20)

    # Connect to specific robots
    await fleet.connect("AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02")

    # Or discover and connect to all
    await fleet.connect_all(timeout=60.0)

    print(f"Connected to {len(fleet)} robots")

    # Broadcast command to all
    await fleet.broadcast(lambda r: r.leds.set_front(255, 0, 0))

    # Sequential wave effect
    for i, robot in enumerate(fleet):
        await robot.audio.play_sound(R2D2.Sounds.HAPPY)
        await asyncio.sleep(0.2)

    await fleet.disconnect_all()
```

### 1.5 Exception Hierarchy

```python
class R2D2Error(Exception):
    """Base exception for all R2D2 errors."""
    pass

class ConnectionError(R2D2Error):
    """Failed to connect to robot."""
    pass

class DisconnectedError(R2D2Error):
    """Robot disconnected unexpectedly."""
    pass

class CommandError(R2D2Error):
    """Command execution failed."""
    def __init__(self, error_code: ErrorCode, command: str):
        self.error_code = error_code
        self.command = command
        super().__init__(f"{command} failed: {error_code.name}")

class TimeoutError(R2D2Error):
    """Command timed out waiting for response."""
    pass

class InvalidParameterError(R2D2Error):
    """Invalid parameter value."""
    pass

class UnsupportedFirmwareError(R2D2Error):
    """Firmware version doesn't support this feature."""
    pass
```

### 1.6 Logging System

```python
import logging

# Logger hierarchy
# r2d2              - Root logger
# r2d2.connection   - Connect/disconnect events
# r2d2.protocol     - Packet encode/decode (DEBUG: hex dumps)
# r2d2.commands     - Command execution
# r2d2.sensors      - Sensor data streaming
# r2d2.fleet        - Multi-robot operations

# Configuration
def configure_logging(
    level: int = logging.WARNING,
    format: str = "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    protocol_level: int = logging.WARNING,  # Separate control for noisy protocol logs
):
    """Configure R2D2 library logging."""
    ...

# Usage
import logging
logging.getLogger('r2d2').setLevel(logging.DEBUG)
logging.getLogger('r2d2.protocol').setLevel(logging.WARNING)  # Less noise
```

### 1.7 Configuration

```python
@dataclass
class R2D2Config:
    """Configuration options for R2D2 connection."""

    # Timeouts
    connect_timeout: float = 10.0
    command_timeout: float = 5.0
    disconnect_timeout: float = 3.0

    # Retry behavior
    max_retries: int = 3
    retry_delay: float = 0.5
    retry_backoff: float = 1.5  # Exponential backoff multiplier

    # Command timing
    command_interval: float = 0.05  # Minimum time between commands

    # Connection
    auto_reconnect: bool = True
    reconnect_attempts: int = 5

    # Logging
    log_level: int = logging.WARNING
    log_packets: bool = False  # Log raw packet hex at DEBUG level

# Global default config
DEFAULT_CONFIG = R2D2Config()

# Per-robot override
robot = R2D2(config=R2D2Config(command_timeout=10.0))
```

---

## Phase 2: Component Implementation

**Priority**: High
**Dependencies**: Phase 1 architecture defined

### 2.1 Drive Component

```python
class DriveComponent:
    """Control R2D2 movement."""

    async def roll(
        self,
        heading: int,
        speed: int,
        duration: float | None = None,
    ) -> None:
        """
        Roll in a direction at a speed.

        Args:
            heading: Direction in degrees (0-359). 0 is forward.
            speed: Speed from -255 (reverse) to 255 (forward).
            duration: Optional duration in seconds. If None, rolls until stopped.
        """
        ...

    async def stop(self) -> None:
        """Stop all movement immediately."""
        ...

    async def set_heading(self, heading: int) -> None:
        """Rotate to face a heading without moving."""
        ...

    async def turn(self, degrees: int, speed: int = 100) -> None:
        """
        Turn by a relative number of degrees.

        Args:
            degrees: Degrees to turn. Positive = right, negative = left.
            speed: Turn speed (1-255).
        """
        ...

    async def raw_motor(
        self,
        left: int,
        right: int,
        duration: float | None = None,
    ) -> None:
        """
        Direct motor control, bypassing stabilization.

        Args:
            left: Left motor power (-255 to 255).
            right: Right motor power (-255 to 255).
            duration: Optional duration in seconds.
        """
        ...

    # Sync wrappers
    def roll_sync(self, heading: int, speed: int, duration: float | None = None) -> None:
        asyncio.run(self.roll(heading, speed, duration))

    def stop_sync(self) -> None:
        asyncio.run(self.stop())
```

### 2.2 Dome Component

```python
class DomeComponent:
    """Control R2D2's rotating dome (head)."""

    async def set_position(self, angle: float) -> None:
        """
        Set dome position.

        Args:
            angle: Position in degrees. Range: -160 to 180.
                   0 = forward, positive = right, negative = left.
        """
        if not -160 <= angle <= 180:
            raise InvalidParameterError(f"Dome angle must be -160 to 180, got {angle}")
        ...

    async def get_position(self) -> float:
        """Get current dome position in degrees."""
        ...

    async def center(self) -> None:
        """Center the dome (set to 0 degrees)."""
        await self.set_position(0)

    async def scan(
        self,
        left: float = -90,
        right: float = 90,
        speed: float = 1.0,
    ) -> None:
        """
        Scan dome back and forth.

        Args:
            left: Left limit in degrees.
            right: Right limit in degrees.
            speed: Scan speed multiplier.
        """
        ...
```

### 2.3 Stance Component

```python
class Stance(Enum):
    BIPOD = "bipod"      # Two legs (standing)
    TRIPOD = "tripod"    # Three legs (for rolling)

class StanceComponent:
    """Control R2D2's leg configuration."""

    async def set_stance(self, stance: Stance) -> None:
        """
        Set leg stance.

        Args:
            stance: BIPOD (2 legs) or TRIPOD (3 legs).
                    Must be in TRIPOD for rolling.
        """
        ...

    async def get_stance(self) -> Stance:
        """Get current stance."""
        ...

    async def waddle(self, enable: bool = True) -> None:
        """
        Enable/disable waddle mode (walking).

        Note: Robot must be in BIPOD stance for waddling.
        """
        ...

    async def is_waddling(self) -> bool:
        """Check if currently waddling."""
        ...
```

### 2.4 LED Component

```python
@dataclass
class Color:
    r: int  # 0-255
    g: int  # 0-255
    b: int  # 0-255

    @classmethod
    def from_hex(cls, hex_color: str) -> 'Color':
        """Create from hex string like '#FF0000' or 'FF0000'."""
        ...

    # Predefined colors
    RED = Color(255, 0, 0)
    GREEN = Color(0, 255, 0)
    BLUE = Color(0, 0, 255)
    WHITE = Color(255, 255, 255)
    OFF = Color(0, 0, 0)

class LEDComponent:
    """Control R2D2's LEDs."""

    async def set_front(self, r: int, g: int, b: int) -> None:
        """Set front LED color (RGB 0-255)."""
        ...

    async def set_front_color(self, color: Color) -> None:
        """Set front LED to a Color."""
        await self.set_front(color.r, color.g, color.b)

    async def set_back(self, r: int, g: int, b: int) -> None:
        """Set back LED color (RGB 0-255)."""
        ...

    async def set_holo_projector(self, brightness: int) -> None:
        """
        Set holographic projector brightness.

        Args:
            brightness: 0 (off) to 255 (full).
        """
        ...

    async def set_logic_displays(self, brightness: int) -> None:
        """
        Set logic display brightness (the blinking lights).

        Args:
            brightness: 0 (off) to 255 (full).
        """
        ...

    async def all_off(self) -> None:
        """Turn off all LEDs."""
        ...

    async def set_all(
        self,
        front: Color | None = None,
        back: Color | None = None,
        holo: int | None = None,
        logic: int | None = None,
    ) -> None:
        """Set multiple LEDs in one command."""
        ...
```

### 2.5 Audio Component

```python
class AudioComponent:
    """Control R2D2 sounds and animations."""

    async def play_sound(
        self,
        sound: R2D2.Sounds,
        wait: bool = False,
    ) -> None:
        """
        Play a sound effect.

        Args:
            sound: Sound to play (from R2D2.Sounds enum).
            wait: If True, wait for sound to complete.
        """
        ...

    async def play_animation(
        self,
        animation: R2D2.Animations,
        wait: bool = True,
    ) -> None:
        """
        Play an animation (movement + lights + sound).

        Args:
            animation: Animation to play (from R2D2.Animations enum).
            wait: If True, wait for animation to complete.
        """
        ...

    async def stop_audio(self) -> None:
        """Stop currently playing sound."""
        ...

# Sound and Animation enums attached to R2D2 class
class R2D2:
    class Sounds(IntEnum):
        # Categorized for easy discovery
        # Happy sounds
        HAPPY = 0x00
        EXCITED = 0x01
        CHEERFUL = 0x02
        ...
        # Sad sounds
        SAD = 0x10
        ...
        # Alert sounds
        ALARM = 0x20
        ...
        # (500+ sounds total)

    class Animations(IntEnum):
        CHARGER_1 = 0x00
        CHARGER_2 = 0x01
        ...
        # (55+ animations)
```

### 2.6 Sensor Component

```python
@dataclass
class SensorData:
    """Container for sensor readings."""
    timestamp: float
    accelerometer: Optional[Vec3] = None
    gyroscope: Optional[Vec3] = None
    orientation: Optional[Orientation] = None
    dome_position: Optional[float] = None

@dataclass
class Vec3:
    x: float
    y: float
    z: float

@dataclass
class Orientation:
    pitch: float
    roll: float
    yaw: float

class SensorComponent:
    """Access R2D2 sensor data."""

    async def start_streaming(
        self,
        sensors: List[str] = ["accelerometer", "gyroscope"],
        interval_ms: int = 100,
    ) -> None:
        """
        Start streaming sensor data.

        Args:
            sensors: List of sensors to stream.
                     Options: "accelerometer", "gyroscope", "orientation", "dome_position"
            interval_ms: Update interval in milliseconds (minimum 50ms).
        """
        ...

    async def stop_streaming(self) -> None:
        """Stop sensor streaming."""
        ...

    def on_sensor_data(self, callback: Callable[[SensorData], None]) -> None:
        """
        Register callback for sensor data.

        Args:
            callback: Function called with SensorData on each update.
        """
        ...

    async def get_sensor_data(self) -> SensorData:
        """Get current sensor readings (one-shot)."""
        ...

    # Async iterator for streaming
    async def stream(
        self,
        sensors: List[str] = ["accelerometer", "gyroscope"],
        interval_ms: int = 100,
    ) -> AsyncIterator[SensorData]:
        """
        Stream sensor data as an async iterator.

        Example:
            async for data in r2.sensors.stream():
                print(data.accelerometer)
        """
        ...

    def on_collision(self, callback: Callable[[], None]) -> None:
        """Register callback for collision detection."""
        ...
```

---

## Phase 3: Protocol Layer

**Priority**: High
**Dependencies**: Phase 0 complete

### 3.1 Packet Implementation

```python
@dataclass
class Packet:
    """V2 protocol packet."""

    flags: int
    device_id: int
    command_id: int
    sequence: int
    target_id: int | None = None
    source_id: int | None = None
    error: ErrorCode | None = None
    data: bytes = b''

    def encode(self) -> bytes:
        """Encode packet to bytes with escaping."""
        ...

    @classmethod
    def decode(cls, data: bytes) -> 'Packet':
        """Decode bytes to packet, handling escape sequences."""
        ...

    @property
    def id(self) -> Tuple[int, int, int]:
        """Unique identifier for matching responses (DID, CID, SEQ)."""
        return (self.device_id, self.command_id, self.sequence)

class PacketBuilder:
    """Build packets with automatic sequence numbering."""

    def __init__(self):
        self._sequence = 0

    def build(
        self,
        device_id: int,
        command_id: int,
        data: bytes = b'',
        expects_response: bool = True,
        target_id: int | None = None,
    ) -> Packet:
        """Build a command packet."""
        seq = self._sequence
        self._sequence = (self._sequence + 1) % 256

        flags = 0
        if expects_response:
            flags |= Flags.REQUESTS_RESPONSE
        if target_id is not None:
            flags |= Flags.HAS_TARGET

        return Packet(
            flags=flags,
            device_id=device_id,
            command_id=command_id,
            sequence=seq,
            target_id=target_id,
            data=data,
        )
```

### 3.2 Command Definitions

```python
# Device IDs
class DeviceID(IntEnum):
    CORE = 0x00
    POWER = 0x13
    DRIVE = 0x16
    ANIMATRONIC = 0x17
    SENSOR = 0x18
    IO = 0x1A

# Command definitions with parameter types
@dataclass
class CommandDef:
    device_id: DeviceID
    command_id: int
    name: str
    params: List[ParamDef]
    response_params: List[ParamDef] = field(default_factory=list)
    expects_response: bool = True

@dataclass
class ParamDef:
    name: str
    type: str  # 'uint8', 'int16', 'float', etc.

    def encode(self, value: Any) -> bytes:
        """Encode value to bytes."""
        ...

    def decode(self, data: bytes) -> Any:
        """Decode bytes to value."""
        ...

# R2D2 Command Registry
COMMANDS = {
    'set_dome_position': CommandDef(
        device_id=DeviceID.ANIMATRONIC,
        command_id=0x0F,
        name='set_dome_position',
        params=[ParamDef('angle', 'float')],
    ),
    'get_dome_position': CommandDef(
        device_id=DeviceID.ANIMATRONIC,
        command_id=0x06,
        name='get_dome_position',
        params=[],
        response_params=[ParamDef('angle', 'float')],
    ),
    'perform_leg_action': CommandDef(
        device_id=DeviceID.ANIMATRONIC,
        command_id=0x0D,
        name='perform_leg_action',
        params=[ParamDef('action', 'uint8')],
    ),
    # ... all other commands
}
```

### 3.3 Response Handling

```python
class ResponseHandler:
    """Handle command responses and async notifications."""

    def __init__(self):
        self._pending: Dict[Tuple, asyncio.Future] = {}
        self._listeners: Dict[Tuple, List[Callable]] = defaultdict(list)

    def expect_response(
        self,
        packet_id: Tuple[int, int, int],
        timeout: float,
    ) -> asyncio.Future:
        """Register expectation for a response."""
        future = asyncio.Future()
        self._pending[packet_id] = future

        # Auto-cleanup on timeout
        asyncio.create_task(self._timeout_handler(packet_id, timeout))

        return future

    def handle_packet(self, packet: Packet) -> None:
        """Handle incoming packet (response or notification)."""
        key = packet.id

        # Check for pending response
        if key in self._pending:
            future = self._pending.pop(key)
            if packet.error and packet.error != ErrorCode.SUCCESS:
                future.set_exception(CommandError(packet.error, str(key)))
            else:
                future.set_result(packet)

        # Notify listeners (for async notifications like sensor data)
        for listener in self._listeners.get((packet.device_id, packet.command_id), []):
            try:
                listener(packet)
            except Exception as e:
                logger.exception(f"Listener error: {e}")

    def add_listener(
        self,
        device_id: int,
        command_id: int,
        callback: Callable[[Packet], None],
    ) -> None:
        """Add listener for async notifications."""
        self._listeners[(device_id, command_id)].append(callback)
```

---

## Phase 4: Testing & Validation

**Priority**: High
**Dependencies**: Phases 1-3

### 4.1 Hardware Test Matrix

```
| Test Case                    | R2D2 #1 | R2D2 #2 | R2D2 #3 | ... |
|------------------------------|---------|---------|---------|-----|
| Firmware Version             | x.x.x   | x.x.x   | x.x.x   |     |
| Connect                      | PASS    | PASS    | PASS    |     |
| Disconnect                   | PASS    | PASS    | PASS    |     |
| Reconnect                    | PASS    | PASS    | PASS    |     |
| Roll forward                 | PASS    | PASS    | PASS    |     |
| Roll backward                | PASS    | PASS    | PASS    |     |
| Turn left/right              | PASS    | PASS    | PASS    |     |
| Dome position (-160)         | PASS    | PASS    | PASS    |     |
| Dome position (0)            | PASS    | PASS    | PASS    |     |
| Dome position (180)          | PASS    | PASS    | PASS    |     |
| Stance: bipod                | PASS    | PASS    | PASS    |     |
| Stance: tripod               | PASS    | PASS    | PASS    |     |
| Waddle                       | PASS    | PASS    | PASS    |     |
| Front LED                    | PASS    | PASS    | PASS    |     |
| Back LED                     | PASS    | PASS    | PASS    |     |
| Holo projector               | PASS    | PASS    | PASS    |     |
| Logic displays               | PASS    | PASS    | PASS    |     |
| Play sound                   | PASS    | PASS    | PASS    |     |
| Play animation               | PASS    | PASS    | PASS    |     |
| Sensor streaming             | PASS    | PASS    | PASS    |     |
| Collision detection          | PASS    | PASS    | PASS    |     |
| Low battery behavior         | PASS    | PASS    | PASS    |     |
| Range test (10m)             | PASS    | PASS    | PASS    |     |
```

### 4.2 Multi-Robot Test Scenarios

```python
# Test: Connect to N robots simultaneously
async def test_multi_connect(n: int = 10):
    fleet = R2D2Fleet()
    robots = await fleet.discover(timeout=30)

    assert len(robots) >= n

    start = time.time()
    await fleet.connect(*[r.address for r in robots[:n]])
    connect_time = time.time() - start

    assert len(fleet) == n
    print(f"Connected to {n} robots in {connect_time:.1f}s")

    await fleet.disconnect_all()

# Test: Broadcast command to all robots
async def test_broadcast():
    fleet = R2D2Fleet()
    await fleet.connect_all()

    results = await fleet.broadcast(lambda r: r.leds.set_front(255, 0, 0))

    failures = [addr for addr, result in results.items() if not result.success]
    assert len(failures) == 0, f"Failed on: {failures}"

# Test: Error isolation (one robot failure doesn't affect others)
async def test_error_isolation():
    fleet = R2D2Fleet()
    await fleet.connect_all()

    # Disconnect one robot manually to simulate failure
    rogue = list(fleet)[0]
    await rogue.disconnect()

    # Broadcast should still work for others
    results = await fleet.broadcast(lambda r: r.leds.set_front(0, 255, 0))

    successes = sum(1 for r in results.values() if r.success)
    assert successes == len(fleet) - 1
```

### 4.3 Stress Tests

```python
# Test: Rapid command sequences
async def test_rapid_commands(robot: R2D2, count: int = 100):
    """Send many commands rapidly to test timing/buffering."""
    for i in range(count):
        await robot.leds.set_front(i % 256, 0, 0)
    # Should complete without errors or timeouts

# Test: Long-running sensor streaming
async def test_sensor_stability(robot: R2D2, duration_minutes: int = 60):
    """Stream sensors for extended period to check for memory leaks."""
    samples = []

    async for data in robot.sensors.stream():
        samples.append(data)
        if len(samples) % 1000 == 0:
            print(f"Collected {len(samples)} samples")
        if len(samples) >= duration_minutes * 60 * 10:  # 10 Hz
            break

    # Check for gaps/errors
    ...

# Test: Reconnection stability
async def test_reconnection_cycle(robot: R2D2, cycles: int = 10):
    """Connect/disconnect repeatedly to test stability."""
    for i in range(cycles):
        await robot.connect()
        await robot.leds.set_front(0, 255, 0)  # Verify working
        await robot.disconnect()
        await asyncio.sleep(1)
    # Should complete without errors
```

---

## Phase 5: Documentation

**Priority**: Medium-High
**Dependencies**: Core implementation stable

### 5.1 User Documentation

```
docs/
├── index.md                    # Overview and quick start
├── installation.md             # Installation instructions
├── quickstart.md               # 5-minute getting started
├── tutorials/
│   ├── basic_movement.md       # Rolling, turning, stopping
│   ├── dome_control.md         # Head positioning
│   ├── leds_and_sounds.md      # Visual and audio feedback
│   ├── sensors.md              # Reading sensor data
│   ├── animations.md           # Playing animations
│   └── multi_robot.md          # Fleet management
├── api/
│   ├── r2d2.md                 # Main R2D2 class
│   ├── components.md           # Drive, Dome, LEDs, etc.
│   ├── fleet.md                # R2D2Fleet class
│   ├── config.md               # Configuration options
│   └── exceptions.md           # Error handling
├── advanced/
│   ├── protocol.md             # Protocol deep-dive
│   ├── custom_commands.md      # Sending raw commands
│   ├── adapters.md             # BLE, TCP, Mock adapters
│   └── troubleshooting.md      # Common issues
└── reference/
    ├── sounds.md               # All 500+ sounds listed
    ├── animations.md           # All animations listed
    └── commands.md             # Low-level command reference
```

### 5.2 Example Programs

```
examples/
├── 01_hello_r2d2.py           # Connect and beep
├── 02_movement.py             # Basic rolling
├── 03_dome_scan.py            # Dome movement
├── 04_light_show.py           # LED patterns
├── 05_sound_board.py          # Play various sounds
├── 06_sensor_display.py       # Print sensor data
├── 07_collision_react.py      # React to collisions
├── 08_dance_routine.py        # Choreographed movement
├── 09_remote_control.py       # Keyboard control
├── 10_fleet_demo.py           # Multiple robots
└── advanced/
    ├── async_patterns.py      # Async programming examples
    ├── sensor_recording.py    # Record and export data
    ├── custom_animation.py    # Programmatic animations
    └── classroom_demo.py      # Educational demo for 20+ robots
```

---

## Phase 6: Polish & Release

**Priority**: Medium
**Dependencies**: All previous phases

### 6.1 Package Setup

```toml
# pyproject.toml
[project]
name = "r2d2"
version = "2.0.0"
description = "Python library for controlling Sphero R2-D2 robots"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = [
    "bleak>=0.21.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "mypy>=1.0",
    "ruff>=0.1",
]

[tool.mypy]
strict = true
```

### 6.2 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest tests/unit/
      - run: mypy src/
      - run: ruff check src/
```

### 6.3 Release Checklist

- [ ] All unit tests passing
- [ ] Hardware tests passing on 3+ R2D2 units
- [ ] Multi-robot tests passing
- [ ] Documentation complete
- [ ] Examples all working
- [ ] Type checking passing (mypy strict)
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Tagged release
- [ ] Published to PyPI

---

## Future Enhancements (Low Priority)

### Rich Text-Based UI

Add beautiful terminal interfaces using the [Rich](https://rich.readthedocs.io/) library for improved user experience in validation tools, fleet management, and sensor monitoring.

**Dependency**: `pip install rich`

#### Validation Test Output

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Firmware survey results as a styled table
table = Table(title="R2D2 Firmware Survey")
table.add_column("Robot", style="cyan")
table.add_column("Main App", style="green")
table.add_column("Bootloader", style="yellow")
table.add_column("Status", style="bold")
table.add_row("D2-55E3", "7.0.101", "4.1.18", "[green]✓ Working[/]")
table.add_row("D2-1234", "7.0.99", "4.1.17", "[yellow]⚠ Needs Update[/]")
console.print(table)

# Progress during command tests
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console
) as progress:
    task = progress.add_task("Testing dome control...", total=None)
    # ... run tests
```

#### Fleet Management Dashboard

```python
from rich.live import Live
from rich.layout import Layout

# Real-time fleet status display
def create_fleet_dashboard(fleet):
    layout = Layout()
    layout.split_column(
        Layout(Panel("R2D2 Fleet Dashboard", style="bold blue"), size=3),
        Layout(name="main")
    )

    # Robot status cards
    robot_panels = []
    for robot in fleet:
        status = f"[green]●[/] Connected" if robot.is_connected else "[red]●[/] Disconnected"
        panel = Panel(
            f"Battery: {robot.battery_level:.0%}\n"
            f"Stance: {robot.stance}\n"
            f"Dome: {robot.dome_position}°",
            title=robot.name,
            subtitle=status
        )
        robot_panels.append(panel)

    return layout

# Live updating display
with Live(create_fleet_dashboard(fleet), refresh_per_second=2):
    await fleet.broadcast(lambda r: r.leds.set_front(0, 255, 0))
```

#### Sensor Streaming Display

```python
from rich.live import Live
from rich.table import Table

# Real-time sensor data visualization
async def display_sensors(robot):
    with Live(console=console, refresh_per_second=10) as live:
        async for data in robot.sensors.stream():
            table = Table(title=f"Sensors: {robot.name}")
            table.add_column("Sensor")
            table.add_column("X", justify="right")
            table.add_column("Y", justify="right")
            table.add_column("Z", justify="right")

            if data.accelerometer:
                a = data.accelerometer
                table.add_row("Accel", f"{a.x:.2f}", f"{a.y:.2f}", f"{a.z:.2f}")
            if data.gyroscope:
                g = data.gyroscope
                table.add_row("Gyro", f"{g.x:.2f}", f"{g.y:.2f}", f"{g.z:.2f}")

            live.update(table)
```

#### Command-Line Interface

```python
from rich.prompt import Prompt, Confirm
from rich.tree import Tree

# Interactive robot selection
def select_robot(discovered_robots):
    tree = Tree("🤖 Discovered R2D2s")
    for i, robot in enumerate(discovered_robots, 1):
        tree.add(f"[{i}] {robot.name} ({robot.address})")
    console.print(tree)

    choice = Prompt.ask("Select robot", choices=[str(i) for i in range(1, len(discovered_robots)+1)])
    return discovered_robots[int(choice) - 1]

# Confirmation for destructive actions
if Confirm.ask("Run full test suite? This will move the robot."):
    await run_tests(robot)
```

### Audio Test Verification via Microphone

Use the laptop microphone to automatically verify that R2D2 audio tests actually produce sound, rather than just confirming the command didn't throw an error.

**Dependencies**: `pip install sounddevice numpy scipy`

```python
import sounddevice as sd
import numpy as np
from scipy.signal import find_peaks

def record_audio(duration: float = 2.0, sample_rate: int = 44100) -> np.ndarray:
    """Record audio from default microphone."""
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    return recording.flatten()

def detect_r2d2_sound(audio: np.ndarray, threshold: float = 0.01) -> bool:
    """
    Detect if R2D2-like sounds are present in audio.

    R2D2 sounds are characterized by:
    - High frequency beeps/chirps (1-4 kHz range)
    - Rapid frequency modulation
    - Distinct amplitude envelope
    """
    # Check if audio energy exceeds background noise
    rms = np.sqrt(np.mean(audio**2))
    if rms < threshold:
        return False

    # Perform FFT to check for characteristic frequencies
    fft = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1/44100)

    # R2D2 sounds typically have energy in 1-4 kHz range
    r2d2_band = (freqs > 1000) & (freqs < 4000)
    r2d2_energy = np.sum(fft[r2d2_band])
    total_energy = np.sum(fft)

    # If significant energy in R2D2 frequency range, sound detected
    return (r2d2_energy / total_energy) > 0.3

def test_audio_with_verification():
    """Test audio playback with microphone verification."""
    # Record baseline (silence)
    print("Recording baseline...")
    baseline = record_audio(1.0)
    baseline_rms = np.sqrt(np.mean(baseline**2))

    # Play sound and record
    print("Playing R2D2 sound...")
    toy.play_audio_file(R2D2.Audio.R2_EXCITED_1, 0)
    audio = record_audio(2.0)

    # Verify sound was detected
    if detect_r2d2_sound(audio, threshold=baseline_rms * 2):
        print("PASS: R2D2 sound detected")
        return True
    else:
        print("FAIL: No R2D2 sound detected")
        return False
```

**Use cases:**
- Automated CI testing with physical robots
- Fleet validation (test all 200 robots have working speakers)
- Detecting hardware issues (blown speakers, volume problems)

### Movement Verification via Video Tracking

Use a webcam to track robot movement and automatically verify that drive/movement tests produce actual physical motion. Supports AprilTags (precise) or computer vision (no tags needed).

**Dependencies**: `pip install opencv-python numpy pupil-apriltags`

#### AprilTag Tracking (Recommended for Precision)

```python
import cv2
import numpy as np
from pupil_apriltags import Detector

class RobotTracker:
    """Track R2D2 position using AprilTags attached to robots."""

    def __init__(self, camera_id: int = 0, tag_size_mm: float = 50.0):
        self.cap = cv2.VideoCapture(camera_id)
        self.detector = Detector(families='tag36h11')
        self.tag_size = tag_size_mm
        # Camera calibration (adjust for your camera)
        self.camera_params = [600, 600, 320, 240]  # fx, fy, cx, cy

    def get_robot_position(self, tag_id: int) -> tuple:
        """Get robot position (x, y, rotation) from AprilTag."""
        ret, frame = self.cap.read()
        if not ret:
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = self.detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=self.camera_params,
            tag_size=self.tag_size / 1000  # Convert to meters
        )

        for det in detections:
            if det.tag_id == tag_id:
                # Extract position from pose
                x = det.pose_t[0][0] * 1000  # Convert to mm
                y = det.pose_t[1][0] * 1000
                # Extract rotation (yaw) from rotation matrix
                rotation = np.arctan2(det.pose_R[1][0], det.pose_R[0][0])
                return (x, y, np.degrees(rotation))

        return None

    def close(self):
        self.cap.release()


def test_movement_with_verification(toy, tracker: RobotTracker, tag_id: int):
    """Test robot movement with video verification."""
    # Get starting position
    start_pos = tracker.get_robot_position(tag_id)
    if start_pos is None:
        print("FAIL: Robot not detected")
        return False

    print(f"Start position: {start_pos}")

    # Command robot to move forward
    toy.drive_with_heading(100, 0, 0)  # speed=100, heading=0
    time.sleep(1.0)
    toy.drive_with_heading(0, 0, 0)  # stop
    time.sleep(0.5)

    # Get ending position
    end_pos = tracker.get_robot_position(tag_id)
    if end_pos is None:
        print("FAIL: Robot lost after movement")
        return False

    print(f"End position: {end_pos}")

    # Calculate distance moved
    distance = np.sqrt((end_pos[0] - start_pos[0])**2 +
                       (end_pos[1] - start_pos[1])**2)

    print(f"Distance moved: {distance:.1f}mm")

    if distance > 50:  # Expect at least 50mm movement
        print("PASS: Robot moved as expected")
        return True
    else:
        print("FAIL: Robot did not move enough")
        return False
```

#### Computer Vision Tracking (No Tags Required)

```python
import cv2
import numpy as np

class R2D2VisionTracker:
    """Track R2D2 using computer vision (color/shape detection)."""

    def __init__(self, camera_id: int = 0):
        self.cap = cv2.VideoCapture(camera_id)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()

    def detect_r2d2(self) -> tuple:
        """Detect R2D2 position using color and shape."""
        ret, frame = self.cap.read()
        if not ret:
            return None

        # Convert to HSV for color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # R2D2 is mostly white/silver with blue accents
        # Detect the blue LED or body colors
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Find largest contour (likely the robot)
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 100:
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)

        return None

    def track_movement(self, duration: float = 2.0) -> list:
        """Record positions over time."""
        positions = []
        start_time = time.time()

        while time.time() - start_time < duration:
            pos = self.detect_r2d2()
            if pos:
                positions.append((time.time() - start_time, pos))
            time.sleep(0.05)  # 20 FPS

        return positions

    def calculate_distance(self, positions: list) -> float:
        """Calculate total distance traveled from position list."""
        if len(positions) < 2:
            return 0.0

        total = 0.0
        for i in range(1, len(positions)):
            p1 = positions[i-1][1]
            p2 = positions[i][1]
            total += np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

        return total
```

**Use cases:**
- Automated verification of drive/movement commands
- Detecting motor issues (one wheel not working, drift)
- Measuring actual speed vs commanded speed
- Fleet validation for movement accuracy
- Creating movement calibration profiles per robot

**AprilTag setup:**
- Print tag36h11 family tags (50mm recommended)
- Attach to top of R2D2 dome with removable adhesive
- Assign unique tag ID per robot (store in fleet_database.json)

### Battery Health Monitoring & Fleet Triage

Track battery discharge rates over time to identify robots with degraded batteries. Use this data to triage which robots are healthy enough for student use.

#### Battery Discharge Tracker

```python
import time
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class BatteryReading:
    timestamp: str
    voltage: float
    state: str
    minutes_since_start: float

@dataclass
class DischargeSession:
    robot_name: str
    start_time: str
    readings: List[BatteryReading]
    discharge_rate_mv_per_min: float = None
    estimated_runtime_min: float = None

class BatteryTracker:
    """Monitor battery discharge to identify degraded batteries."""

    def __init__(self, toy, sample_interval_sec: float = 60.0):
        self.toy = toy
        self.sample_interval = sample_interval_sec
        self.readings: List[BatteryReading] = []
        self.start_time = None

    def take_reading(self) -> BatteryReading:
        """Take a single battery reading."""
        from spherov2.commands.power import Power

        voltage = Power.get_battery_voltage(self.toy)
        state = Power.get_battery_state(self.toy).name

        if self.start_time is None:
            self.start_time = time.time()

        reading = BatteryReading(
            timestamp=datetime.now().isoformat(),
            voltage=round(voltage, 3),
            state=state,
            minutes_since_start=round((time.time() - self.start_time) / 60, 2)
        )
        self.readings.append(reading)
        return reading

    def monitor(self, duration_minutes: float = 30.0, activity: str = "idle"):
        """
        Monitor battery for a duration while robot performs activity.

        Args:
            duration_minutes: How long to monitor
            activity: "idle", "leds_on", "continuous_drive", "mixed"
        """
        print(f"Monitoring battery for {duration_minutes} min ({activity} activity)...")
        print(f"Sampling every {self.sample_interval} seconds")

        end_time = time.time() + (duration_minutes * 60)

        while time.time() < end_time:
            reading = self.take_reading()
            print(f"  {reading.minutes_since_start:.1f}min: {reading.voltage:.3f}V ({reading.state})")

            # Perform activity
            if activity == "leds_on":
                self.toy.set_front_led(255, 0, 0)
            elif activity == "continuous_drive":
                self.toy.drive_with_heading(50, 0, 0)
                time.sleep(2)
                self.toy.drive_with_heading(0, 0, 0)

            time.sleep(self.sample_interval)

        # Stop any activity
        self.toy.set_front_led(0, 0, 0)
        self.toy.drive_with_heading(0, 0, 0)

        return self.calculate_discharge_rate()

    def calculate_discharge_rate(self) -> dict:
        """Calculate discharge statistics."""
        if len(self.readings) < 2:
            return None

        first = self.readings[0]
        last = self.readings[-1]

        voltage_drop = first.voltage - last.voltage
        time_elapsed = last.minutes_since_start - first.minutes_since_start

        if time_elapsed > 0:
            rate_mv_per_min = (voltage_drop * 1000) / time_elapsed

            # Estimate time from full (4.2V) to empty (3.4V)
            usable_range_mv = 800  # 4.2V - 3.4V
            estimated_runtime = usable_range_mv / rate_mv_per_min if rate_mv_per_min > 0 else float('inf')
        else:
            rate_mv_per_min = 0
            estimated_runtime = float('inf')

        return {
            "voltage_drop_mv": round(voltage_drop * 1000, 1),
            "duration_min": round(time_elapsed, 1),
            "discharge_rate_mv_per_min": round(rate_mv_per_min, 2),
            "estimated_runtime_min": round(estimated_runtime, 0),
            "health_rating": self._rate_battery_health(rate_mv_per_min)
        }

    def _rate_battery_health(self, rate_mv_per_min: float) -> str:
        """Rate battery health based on discharge rate."""
        if rate_mv_per_min <= 0:
            return "UNKNOWN"
        elif rate_mv_per_min < 2.0:
            return "EXCELLENT"  # >6 hours runtime
        elif rate_mv_per_min < 4.0:
            return "GOOD"       # 3-6 hours runtime
        elif rate_mv_per_min < 8.0:
            return "FAIR"       # 1.5-3 hours runtime
        elif rate_mv_per_min < 15.0:
            return "POOR"       # 45min-1.5 hours
        else:
            return "CRITICAL"   # <45 min, needs replacement


def triage_fleet(fleet_db_path: Path) -> dict:
    """
    Analyze fleet database to identify robots needing battery replacement.

    Returns robots sorted by battery health.
    """
    with open(fleet_db_path) as f:
        fleet = json.load(f)

    triage = {
        "student_ready": [],      # EXCELLENT or GOOD
        "limited_use": [],        # FAIR
        "needs_replacement": [],  # POOR or CRITICAL
        "unknown": []             # No discharge data
    }

    for name, robot in fleet.items():
        health = robot.get("battery_health", {}).get("health_rating", "UNKNOWN")

        if health in ("EXCELLENT", "GOOD"):
            triage["student_ready"].append(name)
        elif health == "FAIR":
            triage["limited_use"].append(name)
        elif health in ("POOR", "CRITICAL"):
            triage["needs_replacement"].append(name)
        else:
            triage["unknown"].append(name)

    return triage
```

#### Fleet Database Battery Fields

Add to `fleet_database.json` schema:
```json
{
  "D2-55E3": {
    "battery_health": {
      "last_discharge_test": "2026-01-16",
      "discharge_rate_mv_per_min": 3.2,
      "estimated_runtime_min": 250,
      "health_rating": "GOOD",
      "test_conditions": "mixed activity"
    },
    "battery_history": [
      {"date": "2026-01-16", "voltage": 3.84, "state": "OK"},
      {"date": "2026-01-15", "voltage": 3.91, "state": "OK"}
    ]
  }
}
```

**Use cases:**
- Identify robots safe for 2-hour student sessions
- Schedule battery replacements before failures
- Track battery degradation over semesters
- Generate "robot readiness" reports before class

---

### Battery Replacement Guide

**Good news: Battery replacement IS possible!**

Based on research, the Sphero R2-D2 battery can be replaced, though it requires careful disassembly.

#### Resources

- [iFixit Battery Replacement Guide](https://www.ifixit.com/Guide/Sphero+R2-D2+Battery+Replacement/173037) - Step-by-step instructions
- [Detailed Teardown (Microcontroller Tips)](https://www.microcontrollertips.com/teardown-inside-spheros-r2-d2-toy/) - Internal component photos
- [iFixit R2-D2 Device Page](https://www.ifixit.com/Device/Sphero_R2-D2) - Repair guides and parts

#### Key Information

| Aspect | Details |
|--------|---------|
| Battery Type | Lithium-ion (proprietary connector) |
| Charging | USB (not wireless) |
| Disassembly | Requires specific sequence, like "disassembling a car engine" |
| Connector | Proprietary - must splice wires to new battery |
| Warranty | Opening voids warranty (robots are discontinued anyway) |
| Difficulty | Moderate - accessible once panels removed |

#### Disassembly Notes (from teardown)

1. Remove dome first
2. Side cylindrical panel reveals speaker and Li-ion battery
3. Battery is accessible once panels are off
4. Dome motor uses potentiometer feedback (not encoder)
5. Two main electronics boards + two LED boards

#### Replacement Battery Options

The original battery specs need to be matched:
- Voltage: 3.7V nominal Li-ion
- Capacity: ~600-800mAh (estimated)
- Connector: Proprietary (requires soldering/splicing)

**Potential replacement sources:**
- Generic 3.7V Li-Po packs with similar dimensions
- Harvest from other Sphero devices
- Custom battery pack from 18650 cells (advanced)

#### Recommendation for Fleet

For 200 robots, consider:
1. **Triage first**: Use battery tracker to identify which robots actually need replacement
2. **Batch replacement**: Order replacement cells in bulk
3. **Student project**: Battery replacement could be an educational hardware activity
4. **Spare parts robots**: Keep some non-functional units for harvesting parts

---

### Audio-Based Robot-to-Robot Communication (ggwave)

Use [ggwave](https://github.com/ggerganov/ggwave) for audio-based data transmission between R2D2 units. This is primarily a **fun demonstration feature** that lets robots "talk" to each other using sounds reminiscent of R2-D2's communication style in the Star Wars movies - bleeps, chirps, and warbles that are actually carrying structured data!

**Dependencies**: `pip install ggwave sounddevice numpy`

#### Overview

ggwave is a lightweight library for transmitting small amounts of data over sound using frequency-shift keying (FSK) with error correction. The audible protocols produce sounds in the 1-4kHz range - similar to R2-D2's characteristic beeps and whistles from the films. Key properties:

- **Audio-only communication**: Data encoded into audible or near-ultrasonic tones
- **No pairing required**: Robots can communicate without BLE or WiFi setup
- **Low bandwidth, high reliability**: Designed for short messages (IDs, commands, state)
- **Real-time encode/decode**: Suitable for interactive call-and-response behaviors
- **Cross-platform**: C/C++ with Python bindings

#### Use Cases

1. **Robot-to-robot signaling**: R2D2s can "talk" to each other during group activities
2. **Broadcast commands**: Teacher broadcasts command that all nearby robots hear
3. **Ambient coordination**: Emergent swarm behaviors using sound as medium
4. **Roll call**: Robots identify themselves via audio when prompted
5. **Classroom demos**: Visible/audible communication students can observe

#### Implementation

```python
import ggwave
import sounddevice as sd
import numpy as np
from typing import Optional, Callable
import threading
import queue

class R2D2AudioComm:
    """
    Audio-based communication for R2D2 robots using ggwave.

    Enables robot-to-robot messaging via speaker/microphone.
    """

    # ggwave protocols (in order of speed vs reliability)
    PROTOCOL_ULTRASOUND = 0      # ~18kHz, inaudible, short range
    PROTOCOL_AUDIBLE_FAST = 1    # Audible, faster, less reliable
    PROTOCOL_AUDIBLE_NORMAL = 2  # Audible, balanced (recommended)
    PROTOCOL_AUDIBLE_SLOW = 3    # Audible, slower, most reliable

    def __init__(
        self,
        robot_id: str,
        protocol: int = PROTOCOL_AUDIBLE_NORMAL,
        sample_rate: int = 48000
    ):
        """
        Initialize audio communication.

        Args:
            robot_id: Unique identifier for this robot (e.g., "D2-55E3")
            protocol: ggwave protocol (affects speed/reliability/audibility)
            sample_rate: Audio sample rate in Hz
        """
        self.robot_id = robot_id
        self.protocol = protocol
        self.sample_rate = sample_rate
        self._listening = False
        self._message_queue = queue.Queue()
        self._listeners: list[Callable[[str, str], None]] = []

    def transmit(self, message: str, via_r2d2: bool = True) -> None:
        """
        Transmit a message via audio.

        Args:
            message: Message to send (max ~140 bytes)
            via_r2d2: If True, play through R2D2 speaker (requires toy connection)
                      If False, play through computer speaker
        """
        # Encode message to audio waveform
        waveform = ggwave.encode(
            message,
            protocolId=self.protocol,
            sampleRate=self.sample_rate,
            volume=50
        )

        # Convert to numpy array
        audio = np.frombuffer(waveform, dtype=np.float32)

        if via_r2d2:
            # TODO: Stream audio to R2D2 speaker
            # This requires implementing raw audio streaming via BLE
            raise NotImplementedError("R2D2 speaker transmission not yet implemented")
        else:
            # Play through computer speaker
            sd.play(audio, self.sample_rate)
            sd.wait()

    def broadcast_id(self) -> None:
        """Broadcast this robot's ID."""
        self.transmit(f"ID:{self.robot_id}")

    def send_command(self, target_id: str, command: str) -> None:
        """
        Send a command to a specific robot.

        Args:
            target_id: Target robot ID (or "*" for broadcast)
            command: Command string (e.g., "LED:RED", "MOVE:FWD")
        """
        msg = f"{target_id}:{command}"
        self.transmit(msg)

    def start_listening(self, via_r2d2: bool = False) -> None:
        """
        Start listening for incoming audio messages.

        Args:
            via_r2d2: If True, use R2D2 microphone (if available)
                      If False, use computer microphone
        """
        self._listening = True

        def listen_thread():
            instance = ggwave.init()

            def audio_callback(indata, frames, time_info, status):
                if not self._listening:
                    return

                # Decode any messages in the audio
                result = ggwave.decode(
                    instance,
                    indata.flatten().astype(np.float32).tobytes()
                )

                if result is not None:
                    message = result.decode('utf-8')
                    self._handle_message(message)

            # Open audio input stream
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                callback=audio_callback,
                blocksize=1024
            ):
                while self._listening:
                    sd.sleep(100)

            ggwave.free(instance)

        self._listen_thread = threading.Thread(target=listen_thread, daemon=True)
        self._listen_thread.start()

    def stop_listening(self) -> None:
        """Stop listening for messages."""
        self._listening = False
        if hasattr(self, '_listen_thread'):
            self._listen_thread.join(timeout=1.0)

    def _handle_message(self, message: str) -> None:
        """Process received message."""
        # Parse message format: "TARGET:PAYLOAD"
        if ':' in message:
            parts = message.split(':', 1)
            target = parts[0]
            payload = parts[1] if len(parts) > 1 else ""

            # Check if message is for us
            if target == self.robot_id or target == "*":
                self._message_queue.put((target, payload))

                # Notify listeners
                for listener in self._listeners:
                    try:
                        listener(target, payload)
                    except Exception as e:
                        print(f"Listener error: {e}")

    def on_message(self, callback: Callable[[str, str], None]) -> None:
        """
        Register callback for incoming messages.

        Args:
            callback: Function(target, payload) called when message received
        """
        self._listeners.append(callback)

    def get_message(self, timeout: float = None) -> Optional[tuple[str, str]]:
        """
        Get next received message (blocking).

        Args:
            timeout: Max seconds to wait (None = forever)

        Returns:
            (target, payload) tuple or None if timeout
        """
        try:
            return self._message_queue.get(timeout=timeout)
        except queue.Empty:
            return None


# Example: Classroom call-and-response
async def classroom_rollcall(fleet, teacher_comm: R2D2AudioComm):
    """
    Teacher broadcasts rollcall, each robot responds with ID.
    """
    print("Starting rollcall...")

    # Set up listeners on all robots
    responses = []

    def on_response(target, payload):
        if payload.startswith("ID:"):
            robot_id = payload[3:]
            responses.append(robot_id)
            print(f"  Robot {robot_id} responded!")

    teacher_comm.on_message(on_response)
    teacher_comm.start_listening()

    # Broadcast rollcall command
    teacher_comm.send_command("*", "ROLLCALL")

    # Wait for responses
    await asyncio.sleep(10)

    teacher_comm.stop_listening()
    print(f"Rollcall complete: {len(responses)} robots responded")
    return responses


# Example: Follow-the-leader via audio
async def follow_leader_demo(leader_comm: R2D2AudioComm, followers: list):
    """
    Leader broadcasts movements, followers copy.
    """
    movements = [
        ("MOVE", "FWD:50"),
        ("TURN", "LEFT:90"),
        ("MOVE", "FWD:50"),
        ("LED", "RED"),
        ("SOUND", "HAPPY"),
    ]

    for category, action in movements:
        print(f"Leader: {category}:{action}")
        leader_comm.send_command("*", f"{category}:{action}")
        await asyncio.sleep(2)


# Example: Emergent coordination
class SwarmBehavior:
    """
    Robots coordinate via audio without central control.
    """

    def __init__(self, robot_id: str, comm: R2D2AudioComm):
        self.robot_id = robot_id
        self.comm = comm
        self.neighbors = set()

        comm.on_message(self._on_message)

    def _on_message(self, target, payload):
        if payload.startswith("PING:"):
            sender = payload[5:]
            self.neighbors.add(sender)
            # Respond with our ID
            self.comm.send_command(sender, f"PONG:{self.robot_id}")

        elif payload.startswith("LED:"):
            # Copy neighbor's LED color (swarm behavior)
            color = payload[4:]
            # Apply to our robot...

    def discover_neighbors(self):
        """Broadcast ping to discover nearby robots."""
        self.comm.send_command("*", f"PING:{self.robot_id}")
```

#### Protocol Design Considerations

| Protocol | Frequency | Range | Speed | Best For |
|----------|-----------|-------|-------|----------|
| Ultrasound | ~18kHz | Short | Fast | Quiet environments |
| Audible Fast | 1-4kHz | Medium | Fast | Quick commands |
| Audible Normal | 1-4kHz | Medium | Medium | General use |
| Audible Slow | 1-4kHz | Long | Slow | Noisy classrooms |

#### Message Format

```
TARGET:CATEGORY:PAYLOAD

Examples:
  "*:LED:RED"          - All robots set LED red
  "D2-55E3:MOVE:FWD"   - Specific robot move forward
  "ID:D2-1234"         - Robot identifying itself
  "*:ROLLCALL"         - Request all robots identify
```

#### Hardware Limitations

**Important:** The Sphero R2-D2 firmware does **not support custom audio streaming**. The robot can only play its 500+ pre-recorded sounds - there is no command for raw audio output. This is a firmware limitation, not a library limitation.

#### Deployment Options

| Option | Audio Source | Pros | Cons |
|--------|--------------|------|------|
| **Computer speakers** | Laptop/desktop | Works now, no hardware changes | Robots don't "speak" themselves |
| **Sensor pack + USB audio** | Raspberry Pi on robot | True robot-to-robot communication | Requires sensor pack + audio hardware |

#### Sensor Pack Integration (Recommended)

The [sensor pack](docs/SENSOR-PACK.md) includes a Raspberry Pi Zero mounted on the R2D2. By adding a USB speaker and microphone, each robot can transmit and receive ggwave signals:

```python
# On Raspberry Pi sensor pack
import sounddevice as sd
import ggwave
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI

class R2D2WithAudio:
    """R2D2 with ggwave capability via sensor pack."""

    def __init__(self, robot_id: str):
        self.robot_id = robot_id
        self.toy = scanner.find_R2D2()

    def transmit(self, message: str):
        """Send ggwave message through USB speaker."""
        waveform = ggwave.encode(message, protocolId=2, sampleRate=48000)
        audio = np.frombuffer(waveform, dtype=np.float32)
        sd.play(audio, 48000)
        sd.wait()

    def broadcast_id(self):
        """Announce this robot's ID."""
        self.transmit(f"ID:{self.robot_id}")

    def on_message_received(self, target: str, payload: str):
        """Handle incoming ggwave command."""
        if payload == "LED:RED":
            self.toy.set_front_led(255, 0, 0)
        elif payload == "ROLLCALL":
            self.broadcast_id()
        elif payload.startswith("MOVE:"):
            # Parse and execute movement
            pass
```

**Required hardware additions to sensor pack:**
- USB microphone (~$10)
- USB speaker or I2S DAC + small speaker (~$15)
- Or USB sound card with both (~$20)

This approach makes the robots fully autonomous - they can communicate via audio without any computer involvement.

#### Educational Applications

1. **Communication protocols**: Teach networking concepts with visible/audible data
2. **Swarm robotics**: Emergent behavior from local communication
3. **Signal processing**: Students can visualize/hear the frequency modulation
4. **Distributed systems**: No central server, peer-to-peer coordination
5. **Error correction**: Demonstrate how ggwave handles noise

---

### SLAM (Simultaneous Localization and Mapping)

Enable R2D2 robots to build maps of their environment while tracking their position within it. This is a fundamental robotics capability and excellent for teaching autonomous navigation concepts.

**Dependencies**: `pip install slam-toolbox opencv-python numpy`

#### Overview

SLAM allows a robot to:
1. **Map** - Build a representation of the environment
2. **Localize** - Determine its position within that map
3. **Navigate** - Plan paths through the mapped space

With the sensor pack's camera, ultrasonic, and IR sensors, R2D2 can perform visual and sensor-fusion SLAM.

#### Implementation Approaches

| Approach | Sensors Used | Complexity | Best For |
|----------|--------------|------------|----------|
| **AprilTag SLAM** | Camera + tags | Low | Structured environments (classroom) |
| **Visual SLAM** | Camera only | Medium | General environments |
| **Sensor Fusion** | Camera + ultrasonic + IMU | High | Robust navigation |
| **Multi-Robot SLAM** | Fleet coordination | High | Collaborative mapping |

#### AprilTag-Based SLAM (Recommended Starting Point)

Use AprilTags as landmarks for simple, reliable indoor SLAM. Place tags on walls/obstacles and the robot builds a map of tag positions while localizing itself.

```python
import cv2
import numpy as np
from pupil_apriltags import Detector
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

@dataclass
class Landmark:
    """A detected AprilTag landmark."""
    tag_id: int
    position: Tuple[float, float]  # (x, y) in meters
    last_seen: float  # timestamp

@dataclass
class RobotPose:
    """Robot position and orientation."""
    x: float  # meters
    y: float  # meters
    theta: float  # radians (heading)
    confidence: float  # 0-1

class AprilTagSLAM:
    """Simple SLAM using AprilTags as landmarks."""

    def __init__(self, camera_id: int = 0, tag_size_m: float = 0.05):
        self.cap = cv2.VideoCapture(camera_id)
        self.detector = Detector(families='tag36h11')
        self.tag_size = tag_size_m

        # Camera intrinsics (calibrate for your camera)
        self.camera_params = [600, 600, 320, 240]  # fx, fy, cx, cy

        # Map state
        self.landmarks: Dict[int, Landmark] = {}
        self.pose = RobotPose(0, 0, 0, 0)
        self.pose_history: List[RobotPose] = []

        # Known tag positions (pre-mapped landmarks)
        self.known_tags: Dict[int, Tuple[float, float]] = {}

    def add_known_landmark(self, tag_id: int, x: float, y: float):
        """Add a pre-positioned landmark for localization."""
        self.known_tags[tag_id] = (x, y)

    def update(self) -> Optional[RobotPose]:
        """
        Capture frame, detect tags, update pose estimate.

        Returns:
            Updated robot pose, or None if no tags detected
        """
        ret, frame = self.cap.read()
        if not ret:
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = self.detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=self.camera_params,
            tag_size=self.tag_size
        )

        if not detections:
            return None

        # Process each detected tag
        observations = []
        for det in detections:
            # Extract position relative to camera
            rel_x = det.pose_t[0][0]
            rel_y = det.pose_t[2][0]  # depth = forward
            rel_angle = np.arctan2(rel_x, rel_y)

            observations.append({
                'tag_id': det.tag_id,
                'distance': np.sqrt(rel_x**2 + rel_y**2),
                'angle': rel_angle,
                'confidence': det.decision_margin / 100
            })

            # If this is a known landmark, use for localization
            if det.tag_id in self.known_tags:
                self._update_pose_from_landmark(det, observations[-1])
            else:
                # Unknown tag - add to map
                self._add_landmark(det, observations[-1])

        self.pose_history.append(self.pose)
        return self.pose

    def _update_pose_from_landmark(self, detection, observation):
        """Update pose estimate using known landmark position."""
        known_pos = self.known_tags[detection.tag_id]

        # Calculate robot position from landmark observation
        dist = observation['distance']
        angle = observation['angle']

        # Robot position = landmark position - relative vector
        # (simplified - full implementation needs rotation matrix)
        robot_x = known_pos[0] - dist * np.sin(self.pose.theta + angle)
        robot_y = known_pos[1] - dist * np.cos(self.pose.theta + angle)

        # Weighted update based on confidence
        alpha = observation['confidence'] * 0.3
        self.pose.x = (1 - alpha) * self.pose.x + alpha * robot_x
        self.pose.y = (1 - alpha) * self.pose.y + alpha * robot_y
        self.pose.confidence = min(1.0, self.pose.confidence + 0.1)

    def _add_landmark(self, detection, observation):
        """Add newly discovered landmark to map."""
        dist = observation['distance']
        angle = observation['angle']

        # Estimate landmark position from robot pose
        landmark_x = self.pose.x + dist * np.sin(self.pose.theta + angle)
        landmark_y = self.pose.y + dist * np.cos(self.pose.theta + angle)

        import time
        self.landmarks[detection.tag_id] = Landmark(
            tag_id=detection.tag_id,
            position=(landmark_x, landmark_y),
            last_seen=time.time()
        )

    def update_from_odometry(self, distance: float, turn: float):
        """
        Update pose estimate from wheel odometry.

        Args:
            distance: Distance traveled (meters)
            turn: Angle turned (radians)
        """
        self.pose.theta += turn
        self.pose.x += distance * np.sin(self.pose.theta)
        self.pose.y += distance * np.cos(self.pose.theta)
        self.pose.confidence *= 0.95  # Odometry drift reduces confidence

    def get_map(self) -> dict:
        """Export current map as dictionary."""
        return {
            'landmarks': {
                tag_id: {'x': lm.position[0], 'y': lm.position[1]}
                for tag_id, lm in self.landmarks.items()
            },
            'known_tags': self.known_tags,
            'pose_history': [
                {'x': p.x, 'y': p.y, 'theta': p.theta}
                for p in self.pose_history
            ]
        }

    def save_map(self, filepath: str):
        """Save map to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.get_map(), f, indent=2)

    def load_map(self, filepath: str):
        """Load map from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        self.known_tags = {
            int(k): tuple(v.values())
            for k, v in data.get('known_tags', {}).items()
        }


class R2D2Navigator:
    """Navigate R2D2 using SLAM."""

    def __init__(self, robot, slam: AprilTagSLAM):
        self.robot = robot
        self.slam = slam

    async def go_to(self, target_x: float, target_y: float):
        """
        Navigate to target position using SLAM.

        Args:
            target_x: Target X coordinate (meters)
            target_y: Target Y coordinate (meters)
        """
        while True:
            # Update position estimate
            pose = self.slam.update()
            if pose is None:
                # No landmarks visible - dead reckoning
                await self.robot.drive.roll(heading=0, speed=30, duration=0.5)
                continue

            # Calculate distance and heading to target
            dx = target_x - pose.x
            dy = target_y - pose.y
            distance = np.sqrt(dx**2 + dy**2)

            if distance < 0.1:  # Within 10cm
                await self.robot.drive.stop()
                print(f"Reached target at ({target_x}, {target_y})")
                break

            # Calculate required heading
            target_heading = np.degrees(np.arctan2(dx, dy))
            current_heading = np.degrees(pose.theta)
            turn_angle = target_heading - current_heading

            # Normalize to -180 to 180
            while turn_angle > 180:
                turn_angle -= 360
            while turn_angle < -180:
                turn_angle += 360

            # Execute movement
            if abs(turn_angle) > 15:
                # Turn first
                await self.robot.drive.spin(int(turn_angle))
            else:
                # Drive forward
                speed = min(100, int(distance * 200))
                await self.robot.drive.roll(
                    heading=int(target_heading) % 360,
                    speed=speed,
                    duration=0.3
                )

            # Update odometry estimate
            # (In real implementation, get actual movement from encoders)
            await asyncio.sleep(0.1)

    async def explore(self, duration_sec: float = 60):
        """
        Explore environment, building map.

        Simple exploration: move forward, turn when obstacle detected.
        """
        import time
        start = time.time()

        while time.time() - start < duration_sec:
            # Update SLAM
            self.slam.update()

            # Check ultrasonic for obstacles
            # (Requires sensor pack integration)
            obstacle_distance = await self._get_ultrasonic_distance()

            if obstacle_distance < 0.3:  # 30cm
                # Obstacle ahead - turn
                turn_angle = np.random.choice([-90, 90])
                await self.robot.drive.spin(turn_angle)
                self.slam.update_from_odometry(0, np.radians(turn_angle))
            else:
                # Clear ahead - move forward
                await self.robot.drive.roll(heading=0, speed=50, duration=0.5)
                self.slam.update_from_odometry(0.1, 0)  # Estimate 10cm per 0.5s

            await asyncio.sleep(0.1)

        # Save discovered map
        self.slam.save_map('explored_map.json')
        print(f"Exploration complete. Found {len(self.slam.landmarks)} landmarks.")


# Example: Classroom mapping setup
async def setup_classroom_map():
    """
    Set up AprilTags around classroom for robot localization.
    """
    # Place tags at known positions (measure in meters from origin)
    known_positions = {
        0: (0.0, 0.0),      # Origin (corner of room)
        1: (3.0, 0.0),      # 3m along X axis
        2: (0.0, 4.0),      # 4m along Y axis
        3: (3.0, 4.0),      # Opposite corner
        4: (1.5, 2.0),      # Center of room
    }

    slam = AprilTagSLAM()
    for tag_id, pos in known_positions.items():
        slam.add_known_landmark(tag_id, pos[0], pos[1])

    return slam


# Example: Multi-robot collaborative mapping
async def collaborative_mapping(fleet, duration_sec: float = 120):
    """
    Multiple robots explore and share map data.
    """
    slam_instances = {}
    shared_landmarks = {}

    for robot in fleet.robots:
        slam_instances[robot.name] = AprilTagSLAM()

    async def explore_and_share(robot, slam):
        navigator = R2D2Navigator(robot, slam)
        await navigator.explore(duration_sec / 2)

        # Share discovered landmarks with fleet
        for tag_id, landmark in slam.landmarks.items():
            if tag_id not in shared_landmarks:
                shared_landmarks[tag_id] = []
            shared_landmarks[tag_id].append(landmark.position)

    # Run exploration in parallel
    await asyncio.gather(*[
        explore_and_share(r, slam_instances[r.name])
        for r in fleet.robots
    ])

    # Merge maps by averaging landmark positions
    merged_map = {}
    for tag_id, positions in shared_landmarks.items():
        avg_x = sum(p[0] for p in positions) / len(positions)
        avg_y = sum(p[1] for p in positions) / len(positions)
        merged_map[tag_id] = (avg_x, avg_y)

    print(f"Collaborative mapping complete.")
    print(f"Merged map has {len(merged_map)} landmarks from {len(fleet.robots)} robots.")

    return merged_map
```

#### Hardware Requirements

| Component | Purpose | Included in Sensor Pack? |
|-----------|---------|--------------------------|
| Camera | Visual detection | Yes (1080p) |
| Ultrasonic | Obstacle detection | Yes |
| IR Cliff | Edge detection | Yes |
| IMU | Orientation | R2D2 internal sensors |
| AprilTags | Landmarks | Print yourself |

#### Educational Applications

1. **Introduction to SLAM**: Fundamental robotics concept with visual feedback
2. **Sensor Fusion**: Combine camera, ultrasonic, and odometry data
3. **Path Planning**: A* or RRT algorithms on mapped space
4. **Multi-Robot Coordination**: Collaborative mapping with fleet
5. **Localization Challenges**: Compare different approaches (EKF, particle filter)
6. **Map Representation**: Occupancy grids, topological maps, feature maps

#### Classroom Setup

1. **Print AprilTags**: tag36h11 family, 5cm size, on cardstock
2. **Place at known positions**: Measure and record X,Y coordinates
3. **Create map file**: JSON with tag_id → position mapping
4. **Calibrate camera**: Run camera calibration for accurate pose estimation

#### Future Extensions

- **Visual SLAM (ORB-SLAM)**: No tags needed, uses natural features
- **LiDAR integration**: Add RPLidar for precise distance sensing
- **3D mapping**: Extend to full 3D environment representation
- **Semantic mapping**: Label regions (desk, doorway, obstacle)

---

### Bluetooth-Based Robot-to-Robot Positioning

Use Bluetooth signals to determine relative positions between R2D2 robots without external infrastructure. This enables swarm behaviors and collaborative localization.

#### Positioning Methods

| Method | Accuracy | Hardware | Notes |
|--------|----------|----------|-------|
| **RSSI** | 1-4 meters | Built-in BLE | Works now, coarse positioning |
| **BT 5.1 AoA/AoD** | 0.5-1 meter | Antenna arrays | Requires hardware upgrade |
| **UWB** | 10-30 cm | DW1000 module | Best accuracy, add-on needed |
| **Hybrid** | Variable | Mixed | Combine for best results |

#### RSSI-Based Ranging (Works with Existing Hardware)

The R2D2's built-in BLE radio can measure signal strength from other robots. While accuracy is limited (1-4 meters), this enables:
- Detecting "nearby" vs "far" robots
- Forming loose clusters
- Avoiding collisions at close range
- Simple swarm behaviors

```python
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

@dataclass
class RobotSighting:
    """A detected nearby robot."""
    name: str
    address: str
    rssi: int  # Signal strength in dBm
    estimated_distance: float  # meters
    timestamp: float

class BluetoothRanging:
    """Estimate distances to other R2D2 robots using BLE RSSI."""

    # Calibration constants (tune for your environment)
    RSSI_AT_1M = -59  # Expected RSSI at 1 meter
    PATH_LOSS_EXPONENT = 2.0  # 2.0 = free space, 2.5-4.0 = indoor

    def __init__(self, robot_name: str):
        self.robot_name = robot_name
        self.sightings: Dict[str, List[RobotSighting]] = {}
        self._rssi_filter_window = 5  # Rolling average window

    def rssi_to_distance(self, rssi: int) -> float:
        """
        Convert RSSI to estimated distance using log-distance path loss model.

        Distance = 10 ^ ((RSSI_at_1m - RSSI) / (10 * n))

        Where n is the path loss exponent.
        """
        if rssi >= self.RSSI_AT_1M:
            return 0.5  # Very close

        distance = 10 ** ((self.RSSI_AT_1M - rssi) / (10 * self.PATH_LOSS_EXPONENT))
        return min(distance, 20.0)  # Cap at 20m (beyond reliable range)

    def update_sighting(self, name: str, address: str, rssi: int):
        """Record a sighting of another robot."""
        import time

        if name not in self.sightings:
            self.sightings[name] = []

        distance = self.rssi_to_distance(rssi)

        sighting = RobotSighting(
            name=name,
            address=address,
            rssi=rssi,
            estimated_distance=distance,
            timestamp=time.time()
        )

        self.sightings[name].append(sighting)

        # Keep only recent sightings for filtering
        self.sightings[name] = self.sightings[name][-self._rssi_filter_window:]

    def get_filtered_distance(self, name: str) -> Optional[float]:
        """Get filtered distance estimate using rolling average."""
        if name not in self.sightings or not self.sightings[name]:
            return None

        # Average recent RSSI values
        recent = self.sightings[name]
        avg_rssi = sum(s.rssi for s in recent) / len(recent)

        return self.rssi_to_distance(int(avg_rssi))

    def get_nearby_robots(self, max_distance: float = 3.0) -> List[Tuple[str, float]]:
        """Get list of robots within specified distance."""
        nearby = []

        for name in self.sightings:
            distance = self.get_filtered_distance(name)
            if distance and distance <= max_distance:
                nearby.append((name, distance))

        # Sort by distance
        nearby.sort(key=lambda x: x[1])
        return nearby

    def calibrate(self, known_distances: Dict[str, float]):
        """
        Calibrate RSSI model using known distances.

        Args:
            known_distances: Dict mapping robot name to actual distance
        """
        # Collect RSSI samples at known distances
        samples = []

        for name, actual_distance in known_distances.items():
            if name in self.sightings and self.sightings[name]:
                avg_rssi = sum(s.rssi for s in self.sightings[name]) / len(self.sightings[name])
                samples.append((actual_distance, avg_rssi))

        if len(samples) < 2:
            print("Need at least 2 calibration points")
            return

        # Fit path loss model using least squares
        # log(d) = (RSSI_1m - RSSI) / (10 * n)
        # This is a simplified calibration - production would use more points
        d1, rssi1 = samples[0]
        d2, rssi2 = samples[1]

        if d1 > 0 and d2 > 0 and d1 != d2:
            # Solve for n given two points
            n = (rssi1 - rssi2) / (10 * (math.log10(d2) - math.log10(d1)))
            rssi_1m = rssi1 + 10 * n * math.log10(d1)

            self.PATH_LOSS_EXPONENT = abs(n)
            self.RSSI_AT_1M = int(rssi_1m)

            print(f"Calibrated: RSSI@1m={self.RSSI_AT_1M}, n={self.PATH_LOSS_EXPONENT:.2f}")


class SwarmPositioning:
    """Multi-robot relative positioning using BLE RSSI."""

    def __init__(self, fleet):
        self.fleet = fleet
        self.ranging: Dict[str, BluetoothRanging] = {}

        for robot in fleet.robots:
            self.ranging[robot.name] = BluetoothRanging(robot.name)

    async def scan_for_neighbors(self, robot, duration: float = 2.0):
        """Have one robot scan for other fleet members."""
        from r2d2.scanner import scan

        # Scan for nearby BLE devices
        devices = await scan(timeout=duration)

        # Filter for R2D2s and update ranging
        ranging = self.ranging[robot.name]
        for device in devices:
            if device.name and device.name.startswith("D2-"):
                # This is another R2D2
                rssi = device.rssi if hasattr(device, 'rssi') else -70
                ranging.update_sighting(device.name, device.address, rssi)

    async def build_distance_matrix(self) -> Dict[Tuple[str, str], float]:
        """
        Build matrix of distances between all robot pairs.

        Returns dict mapping (robot_a, robot_b) -> estimated_distance
        """
        distances = {}

        # Have each robot scan for neighbors
        for robot in self.fleet.robots:
            await self.scan_for_neighbors(robot)

            ranging = self.ranging[robot.name]
            for other_name, distance in ranging.get_nearby_robots(max_distance=10.0):
                key = tuple(sorted([robot.name, other_name]))
                if key not in distances:
                    distances[key] = distance
                else:
                    # Average both measurements
                    distances[key] = (distances[key] + distance) / 2

        return distances

    def estimate_positions_2d(
        self,
        distances: Dict[Tuple[str, str], float],
        anchor: str = None
    ) -> Dict[str, Tuple[float, float]]:
        """
        Estimate 2D positions using multidimensional scaling (MDS).

        This places robots in a coordinate system based on their
        relative distances. The absolute position/orientation is arbitrary.

        Args:
            distances: Distance matrix from build_distance_matrix()
            anchor: Optional robot to place at origin

        Returns:
            Dict mapping robot name to (x, y) position
        """
        import numpy as np
        from sklearn.manifold import MDS

        # Get list of robot names
        names = set()
        for a, b in distances.keys():
            names.add(a)
            names.add(b)
        names = sorted(list(names))

        n = len(names)
        if n < 2:
            return {names[0]: (0, 0)} if names else {}

        # Build distance matrix
        D = np.zeros((n, n))
        for i, name_i in enumerate(names):
            for j, name_j in enumerate(names):
                if i == j:
                    continue
                key = tuple(sorted([name_i, name_j]))
                D[i, j] = distances.get(key, 5.0)  # Default 5m if unknown

        # Run MDS to find 2D positions
        mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
        positions = mds.fit_transform(D)

        # Convert to dict
        result = {}
        for i, name in enumerate(names):
            result[name] = (float(positions[i, 0]), float(positions[i, 1]))

        # Translate so anchor is at origin
        if anchor and anchor in result:
            ax, ay = result[anchor]
            result = {name: (x - ax, y - ay) for name, (x, y) in result.items()}

        return result


# Example: Swarm clustering behavior
async def cluster_behavior(fleet):
    """
    Robots form clusters based on RSSI proximity.

    Robots move toward the strongest signal (closest neighbor).
    """
    positioning = SwarmPositioning(fleet)

    while True:
        for robot in fleet.robots:
            ranging = positioning.ranging[robot.name]
            await positioning.scan_for_neighbors(robot, duration=1.0)

            nearby = ranging.get_nearby_robots(max_distance=3.0)

            if nearby:
                # Move toward closest neighbor
                closest_name, closest_dist = nearby[0]
                print(f"{robot.name}: Moving toward {closest_name} ({closest_dist:.1f}m)")

                # Simple approach - move forward slowly
                # (In practice, need to determine direction somehow)
                if closest_dist > 0.5:
                    await robot.drive.roll(heading=0, speed=30, duration=0.5)
            else:
                # No neighbors - spin to scan
                await robot.drive.spin(45)

        await asyncio.sleep(1.0)


# Example: Formation keeping
async def maintain_formation(fleet, target_spacing: float = 1.0):
    """
    Robots try to maintain equal spacing from neighbors.
    """
    positioning = SwarmPositioning(fleet)

    while True:
        distances = await positioning.build_distance_matrix()

        for robot in fleet.robots:
            ranging = positioning.ranging[robot.name]
            nearby = ranging.get_nearby_robots(max_distance=5.0)

            if not nearby:
                continue

            # Calculate average distance to neighbors
            avg_distance = sum(d for _, d in nearby) / len(nearby)

            if avg_distance < target_spacing * 0.8:
                # Too close - back away
                print(f"{robot.name}: Too close ({avg_distance:.1f}m), backing up")
                await robot.drive.roll(heading=180, speed=30, duration=0.3)

            elif avg_distance > target_spacing * 1.2:
                # Too far - move closer
                print(f"{robot.name}: Too far ({avg_distance:.1f}m), approaching")
                await robot.drive.roll(heading=0, speed=30, duration=0.3)

        await asyncio.sleep(0.5)
```

#### Hardware Upgrades for Better Accuracy

**Option 1: Bluetooth 5.1 Direction Finding**

Add a Bluetooth 5.1 module with antenna array to the sensor pack for sub-meter accuracy:
- Nordic nRF52833 (~$15) supports AoA/AoD
- Requires antenna array PCB
- 0.5-1 meter accuracy achievable

**Option 2: Ultra-Wideband (UWB)**

Add UWB modules for centimeter-level accuracy:
- Decawave DWM1001 (~$20) or Qorvo DW3000
- 10-30 cm accuracy
- Works well for indoor robotics
- Same tech as Apple AirTags

```python
# Example UWB integration (if hardware added)
class UWBRanging:
    """Centimeter-accurate ranging using UWB modules."""

    def __init__(self, serial_port: str = "/dev/ttyUSB0"):
        import serial
        self.ser = serial.Serial(serial_port, 115200)

    async def get_distance(self, target_id: int) -> float:
        """Get two-way ranging distance to target UWB module."""
        # Send ranging request
        self.ser.write(f"RANGE {target_id}\n".encode())

        # Read response
        response = self.ser.readline().decode().strip()
        if response.startswith("DIST:"):
            return float(response[5:]) / 100  # cm to meters

        return None

    async def get_all_distances(self, target_ids: List[int]) -> Dict[int, float]:
        """Range to all targets."""
        distances = {}
        for tid in target_ids:
            dist = await self.get_distance(tid)
            if dist is not None:
                distances[tid] = dist
        return distances
```

#### Educational Applications

1. **Signal Propagation**: Study how RSSI varies with distance and obstacles
2. **Localization Algorithms**: Implement trilateration, MDS, particle filters
3. **Swarm Robotics**: Emergent behaviors from local distance sensing
4. **Sensor Fusion**: Combine RSSI with odometry and visual landmarks
5. **Calibration**: Learn about environmental effects on wireless signals

#### Limitations

- **RSSI accuracy**: Best at 1-4 meters, unreliable beyond 5 meters
- **No direction**: RSSI tells distance but not direction to neighbor
- **Environmental effects**: Reflections, obstacles, interference affect readings
- **R2D2 BLE version**: Older Bluetooth without direction-finding features

For classroom use, RSSI is sufficient for demonstrating concepts. For precise positioning, consider adding UWB to the sensor packs.

**Sources:**
- [Bluetooth Direction Finding](https://www.bluetooth.com/learn-about-bluetooth/feature-enhancements/direction-finding/)
- [How AoA & AoD changed Bluetooth Location Services](https://www.bluetooth.com/blog/new-aoa-aod-bluetooth-capabilities/)
- [BLE RSSI Indoor Positioning Study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8347277/)
- [RSSI vs Direction Finding Guide](https://novelbits.io/bluetooth-rtls-direction-finding-and-rssi/)
- [Location Awareness with Multiple BLE Devices](https://novelbits.io/location-awareness-ble-connections-monitoring-rssi/)

---

### Augmented Reality Maze Navigation

An interactive AR system where students overlay virtual mazes on a camera feed and navigate R2D2 through them. Based on the [CIS 521 Robot Navigation assignment](https://artificial-intelligence-class.org/r2d2_assignments/22fall/hw2/hw2.html).

#### Overview

Students place an AprilTag on the floor, which establishes a world coordinate frame. A virtual maze is projected onto the camera feed, and students click to select start/goal points. The robot then navigates through the "virtual" maze in the real world.

**Educational value:**
- Camera geometry and projection matrices
- Graph search algorithms (BFS, DFS, A*)
- Traveling Salesman Problem
- Path planning to robot commands
- Real-world algorithm deployment

#### System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Camera    │────▶│  AprilTag    │────▶│  World      │
│   Feed      │     │  Detection   │     │  Transform  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                    ┌──────────────┐            ▼
                    │    Maze      │     ┌─────────────┐
                    │  Definition  │────▶│  AR Overlay │
                    └──────────────┘     │  Rendering  │
                                         └─────────────┘
                                                │
┌─────────────┐     ┌──────────────┐            ▼
│   R2D2      │◀────│    Path      │◀────┌─────────────┐
│   Movement  │     │  Execution   │     │  User GUI   │
└─────────────┘     └──────────────┘     │  (clicks)   │
                           ▲             └─────────────┘
                           │                    │
                    ┌──────────────┐            ▼
                    │   A* / TSP   │◀────┌─────────────┐
                    │   Planner    │     │ Start/Goals │
                    └──────────────┘     └─────────────┘
```

#### Key Components

```python
# Graph representation
class MazeGraph:
    def neighbors(self, u: Vertex) -> Set[Vertex]: ...
    def build_grid_maze(self) -> None: ...

# Search algorithms
def bfs(graph, start, goal) -> Tuple[path, visited]: ...
def dfs(graph, start, goal) -> Tuple[path, visited]: ...
def astar(graph, start, goal, heuristic) -> Tuple[path, visited]: ...
def traveling_salesman(graph, start, goals) -> Tuple[path, cost]: ...

# Camera projection (3D world -> 2D image)
class CameraProjection:
    def world_to_image(self, points_3d) -> points_2d: ...

# Path to robot commands
def path_to_moves(path, cell_size) -> List[(heading, distance)]: ...
```

#### Hardware Setup

| Component | Purpose |
|-----------|---------|
| AprilTag (5cm) | World coordinate frame reference |
| USB webcam | Camera feed for AR overlay |
| R2D2 | Executes navigation commands |

#### Educational Extensions

| Extension | Learning Outcome |
|-----------|------------------|
| Algorithm comparison | Visualize BFS vs DFS vs A* efficiency |
| Heuristic design | A* admissibility and optimality |
| Dynamic obstacles | Real-time replanning |
| Multi-robot maze | Fleet coordination |
| Procedural mazes | Graph generation algorithms |

---

### LLM-Based Voice/Text Command Interface

Natural language control of R2D2 using modern LLMs. Updated from the [CIS 521 Intent Detection assignment](https://artificial-intelligence-class.org/r2d2_assignments/22fall/hw5/hw5.html) with modern approaches.

#### Overview

The original assignment used RNNs, Word2Vec, and BERT for intent classification. Modern LLMs enable more powerful and flexible command understanding:

| Original (2022) | Modern (2025+) |
|-----------------|----------------|
| Fixed 9 intents | Open-ended commands |
| Custom training data | Zero/few-shot |
| LSTM/BERT classification | GPT-4/Claude/Llama |
| Text only | Voice + text |
| Single command | Multi-step reasoning |

#### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Voice     │────▶│   Whisper    │────▶│   Text      │
│   Input     │     │   STT        │     │   Command   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   R2D2      │◀────│   Command    │◀────│   LLM       │
│   Execution │     │   Parser     │     │   (tools)   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │   Context   │
                                         │   Memory    │
                                         └─────────────┘
```

#### Implementation

```python
import openai
from dataclasses import dataclass
from typing import Optional, List
import json

# Define robot capabilities as tools
ROBOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "drive",
            "description": "Move the robot in a direction",
            "parameters": {
                "type": "object",
                "properties": {
                    "heading": {
                        "type": "integer",
                        "description": "Direction in degrees (0=forward, 90=right, 180=back, 270=left)"
                    },
                    "speed": {
                        "type": "integer",
                        "description": "Speed from 0-255"
                    },
                    "duration": {
                        "type": "number",
                        "description": "How long to move in seconds"
                    }
                },
                "required": ["heading", "speed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_led_color",
            "description": "Set the robot's LED color",
            "parameters": {
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string",
                        "enum": ["red", "green", "blue", "white", "off", "purple", "yellow", "cyan"]
                    },
                    "location": {
                        "type": "string",
                        "enum": ["front", "back", "all"]
                    }
                },
                "required": ["color"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_dome",
            "description": "Rotate R2D2's head/dome",
            "parameters": {
                "type": "object",
                "properties": {
                    "angle": {
                        "type": "integer",
                        "description": "Angle in degrees (-160 to 180, 0 is center)"
                    }
                },
                "required": ["angle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_sound",
            "description": "Play a sound or make R2D2 express an emotion",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string",
                        "enum": ["happy", "sad", "excited", "scared", "alarm", "chatty"]
                    }
                },
                "required": ["emotion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_stance",
            "description": "Change R2D2's leg position",
            "parameters": {
                "type": "object",
                "properties": {
                    "stance": {
                        "type": "string",
                        "enum": ["tripod", "bipod", "waddle"]
                    }
                },
                "required": ["stance"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_status",
            "description": "Get robot status information",
            "parameters": {
                "type": "object",
                "properties": {
                    "info": {
                        "type": "string",
                        "enum": ["battery", "position", "connection", "all"]
                    }
                },
                "required": ["info"]
            }
        }
    },
]

SYSTEM_PROMPT = """You are an AI assistant controlling an R2-D2 robot from Star Wars.
You can execute commands on the robot using the provided tools.

Guidelines:
- Be playful and in-character as R2D2's helper
- For ambiguous commands, ask for clarification
- Chain multiple actions for complex requests
- Report status after actions when appropriate
- If a command seems dangerous or impossible, explain why

The robot can: drive, change LED colors, rotate its dome/head, play sounds,
change stance (tripod/bipod), and report status.

Current robot state:
- Battery: {battery_pct}%
- Stance: {stance}
- Connected: {connected}
"""


class R2D2VoiceController:
    """
    LLM-powered voice/text control for R2D2.
    """

    def __init__(self, robot, model: str = "gpt-4"):
        self.robot = robot
        self.model = model
        self.client = openai.OpenAI()
        self.conversation_history = []

    async def get_robot_state(self) -> dict:
        """Get current robot state for context."""
        try:
            battery = await self.robot.get_battery_percentage()
            connected = self.robot.is_connected
            # stance would need to be tracked
            return {
                "battery_pct": battery,
                "stance": "bipod",
                "connected": connected,
            }
        except:
            return {"battery_pct": "unknown", "stance": "unknown", "connected": False}

    async def execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool call on the robot."""
        try:
            if tool_name == "drive":
                heading = args.get("heading", 0)
                speed = args.get("speed", 50)
                duration = args.get("duration", 1.0)
                await self.robot.drive.roll(heading=heading, speed=speed, duration=duration)
                return f"Moved at heading {heading}° for {duration}s"

            elif tool_name == "set_led_color":
                color = args.get("color", "white")
                location = args.get("location", "front")

                color_map = {
                    "red": (255, 0, 0),
                    "green": (0, 255, 0),
                    "blue": (0, 0, 255),
                    "white": (255, 255, 255),
                    "purple": (128, 0, 255),
                    "yellow": (255, 255, 0),
                    "cyan": (0, 255, 255),
                    "off": (0, 0, 0),
                }
                rgb = color_map.get(color, (255, 255, 255))

                if location in ("front", "all"):
                    await self.robot.leds.set_front(*rgb)
                if location in ("back", "all"):
                    await self.robot.leds.set_back(*rgb)

                return f"Set {location} LED to {color}"

            elif tool_name == "move_dome":
                angle = args.get("angle", 0)
                await self.robot.dome.set_position(angle)
                return f"Moved dome to {angle}°"

            elif tool_name == "play_sound":
                emotion = args.get("emotion", "happy")
                sound_map = {
                    "happy": self.robot.audio.happy,
                    "sad": self.robot.audio.sad,
                    "excited": self.robot.audio.excited,
                    "scared": self.robot.audio.scream,
                    "alarm": self.robot.audio.alarm,
                    "chatty": lambda: self.robot.audio.play_sound(1862),
                }
                await sound_map.get(emotion, self.robot.audio.happy)()
                return f"Played {emotion} sound"

            elif tool_name == "set_stance":
                stance = args.get("stance", "bipod")
                if stance == "tripod":
                    await self.robot.stance.set_tripod()
                elif stance == "waddle":
                    await self.robot.stance.waddle()
                else:
                    await self.robot.stance.set_bipod()
                return f"Changed to {stance} stance"

            elif tool_name == "get_status":
                info = args.get("info", "all")
                state = await self.get_robot_state()

                if info == "battery":
                    return f"Battery: {state['battery_pct']}%"
                elif info == "connection":
                    return f"Connected: {state['connected']}"
                else:
                    return f"Status: Battery {state['battery_pct']}%, Connected: {state['connected']}"

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    async def process_command(self, user_input: str) -> str:
        """
        Process a natural language command.

        Args:
            user_input: Text command from user

        Returns:
            Response text
        """
        # Get current state for context
        state = await self.get_robot_state()
        system_prompt = SYSTEM_PROMPT.format(**state)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_input})

        # Call LLM with tools
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=ROBOT_TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # Process tool calls
        if assistant_message.tool_calls:
            # Execute each tool
            tool_results = []
            for tool_call in assistant_message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = await self.execute_tool(tool_call.function.name, args)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": result,
                })

            # Get final response with tool results
            messages.append(assistant_message)
            messages.extend(tool_results)

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            response_text = final_response.choices[0].message.content
        else:
            response_text = assistant_message.content

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response_text})

        # Trim history to last 10 exchanges
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return response_text


# Voice input using Whisper
class VoiceInput:
    """Voice-to-text using OpenAI Whisper."""

    def __init__(self):
        self.client = openai.OpenAI()

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        with open(audio_path, "rb") as f:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )
        return transcript.text

    def record_and_transcribe(self, duration_sec: float = 5.0) -> str:
        """Record from microphone and transcribe."""
        import sounddevice as sd
        import scipy.io.wavfile as wav
        import tempfile

        # Record audio
        sample_rate = 16000
        audio = sd.rec(
            int(duration_sec * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='int16'
        )
        sd.wait()

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav.write(f.name, sample_rate, audio)
            return self.transcribe_file(f.name)


# Local LLM option using Ollama
class LocalLLMController:
    """
    Use local LLMs via Ollama for low-latency, offline operation.

    Requires: ollama pull llama3.2
    """

    def __init__(self, robot, model: str = "llama3.2"):
        self.robot = robot
        self.model = model
        self.base_url = "http://localhost:11434"

    async def process_command(self, user_input: str) -> str:
        """Process command using local Ollama model."""
        import httpx

        # Simpler prompt format for local models
        prompt = f"""You control an R2-D2 robot. Parse this command and respond with JSON.

Command: {user_input}

Respond with JSON in this format:
{{"action": "drive|led|dome|sound|stance|status|unknown", "params": {{...}}, "response": "what to say"}}

Examples:
- "go forward" -> {{"action": "drive", "params": {{"heading": 0, "speed": 50}}, "response": "Moving forward!"}}
- "turn red" -> {{"action": "led", "params": {{"color": "red"}}, "response": "Lighting up red!"}}
- "look left" -> {{"action": "dome", "params": {{"angle": -90}}, "response": "Looking left!"}}

JSON response:"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=30.0,
            )
            result = response.json()
            text = result.get("response", "")

            # Parse JSON from response
            try:
                # Find JSON in response
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    cmd = json.loads(json_match.group())
                    await self._execute_parsed_command(cmd)
                    return cmd.get("response", "Done!")
            except:
                pass

            return "I didn't understand that command."

    async def _execute_parsed_command(self, cmd: dict):
        """Execute parsed command."""
        action = cmd.get("action")
        params = cmd.get("params", {})

        if action == "drive":
            await self.robot.drive.roll(
                heading=params.get("heading", 0),
                speed=params.get("speed", 50),
                duration=params.get("duration", 1.0)
            )
        elif action == "led":
            color = params.get("color", "white")
            # ... color mapping and execution
        elif action == "dome":
            await self.robot.dome.set_position(params.get("angle", 0))
        elif action == "sound":
            await self.robot.audio.happy()
        elif action == "stance":
            stance = params.get("stance", "bipod")
            if stance == "tripod":
                await self.robot.stance.set_tripod()


# Example: Interactive voice control
async def voice_control_demo(robot):
    """Run interactive voice control session."""
    controller = R2D2VoiceController(robot, model="gpt-4")
    voice = VoiceInput()

    print("R2D2 Voice Control")
    print("Say 'quit' to exit, or press Enter to record a command")

    while True:
        input("Press Enter to speak...")
        print("Listening...")

        # Record and transcribe
        text = voice.record_and_transcribe(duration_sec=5.0)
        print(f"You said: {text}")

        if "quit" in text.lower():
            break

        # Process command
        response = await controller.process_command(text)
        print(f"R2D2: {response}")


# Example: Text chat interface
async def chat_control_demo(robot):
    """Run text chat control session."""
    controller = R2D2VoiceController(robot, model="gpt-4")

    print("R2D2 Chat Control (type 'quit' to exit)")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == 'quit':
            break

        response = await controller.process_command(user_input)
        print(f"R2D2: {response}")
```

#### Model Options

| Model | Latency | Cost | Offline | Best For |
|-------|---------|------|---------|----------|
| **GPT-4** | ~2s | $$$ | No | Best understanding |
| **GPT-3.5** | ~1s | $ | No | Good balance |
| **Claude 3** | ~1.5s | $$ | No | Nuanced commands |
| **Llama 3.2** | ~0.5s | Free | Yes | Low latency, privacy |
| **Mistral** | ~0.5s | Free | Yes | Good local option |

#### Educational Value

| Concept | Learning Outcome |
|---------|------------------|
| Tool/Function calling | How LLMs interact with external systems |
| Prompt engineering | System prompts, few-shot examples |
| Conversation context | Managing multi-turn dialogues |
| Speech-to-text | Whisper API, audio processing |
| Local vs cloud LLMs | Latency, privacy, cost tradeoffs |
| Structured output | JSON parsing, command validation |

#### Assignment Ideas

1. **Basic Commands**: Implement 5 robot tools, process simple commands
2. **Multi-Step**: Handle "do a happy dance" (stance + movement + sound)
3. **Context Memory**: Remember user preferences across session
4. **Local LLM**: Run entirely offline with Ollama
5. **Voice Control**: Add Whisper STT for hands-free operation
6. **Safety Layer**: Add command validation and confirmation for dangerous actions

#### Comparison: Old vs New Approach

| Aspect | LSTM/BERT (2022) | LLM Tools (2025) |
|--------|------------------|------------------|
| Training data | 80+ manual examples | Zero-shot |
| New commands | Requires retraining | Just describe in prompt |
| Ambiguity | Fails silently | Asks for clarification |
| Multi-step | Not supported | Natural chaining |
| Context | None | Conversation memory |
| Explanation | Classification only | Can explain actions |

---

### ROS-Inspired Architecture Features

The [Robot Operating System (ROS)](https://www.ros.org/) provides many patterns and concepts that could enhance the R2D2 library for educational robotics. These features are inspired by ROS but adapted for our simpler Python-based architecture.

#### 1. Message/Topic System (Pub/Sub)

ROS uses a publish/subscribe pattern for inter-component communication. We can implement a lightweight version for R2D2 fleet coordination.

```python
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

@dataclass
class Message:
    """Base message with timestamp and source."""
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""

@dataclass
class SensorMessage(Message):
    """Sensor data message."""
    accelerometer: tuple = (0.0, 0.0, 0.0)
    gyroscope: tuple = (0.0, 0.0, 0.0)
    dome_position: float = 0.0

@dataclass
class PoseMessage(Message):
    """Robot pose message (like geometry_msgs/Pose)."""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0  # heading in radians
    frame_id: str = "map"

@dataclass
class TwistMessage(Message):
    """Velocity command (like geometry_msgs/Twist)."""
    linear_x: float = 0.0  # forward velocity
    angular_z: float = 0.0  # rotation velocity

@dataclass
class BatteryMessage(Message):
    """Battery status (like sensor_msgs/BatteryState)."""
    voltage: float = 0.0
    percentage: int = 0
    charging: bool = False


class MessageBus:
    """
    Lightweight pub/sub message bus for R2D2 fleet.

    Inspired by ROS topics but simplified for Python async.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._latest: Dict[str, Message] = {}
        self._history: Dict[str, List[Message]] = {}
        self._history_size = 100

    def subscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Topic name (e.g., "/fleet/D2-55E3/sensors")
            callback: Function to call when message received
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable) -> None:
        """Unsubscribe from a topic."""
        if topic in self._subscribers:
            self._subscribers[topic].remove(callback)

    async def publish(self, topic: str, message: Message) -> None:
        """
        Publish a message to a topic.

        Args:
            topic: Topic name
            message: Message to publish
        """
        self._latest[topic] = message

        # Add to history
        if topic not in self._history:
            self._history[topic] = []
        self._history[topic].append(message)
        if len(self._history[topic]) > self._history_size:
            self._history[topic].pop(0)

        # Notify subscribers
        for callback in self._subscribers.get(topic, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                print(f"Subscriber error on {topic}: {e}")

    def get_latest(self, topic: str) -> Message | None:
        """Get most recent message on topic."""
        return self._latest.get(topic)

    def get_history(self, topic: str, count: int = 10) -> List[Message]:
        """Get recent message history."""
        return self._history.get(topic, [])[-count:]

    def list_topics(self) -> List[str]:
        """List all active topics."""
        return list(self._latest.keys())


# Global message bus for fleet
message_bus = MessageBus()


# Example usage
async def sensor_publisher(robot):
    """Publish sensor data to message bus."""
    while robot.is_connected:
        # Read sensors
        data = await robot.sensors.get_data()

        msg = SensorMessage(
            source=robot.name,
            accelerometer=data.accelerometer,
            gyroscope=data.gyroscope,
            dome_position=data.dome_position,
        )

        await message_bus.publish(f"/fleet/{robot.name}/sensors", msg)
        await asyncio.sleep(0.1)


async def pose_subscriber_example():
    """Subscribe to all robot poses."""
    def on_pose(msg: PoseMessage):
        print(f"{msg.source} at ({msg.x:.2f}, {msg.y:.2f})")

    # Subscribe to all robots
    for robot_name in ["D2-55E3", "D2-1234", "D2-ABCD"]:
        message_bus.subscribe(f"/fleet/{robot_name}/pose", on_pose)
```

#### 2. Transform (TF) System

ROS TF maintains relationships between coordinate frames. Essential for SLAM and multi-robot coordination.

```python
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import math
import time

@dataclass
class Transform:
    """Transform between two coordinate frames."""
    parent_frame: str
    child_frame: str
    x: float  # translation
    y: float
    theta: float  # rotation (radians)
    timestamp: float = 0.0

    def apply(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """Transform a point from child to parent frame."""
        px, py = point
        # Rotate
        cos_t = math.cos(self.theta)
        sin_t = math.sin(self.theta)
        rx = px * cos_t - py * sin_t
        ry = px * sin_t + py * cos_t
        # Translate
        return (rx + self.x, ry + self.y)

    def inverse(self) -> 'Transform':
        """Get inverse transform (parent -> child)."""
        cos_t = math.cos(-self.theta)
        sin_t = math.sin(-self.theta)
        inv_x = -self.x * cos_t + self.y * sin_t
        inv_y = -self.x * sin_t - self.y * cos_t
        return Transform(
            parent_frame=self.child_frame,
            child_frame=self.parent_frame,
            x=inv_x,
            y=inv_y,
            theta=-self.theta,
            timestamp=self.timestamp,
        )


class TransformTree:
    """
    Maintain coordinate frame relationships.

    Inspired by ROS TF2, simplified for 2D mobile robots.

    Standard frames (following REP-105):
    - map: Global fixed frame (origin = room corner)
    - odom: Odometry frame (origin = robot start position)
    - base_link: Robot body frame (origin = robot center)
    - dome: Dome/head frame
    - sensor: Sensor pack frame (if attached)
    """

    def __init__(self):
        self._transforms: Dict[Tuple[str, str], Transform] = {}
        self._transform_timeout = 1.0  # seconds

    def set_transform(self, transform: Transform) -> None:
        """Add or update a transform."""
        transform.timestamp = time.time()
        key = (transform.parent_frame, transform.child_frame)
        self._transforms[key] = transform

    def get_transform(
        self,
        target_frame: str,
        source_frame: str,
    ) -> Optional[Transform]:
        """
        Get transform from source_frame to target_frame.

        Args:
            target_frame: Frame to transform into
            source_frame: Frame to transform from

        Returns:
            Transform or None if not found
        """
        # Direct transform?
        key = (target_frame, source_frame)
        if key in self._transforms:
            return self._transforms[key]

        # Inverse?
        inv_key = (source_frame, target_frame)
        if inv_key in self._transforms:
            return self._transforms[inv_key].inverse()

        # Chain through common parent (simplified)
        # Full implementation would use graph search
        return None

    def transform_point(
        self,
        point: Tuple[float, float],
        target_frame: str,
        source_frame: str,
    ) -> Optional[Tuple[float, float]]:
        """Transform a point between frames."""
        tf = self.get_transform(target_frame, source_frame)
        if tf:
            return tf.apply(point)
        return None

    def can_transform(self, target_frame: str, source_frame: str) -> bool:
        """Check if transform is available."""
        return self.get_transform(target_frame, source_frame) is not None


class RobotStatePublisher:
    """
    Publish transforms for a robot.

    Inspired by robot_state_publisher in ROS.
    """

    def __init__(self, robot, tf_tree: TransformTree):
        self.robot = robot
        self.tf = tf_tree
        self._running = False

    async def start(self):
        """Start publishing transforms."""
        self._running = True

        while self._running:
            # Publish base_link -> dome transform
            dome_pos = await self.robot.dome.get_position()
            self.tf.set_transform(Transform(
                parent_frame=f"{self.robot.name}/base_link",
                child_frame=f"{self.robot.name}/dome",
                x=0.0,
                y=0.0,
                theta=math.radians(dome_pos),
            ))

            # odom -> base_link would come from odometry
            # map -> odom would come from SLAM

            await asyncio.sleep(0.1)

    def stop(self):
        """Stop publishing."""
        self._running = False


# Example: Multi-robot TF tree
tf_tree = TransformTree()

# Set up world -> robot transforms
tf_tree.set_transform(Transform("map", "D2-55E3/odom", 0, 0, 0))
tf_tree.set_transform(Transform("map", "D2-1234/odom", 2.0, 0, 0))

# Transform point from one robot's frame to another
point_in_r1 = (0.5, 0.3)  # Point in D2-55E3 frame
# Would need chain: D2-55E3/base_link -> D2-55E3/odom -> map -> D2-1234/odom -> D2-1234/base_link
```

#### 3. Bag Recording and Playback

ROS bags enable recording and replaying robot data. Essential for debugging, testing, and demonstrations.

```python
import json
import gzip
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Iterator
from dataclasses import dataclass, asdict
import asyncio

@dataclass
class BagEntry:
    """Single entry in a bag file."""
    timestamp: float
    topic: str
    message_type: str
    data: Dict[str, Any]


class R2D2Bag:
    """
    Record and playback R2D2 session data.

    Inspired by rosbag but simplified for R2D2.

    File format: gzipped JSON lines
    """

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self._entries: List[BagEntry] = []
        self._recording = False
        self._start_time = 0.0

    # Recording

    def start_recording(self) -> None:
        """Start recording session."""
        self._recording = True
        self._start_time = time.time()
        self._entries = []
        print(f"Recording started: {self.filepath}")

    def stop_recording(self) -> None:
        """Stop recording and save to file."""
        self._recording = False
        self._save()
        print(f"Recording stopped: {len(self._entries)} entries saved")

    def record(self, topic: str, message_type: str, data: Dict[str, Any]) -> None:
        """Record a message."""
        if not self._recording:
            return

        entry = BagEntry(
            timestamp=time.time() - self._start_time,
            topic=topic,
            message_type=message_type,
            data=data,
        )
        self._entries.append(entry)

    async def record_robot(self, robot, topics: List[str] = None) -> None:
        """
        Automatically record robot data.

        Args:
            robot: R2D2 instance
            topics: Topics to record (None = all)
        """
        default_topics = ["sensors", "battery", "pose", "commands"]
        topics = topics or default_topics

        while self._recording:
            if "sensors" in topics:
                try:
                    data = await robot.sensors.get_data()
                    self.record(
                        f"/{robot.name}/sensors",
                        "SensorMessage",
                        asdict(data) if hasattr(data, '__dataclass_fields__') else {"raw": str(data)}
                    )
                except:
                    pass

            if "battery" in topics:
                try:
                    voltage = await robot.get_battery_voltage()
                    percentage = await robot.get_battery_percentage()
                    self.record(
                        f"/{robot.name}/battery",
                        "BatteryMessage",
                        {"voltage": voltage, "percentage": percentage}
                    )
                except:
                    pass

            await asyncio.sleep(0.1)

    def _save(self) -> None:
        """Save entries to file."""
        with gzip.open(self.filepath, 'wt') as f:
            for entry in self._entries:
                f.write(json.dumps(asdict(entry)) + '\n')

    # Playback

    def load(self) -> None:
        """Load bag file."""
        self._entries = []
        with gzip.open(self.filepath, 'rt') as f:
            for line in f:
                data = json.loads(line)
                self._entries.append(BagEntry(**data))
        print(f"Loaded {len(self._entries)} entries")

    def play(self, speed: float = 1.0) -> Iterator[BagEntry]:
        """
        Play back entries with timing.

        Args:
            speed: Playback speed multiplier (1.0 = realtime)

        Yields:
            BagEntry at appropriate times
        """
        if not self._entries:
            return

        start_time = time.time()

        for entry in self._entries:
            # Wait until appropriate time
            target_time = start_time + (entry.timestamp / speed)
            wait_time = target_time - time.time()
            if wait_time > 0:
                time.sleep(wait_time)

            yield entry

    async def play_async(self, speed: float = 1.0) -> Iterator[BagEntry]:
        """Async playback."""
        if not self._entries:
            return

        start_time = time.time()

        for entry in self._entries:
            target_time = start_time + (entry.timestamp / speed)
            wait_time = target_time - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            yield entry

    # Analysis

    def get_topics(self) -> List[str]:
        """Get all topics in bag."""
        return list(set(e.topic for e in self._entries))

    def get_duration(self) -> float:
        """Get bag duration in seconds."""
        if not self._entries:
            return 0.0
        return self._entries[-1].timestamp - self._entries[0].timestamp

    def filter(self, topic: str = None, message_type: str = None) -> List[BagEntry]:
        """Filter entries by topic or message type."""
        result = self._entries
        if topic:
            result = [e for e in result if e.topic == topic]
        if message_type:
            result = [e for e in result if e.message_type == message_type]
        return result

    def info(self) -> Dict[str, Any]:
        """Get bag information."""
        topics = {}
        for entry in self._entries:
            if entry.topic not in topics:
                topics[entry.topic] = {"count": 0, "types": set()}
            topics[entry.topic]["count"] += 1
            topics[entry.topic]["types"].add(entry.message_type)

        return {
            "filepath": str(self.filepath),
            "duration_sec": self.get_duration(),
            "entry_count": len(self._entries),
            "topics": {t: {"count": d["count"], "types": list(d["types"])}
                       for t, d in topics.items()},
        }


# Example usage
async def record_session(robot, duration_sec: float = 60):
    """Record a robot session."""
    bag = R2D2Bag(f"recordings/{robot.name}_{datetime.now():%Y%m%d_%H%M%S}.bag")

    bag.start_recording()

    # Start recording task
    record_task = asyncio.create_task(bag.record_robot(robot))

    # Do some actions
    await robot.leds.red()
    bag.record(f"/{robot.name}/commands", "LEDCommand", {"color": "red"})

    await robot.dome.set_position(90)
    bag.record(f"/{robot.name}/commands", "DomeCommand", {"position": 90})

    await asyncio.sleep(duration_sec)

    bag.stop_recording()
    record_task.cancel()

    # Print info
    print(json.dumps(bag.info(), indent=2))


def replay_session(bag_path: str):
    """Replay a recorded session."""
    bag = R2D2Bag(bag_path)
    bag.load()

    print(f"Replaying {bag.get_duration():.1f}s session...")

    for entry in bag.play(speed=2.0):  # 2x speed
        print(f"[{entry.timestamp:.2f}s] {entry.topic}: {entry.message_type}")
```

#### 4. Behavior Trees

ROS Nav2 uses behavior trees for complex autonomous behaviors. Great for teaching decision-making and task sequencing.

```python
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, Any, List, Optional
import asyncio

class NodeStatus(Enum):
    """Behavior tree node status."""
    SUCCESS = auto()
    FAILURE = auto()
    RUNNING = auto()


class BTNode(ABC):
    """Base behavior tree node."""

    def __init__(self, name: str):
        self.name = name
        self.status = NodeStatus.RUNNING

    @abstractmethod
    async def tick(self, blackboard: Dict[str, Any]) -> NodeStatus:
        """Execute one tick of the node."""
        pass

    def reset(self):
        """Reset node state."""
        self.status = NodeStatus.RUNNING


class ActionNode(BTNode):
    """Leaf node that performs an action."""

    def __init__(self, name: str, action_func):
        super().__init__(name)
        self.action_func = action_func

    async def tick(self, blackboard: Dict[str, Any]) -> NodeStatus:
        try:
            result = await self.action_func(blackboard)
            self.status = NodeStatus.SUCCESS if result else NodeStatus.FAILURE
        except Exception as e:
            print(f"Action {self.name} failed: {e}")
            self.status = NodeStatus.FAILURE
        return self.status


class ConditionNode(BTNode):
    """Leaf node that checks a condition."""

    def __init__(self, name: str, condition_func):
        super().__init__(name)
        self.condition_func = condition_func

    async def tick(self, blackboard: Dict[str, Any]) -> NodeStatus:
        if self.condition_func(blackboard):
            self.status = NodeStatus.SUCCESS
        else:
            self.status = NodeStatus.FAILURE
        return self.status


class SequenceNode(BTNode):
    """Execute children in order until one fails."""

    def __init__(self, name: str, children: List[BTNode]):
        super().__init__(name)
        self.children = children
        self._current_child = 0

    async def tick(self, blackboard: Dict[str, Any]) -> NodeStatus:
        while self._current_child < len(self.children):
            child = self.children[self._current_child]
            status = await child.tick(blackboard)

            if status == NodeStatus.RUNNING:
                self.status = NodeStatus.RUNNING
                return self.status
            elif status == NodeStatus.FAILURE:
                self.status = NodeStatus.FAILURE
                self._current_child = 0
                return self.status
            else:
                self._current_child += 1

        self.status = NodeStatus.SUCCESS
        self._current_child = 0
        return self.status

    def reset(self):
        super().reset()
        self._current_child = 0
        for child in self.children:
            child.reset()


class SelectorNode(BTNode):
    """Try children until one succeeds (fallback)."""

    def __init__(self, name: str, children: List[BTNode]):
        super().__init__(name)
        self.children = children
        self._current_child = 0

    async def tick(self, blackboard: Dict[str, Any]) -> NodeStatus:
        while self._current_child < len(self.children):
            child = self.children[self._current_child]
            status = await child.tick(blackboard)

            if status == NodeStatus.RUNNING:
                self.status = NodeStatus.RUNNING
                return self.status
            elif status == NodeStatus.SUCCESS:
                self.status = NodeStatus.SUCCESS
                self._current_child = 0
                return self.status
            else:
                self._current_child += 1

        self.status = NodeStatus.FAILURE
        self._current_child = 0
        return self.status

    def reset(self):
        super().reset()
        self._current_child = 0
        for child in self.children:
            child.reset()


class ParallelNode(BTNode):
    """Execute all children simultaneously."""

    def __init__(self, name: str, children: List[BTNode], success_threshold: int = None):
        super().__init__(name)
        self.children = children
        self.success_threshold = success_threshold or len(children)

    async def tick(self, blackboard: Dict[str, Any]) -> NodeStatus:
        results = await asyncio.gather(*[c.tick(blackboard) for c in self.children])

        successes = sum(1 for r in results if r == NodeStatus.SUCCESS)
        failures = sum(1 for r in results if r == NodeStatus.FAILURE)

        if successes >= self.success_threshold:
            self.status = NodeStatus.SUCCESS
        elif failures > len(self.children) - self.success_threshold:
            self.status = NodeStatus.FAILURE
        else:
            self.status = NodeStatus.RUNNING

        return self.status


class RepeatNode(BTNode):
    """Repeat child N times or until failure."""

    def __init__(self, name: str, child: BTNode, count: int = -1):
        super().__init__(name)
        self.child = child
        self.count = count  # -1 = infinite
        self._iterations = 0

    async def tick(self, blackboard: Dict[str, Any]) -> NodeStatus:
        status = await self.child.tick(blackboard)

        if status == NodeStatus.SUCCESS:
            self._iterations += 1
            self.child.reset()

            if self.count > 0 and self._iterations >= self.count:
                self.status = NodeStatus.SUCCESS
                self._iterations = 0
            else:
                self.status = NodeStatus.RUNNING
        elif status == NodeStatus.FAILURE:
            self.status = NodeStatus.FAILURE
            self._iterations = 0
        else:
            self.status = NodeStatus.RUNNING

        return self.status


class BehaviorTree:
    """
    Behavior tree executor.

    Inspired by BehaviorTree.CPP and Nav2's BT system.
    """

    def __init__(self, root: BTNode):
        self.root = root
        self.blackboard: Dict[str, Any] = {}

    async def tick(self) -> NodeStatus:
        """Execute one tick of the tree."""
        return await self.root.tick(self.blackboard)

    async def run(self, tick_rate_hz: float = 10.0) -> NodeStatus:
        """Run tree until completion."""
        tick_interval = 1.0 / tick_rate_hz

        while True:
            status = await self.tick()

            if status != NodeStatus.RUNNING:
                return status

            await asyncio.sleep(tick_interval)

    def reset(self):
        """Reset tree state."""
        self.root.reset()


# Example: Patrol behavior tree
def create_patrol_tree(robot, waypoints: List[tuple]) -> BehaviorTree:
    """Create a patrol behavior tree."""

    async def go_to_waypoint(bb):
        """Navigate to current waypoint."""
        wp = waypoints[bb.get("waypoint_index", 0)]
        # Simplified - real impl would use navigator
        await robot.drive.roll(heading=0, speed=50, duration=2.0)
        return True

    async def play_arrival_sound(bb):
        """Play sound when arriving at waypoint."""
        await robot.audio.happy()
        return True

    async def advance_waypoint(bb):
        """Move to next waypoint."""
        idx = bb.get("waypoint_index", 0)
        bb["waypoint_index"] = (idx + 1) % len(waypoints)
        return True

    def check_battery_ok(bb):
        """Check if battery is sufficient."""
        return bb.get("battery_percentage", 100) > 20

    # Build tree
    patrol_sequence = SequenceNode("patrol_sequence", [
        ConditionNode("check_battery", check_battery_ok),
        ActionNode("go_to_waypoint", go_to_waypoint),
        ActionNode("announce_arrival", play_arrival_sound),
        ActionNode("advance_waypoint", advance_waypoint),
    ])

    root = RepeatNode("patrol_loop", patrol_sequence, count=-1)

    return BehaviorTree(root)


# Example: Run patrol
async def run_patrol(robot):
    waypoints = [(0, 0), (1, 0), (1, 1), (0, 1)]
    tree = create_patrol_tree(robot, waypoints)

    # Update blackboard with robot state
    tree.blackboard["battery_percentage"] = await robot.get_battery_percentage()

    await tree.run()
```

#### 5. Diagnostics System

ROS diagnostics provides health monitoring. Essential for managing a fleet of 200 robots.

```python
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Callable, Any
from datetime import datetime
import asyncio

class DiagnosticLevel(Enum):
    """Diagnostic severity levels."""
    OK = auto()
    WARN = auto()
    ERROR = auto()
    STALE = auto()


@dataclass
class DiagnosticStatus:
    """Status of a single diagnostic."""
    name: str
    level: DiagnosticLevel
    message: str
    values: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DiagnosticReport:
    """Complete diagnostic report for a robot."""
    robot_name: str
    timestamp: datetime
    statuses: List[DiagnosticStatus]

    @property
    def overall_level(self) -> DiagnosticLevel:
        """Get worst diagnostic level."""
        if any(s.level == DiagnosticLevel.ERROR for s in self.statuses):
            return DiagnosticLevel.ERROR
        if any(s.level == DiagnosticLevel.WARN for s in self.statuses):
            return DiagnosticLevel.WARN
        if any(s.level == DiagnosticLevel.STALE for s in self.statuses):
            return DiagnosticLevel.STALE
        return DiagnosticLevel.OK


class DiagnosticUpdater:
    """
    Collect and report robot diagnostics.

    Inspired by diagnostic_updater in ROS.
    """

    def __init__(self, robot):
        self.robot = robot
        self._checks: List[Callable] = []
        self._last_report: DiagnosticReport = None

    def add_check(self, check_func: Callable[[], DiagnosticStatus]) -> None:
        """Add a diagnostic check function."""
        self._checks.append(check_func)

    async def update(self) -> DiagnosticReport:
        """Run all checks and generate report."""
        statuses = []

        for check in self._checks:
            try:
                if asyncio.iscoroutinefunction(check):
                    status = await check()
                else:
                    status = check()
                statuses.append(status)
            except Exception as e:
                statuses.append(DiagnosticStatus(
                    name=check.__name__,
                    level=DiagnosticLevel.ERROR,
                    message=f"Check failed: {e}",
                ))

        self._last_report = DiagnosticReport(
            robot_name=self.robot.name,
            timestamp=datetime.now(),
            statuses=statuses,
        )

        return self._last_report

    def get_last_report(self) -> DiagnosticReport:
        """Get most recent report."""
        return self._last_report


def create_standard_diagnostics(robot) -> DiagnosticUpdater:
    """Create diagnostics with standard checks."""
    updater = DiagnosticUpdater(robot)

    async def check_battery():
        voltage = await robot.get_battery_voltage()
        percentage = await robot.get_battery_percentage()

        if percentage < 10:
            level = DiagnosticLevel.ERROR
            msg = "Battery critical!"
        elif percentage < 25:
            level = DiagnosticLevel.WARN
            msg = "Battery low"
        else:
            level = DiagnosticLevel.OK
            msg = "Battery OK"

        return DiagnosticStatus(
            name="battery",
            level=level,
            message=msg,
            values={"voltage": voltage, "percentage": percentage},
        )

    async def check_connection():
        if robot.is_connected:
            return DiagnosticStatus(
                name="connection",
                level=DiagnosticLevel.OK,
                message="Connected",
                values={"address": robot.address},
            )
        else:
            return DiagnosticStatus(
                name="connection",
                level=DiagnosticLevel.ERROR,
                message="Disconnected",
            )

    async def check_motors():
        # Would check motor response
        return DiagnosticStatus(
            name="motors",
            level=DiagnosticLevel.OK,
            message="Motors responding",
        )

    updater.add_check(check_battery)
    updater.add_check(check_connection)
    updater.add_check(check_motors)

    return updater


class DiagnosticAggregator:
    """
    Aggregate diagnostics from multiple robots.

    Inspired by diagnostic_aggregator in ROS.
    """

    def __init__(self):
        self._updaters: Dict[str, DiagnosticUpdater] = {}
        self._reports: Dict[str, DiagnosticReport] = {}

    def add_robot(self, robot) -> None:
        """Add robot to aggregator."""
        updater = create_standard_diagnostics(robot)
        self._updaters[robot.name] = updater

    async def update_all(self) -> Dict[str, DiagnosticReport]:
        """Update all robot diagnostics."""
        for name, updater in self._updaters.items():
            try:
                self._reports[name] = await updater.update()
            except Exception as e:
                self._reports[name] = DiagnosticReport(
                    robot_name=name,
                    timestamp=datetime.now(),
                    statuses=[DiagnosticStatus(
                        name="update",
                        level=DiagnosticLevel.ERROR,
                        message=f"Update failed: {e}",
                    )],
                )

        return self._reports

    def get_fleet_status(self) -> Dict[str, int]:
        """Get count of robots at each level."""
        counts = {level: 0 for level in DiagnosticLevel}
        for report in self._reports.values():
            counts[report.overall_level] += 1
        return counts

    def get_robots_with_errors(self) -> List[str]:
        """Get names of robots with errors."""
        return [
            name for name, report in self._reports.items()
            if report.overall_level == DiagnosticLevel.ERROR
        ]

    def print_summary(self):
        """Print fleet diagnostic summary."""
        status = self.get_fleet_status()
        print(f"\nFleet Diagnostics Summary:")
        print(f"  OK:    {status[DiagnosticLevel.OK]}")
        print(f"  WARN:  {status[DiagnosticLevel.WARN]}")
        print(f"  ERROR: {status[DiagnosticLevel.ERROR]}")
        print(f"  STALE: {status[DiagnosticLevel.STALE]}")

        errors = self.get_robots_with_errors()
        if errors:
            print(f"\nRobots with errors: {', '.join(errors)}")
```

#### 6. Launch System

ROS launch files coordinate starting multiple nodes. Useful for classroom fleet setup.

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import asyncio
import yaml
from pathlib import Path

@dataclass
class LaunchConfig:
    """Configuration for launching robots."""
    robots: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)  # robot -> behavior


class LaunchSystem:
    """
    Coordinate startup of multiple robots.

    Inspired by ROS launch system.
    """

    def __init__(self):
        self._robots: Dict[str, Any] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    @classmethod
    def from_yaml(cls, filepath: str | Path) -> 'LaunchSystem':
        """Load launch config from YAML file."""
        with open(filepath) as f:
            config = yaml.safe_load(f)

        system = cls()
        system._config = LaunchConfig(
            robots=config.get("robots", []),
            parameters=config.get("parameters", {}),
            behaviors=config.get("behaviors", {}),
        )
        return system

    async def launch(self) -> Dict[str, bool]:
        """
        Launch all configured robots.

        Returns:
            Dict mapping robot name to success status
        """
        from r2d2 import R2D2

        results = {}

        for robot_name in self._config.robots:
            try:
                robot = R2D2(name=robot_name)
                await robot.connect()
                self._robots[robot_name] = robot
                results[robot_name] = True
                print(f"Launched: {robot_name}")
            except Exception as e:
                print(f"Failed to launch {robot_name}: {e}")
                results[robot_name] = False

        return results

    async def shutdown(self) -> None:
        """Shutdown all robots."""
        # Cancel tasks
        for task in self._tasks.values():
            task.cancel()

        # Disconnect robots
        for robot in self._robots.values():
            try:
                await robot.disconnect()
            except:
                pass

        self._robots.clear()
        self._tasks.clear()
        print("All robots shut down")

    def get_robot(self, name: str) -> Optional[Any]:
        """Get a launched robot by name."""
        return self._robots.get(name)

    def get_all_robots(self) -> List[Any]:
        """Get all launched robots."""
        return list(self._robots.values())

    async def run_behavior(self, robot_name: str, behavior_name: str) -> None:
        """Start a behavior on a robot."""
        robot = self._robots.get(robot_name)
        if not robot:
            raise ValueError(f"Robot {robot_name} not launched")

        # Behavior implementations would be registered separately
        # This is a simplified example
        print(f"Starting behavior '{behavior_name}' on {robot_name}")


# Example launch file (classroom_demo.yaml):
"""
robots:
  - D2-55E3
  - D2-1234
  - D2-ABCD
  - D2-5678

parameters:
  led_brightness: 200
  movement_speed: 50
  sound_volume: 128

behaviors:
  D2-55E3: patrol
  D2-1234: patrol
  D2-ABCD: sentry
  D2-5678: follow_leader
"""


# Example usage
async def classroom_demo():
    """Launch classroom demo."""
    launch = LaunchSystem.from_yaml("launch/classroom_demo.yaml")

    try:
        # Launch all robots
        results = await launch.launch()

        success_count = sum(results.values())
        print(f"\nLaunched {success_count}/{len(results)} robots")

        # Start behaviors
        for robot_name, behavior in launch._config.behaviors.items():
            if results.get(robot_name):
                await launch.run_behavior(robot_name, behavior)

        # Run until interrupted
        await asyncio.sleep(float('inf'))

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await launch.shutdown()
```

#### 7. Simulation / Mock Robot

ROS uses Gazebo for simulation. A mock R2D2 enables testing without hardware.

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import asyncio
import random

@dataclass
class SimulatedState:
    """Simulated robot state."""
    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0
    dome_position: float = 0.0
    stance: str = "bipod"
    battery_voltage: float = 3.85
    battery_percentage: int = 80
    front_led: tuple = (0, 0, 0)
    back_led: tuple = (0, 0, 0)


class MockR2D2:
    """
    Simulated R2D2 for testing without hardware.

    Implements the same interface as the real R2D2 class.
    Inspired by Gazebo simulation but much simpler.
    """

    def __init__(self, name: str = "D2-SIM"):
        self.name = name
        self.address = "00:00:00:00:00:00"
        self._connected = False
        self._state = SimulatedState()

        # Components (matching real R2D2 interface)
        self.drive = MockDriveComponent(self)
        self.dome = MockDomeComponent(self)
        self.stance = MockStanceComponent(self)
        self.leds = MockLEDComponent(self)
        self.audio = MockAudioComponent(self)
        self.sensors = MockSensorComponent(self)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()

    async def connect(self) -> None:
        """Simulate connection."""
        await asyncio.sleep(0.1)  # Simulate delay
        self._connected = True
        print(f"[SIM] {self.name} connected")

    async def disconnect(self) -> None:
        """Simulate disconnection."""
        self._connected = False
        print(f"[SIM] {self.name} disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get_battery_voltage(self) -> float:
        # Slowly drain battery
        self._state.battery_voltage -= 0.0001
        return self._state.battery_voltage

    async def get_battery_percentage(self) -> int:
        return self._state.battery_percentage

    async def get_firmware_version(self) -> str:
        return "SIM.1.0.0"


class MockDriveComponent:
    def __init__(self, robot: MockR2D2):
        self._robot = robot

    async def roll(self, heading: int, speed: int, duration: float = None) -> None:
        state = self._robot._state

        # Simulate movement
        distance = speed * 0.01 * (duration or 1.0)
        import math
        state.x += distance * math.sin(math.radians(heading))
        state.y += distance * math.cos(math.radians(heading))
        state.heading = heading

        if duration:
            await asyncio.sleep(duration)

        print(f"[SIM] Roll: heading={heading}, speed={speed}, pos=({state.x:.2f}, {state.y:.2f})")

    async def stop(self) -> None:
        print(f"[SIM] Stop")

    async def spin(self, degrees: int) -> None:
        self._robot._state.heading = (self._robot._state.heading + degrees) % 360
        await asyncio.sleep(abs(degrees) / 180)  # Simulate turn time
        print(f"[SIM] Spin: {degrees}°, new heading={self._robot._state.heading}")


class MockDomeComponent:
    def __init__(self, robot: MockR2D2):
        self._robot = robot

    async def set_position(self, angle: float) -> None:
        self._robot._state.dome_position = max(-160, min(180, angle))
        await asyncio.sleep(0.2)
        print(f"[SIM] Dome: {angle}°")

    async def get_position(self) -> float:
        return self._robot._state.dome_position

    async def center(self) -> None:
        await self.set_position(0)


class MockStanceComponent:
    def __init__(self, robot: MockR2D2):
        self._robot = robot

    async def set_tripod(self) -> None:
        self._robot._state.stance = "tripod"
        await asyncio.sleep(1.0)
        print(f"[SIM] Stance: tripod")

    async def set_bipod(self) -> None:
        self._robot._state.stance = "bipod"
        await asyncio.sleep(1.0)
        print(f"[SIM] Stance: bipod")


class MockLEDComponent:
    def __init__(self, robot: MockR2D2):
        self._robot = robot

    async def set_front(self, r: int, g: int, b: int) -> None:
        self._robot._state.front_led = (r, g, b)
        print(f"[SIM] Front LED: ({r}, {g}, {b})")

    async def set_back(self, r: int, g: int, b: int) -> None:
        self._robot._state.back_led = (r, g, b)
        print(f"[SIM] Back LED: ({r}, {g}, {b})")

    async def red(self) -> None:
        await self.set_front(255, 0, 0)

    async def green(self) -> None:
        await self.set_front(0, 255, 0)

    async def blue(self) -> None:
        await self.set_front(0, 0, 255)

    async def off(self) -> None:
        await self.set_front(0, 0, 0)
        await self.set_back(0, 0, 0)


class MockAudioComponent:
    def __init__(self, robot: MockR2D2):
        self._robot = robot

    async def play_sound(self, sound_id: int) -> None:
        print(f"[SIM] Sound: {sound_id}")
        await asyncio.sleep(0.5)

    async def happy(self) -> None:
        print(f"[SIM] Sound: happy beep!")

    async def sad(self) -> None:
        print(f"[SIM] Sound: sad boop...")

    async def excited(self) -> None:
        print(f"[SIM] Sound: excited chirps!")


class MockSensorComponent:
    def __init__(self, robot: MockR2D2):
        self._robot = robot

    async def get_data(self) -> Dict[str, Any]:
        """Return simulated sensor data with noise."""
        return {
            "accelerometer": (
                random.gauss(0, 0.1),
                random.gauss(0, 0.1),
                random.gauss(9.8, 0.1),
            ),
            "gyroscope": (
                random.gauss(0, 0.5),
                random.gauss(0, 0.5),
                random.gauss(0, 0.5),
            ),
            "dome_position": self._robot._state.dome_position,
        }


# Factory function
def create_robot(name: str, simulated: bool = False):
    """
    Create real or simulated robot.

    Args:
        name: Robot name
        simulated: If True, create MockR2D2

    Returns:
        R2D2 or MockR2D2 instance
    """
    if simulated:
        return MockR2D2(name=name)
    else:
        from r2d2 import R2D2
        return R2D2(name=name)


# Example: Test code with simulated robot
async def test_patrol_behavior():
    """Test patrol behavior with simulated robot."""
    async with MockR2D2("D2-TEST") as robot:
        # Same code works with real or mock robot
        await robot.leds.red()
        await robot.dome.set_position(90)
        await robot.drive.roll(heading=0, speed=50, duration=2.0)
        await robot.dome.center()
        await robot.audio.happy()
        await robot.drive.stop()
```

#### Summary: ROS-Inspired Features

| Feature | ROS Equivalent | R2D2 Implementation | Priority |
|---------|---------------|---------------------|----------|
| **Message Bus** | Topics/Pub-Sub | `MessageBus` class | Medium |
| **Transforms** | TF2 | `TransformTree` class | High (for SLAM) |
| **Bag Recording** | rosbag | `R2D2Bag` class | High |
| **Behavior Trees** | BehaviorTree.CPP | `BehaviorTree` classes | Medium |
| **Diagnostics** | diagnostic_updater | `DiagnosticUpdater` | High (for fleet) |
| **Launch System** | roslaunch | `LaunchSystem` class | Medium |
| **Simulation** | Gazebo | `MockR2D2` class | High (for testing) |
| **Visualization** | RViz | Web dashboard (future) | Low |
| **Parameters** | rosparam | Config dataclasses | Low |
| **Actions** | actionlib | Long-running commands | Low |

#### Educational Value

These ROS-inspired features teach fundamental robotics concepts:

1. **Pub/Sub messaging**: Distributed systems, decoupling
2. **Transforms**: Coordinate frames, spatial reasoning
3. **Bag recording**: Data collection, reproducibility
4. **Behavior trees**: Decision making, task planning
5. **Diagnostics**: System monitoring, fault detection
6. **Simulation**: Testing without hardware, CI/CD

**Sources:**
- [ROS.org](https://www.ros.org/)
- [ROS 2 Overview](https://www.roboticstomorrow.com/news/2025/05/20/ros-2-robot-operating-system-overview-and-key-features-of-the-robotics-software/24795)
- [BehaviorTree.CPP ROS2 Integration](https://www.behaviortree.dev/docs/ros2_integration/)
- [Nav2 Concepts](https://docs.nav2.org/concepts/index.html)
- [REP-103 Coordinate Conventions](https://www.ros.org/reps/rep-0103.html)

---

## Appendix A: R2D2 Protocol Reference

### Packet Structure (V2)

```
┌─────┬───────┬─────┬─────┬─────┬─────┬─────┬─────┬──────┬─────┬─────┐
│ SOP │ FLAGS │ TID │ SID │ DID │ CID │ SEQ │ ERR │ DATA │ CHK │ EOP │
│ 8D  │  1B   │ 0-1 │ 0-1 │ 1B  │ 1B  │ 1B  │ 0-1 │  nB  │ 1B  │ D8  │
└─────┴───────┴─────┴─────┴─────┴─────┴─────┴─────┴──────┴─────┴─────┘

SOP: Start of Packet (0x8D)
FLAGS: Bit flags controlling packet behavior
TID: Target ID (optional, present if FLAGS.HAS_TARGET)
SID: Source ID (optional, present if FLAGS.HAS_SOURCE)
DID: Device ID
CID: Command ID
SEQ: Sequence number (0-255)
ERR: Error code (optional, present in responses)
DATA: Command-specific payload
CHK: Checksum (XOR of all bytes except SOP/EOP, then XOR 0xFF)
EOP: End of Packet (0xD8)
```

### Escape Sequences

| Byte | Escaped As |
|------|------------|
| 0x8D (SOP) | 0xAB 0x05 |
| 0xD8 (EOP) | 0xAB 0x50 |
| 0xAB (ESC) | 0xAB 0x23 |

### Flag Bits

| Bit | Name | Description |
|-----|------|-------------|
| 0 | IS_RESPONSE | Packet is a response |
| 1 | REQUESTS_RESPONSE | Expects a response |
| 2 | REQUESTS_ERROR_RESPONSE | Only respond on error |
| 3 | IS_ACTIVITY | Activity indicator |
| 4 | HAS_TARGET | TID field present |
| 5 | HAS_SOURCE | SID field present |
| 7 | EXTENDED_FLAGS | Additional flags byte follows |

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0x00 | SUCCESS | Command succeeded |
| 0x01 | BAD_DEVICE_ID | Unknown device ID |
| 0x02 | BAD_COMMAND_ID | Unknown command ID |
| 0x03 | NOT_IMPLEMENTED | Command not implemented |
| 0x04 | RESTRICTED | Command restricted |
| 0x05 | BAD_DATA_LENGTH | Wrong payload length |
| 0x06 | COMMAND_FAILED | Command execution failed |
| 0x07 | BAD_PARAMETER | Invalid parameter value |
| 0x08 | BUSY | Robot busy |
| 0x09 | BAD_TARGET_ID | Unknown target ID |
| 0x0A | TARGET_UNAVAILABLE | Target not available |

---

## Appendix B: R2D2 Commands

### Animatronic (DID=0x17)

| CID | Name | Params | Response | Notes |
|-----|------|--------|----------|-------|
| 0x05 | play_animation | id:u8, wait:bool | - | 55+ animations |
| 0x06 | get_head_position | - | angle:f32 | Current dome position |
| 0x0D | perform_leg_action | action:u8 | - | 0=stop,1=tripod,2=bipod,3=waddle |
| 0x0F | set_head_position | angle:f32 | - | -160° to 180° |

### Drive (DID=0x16)

| CID | Name | Params | Response | Notes |
|-----|------|--------|----------|-------|
| 0x01 | raw_motors | L_mode:u8,L_pwr:u8,R_mode:u8,R_pwr:u8 | - | Direct motor |
| 0x07 | drive_with_heading | speed:u8,heading:u16,flags:u8 | - | Main drive |
| 0x0C | reset_heading | - | - | Reset yaw |

### IO (DID=0x1A)

| CID | Name | Params | Response | Notes |
|-----|------|--------|----------|-------|
| 0x07 | play_audio | id:u16,mode:u8 | - | 500+ sounds |
| 0x1A | set_all_leds | mask:u32,values:bytes | - | 8 LEDs |

### Sensor (DID=0x18)

| CID | Name | Params | Response | Notes |
|-----|------|--------|----------|-------|
| 0x00 | set_streaming_mask | interval:u16,count:u8,mask:u32 | - | Start streaming |
| 0x0C | collision_detected | - | async notify | Collision event |

### Power (DID=0x13)

| CID | Name | Params | Response | Notes |
|-----|------|--------|----------|-------|
| 0x00 | deep_sleep | - | - | Enter sleep |
| 0x01 | wake | - | - | Wake up |
| 0x10 | get_battery_state | - | state:u8 | Battery status |

---

## Appendix C: R2D2 LED Map

```
     ┌─────────────┐
     │   ◯ HOLO    │  Index 7: Holo Projector (brightness)
     │  PROJECTOR  │
     ├─────────────┤
     │  ░░░░░░░░░  │  Index 3: Logic Displays (brightness)
     │  ░ LOGIC ░  │
     │  ░░░░░░░░░  │
     ├─────────────┤
     │             │
     │   ● FRONT   │  Index 0-2: Front LED (RGB)
     │             │
     │             │
     │   ● BACK    │  Index 4-6: Back LED (RGB)
     │             │
     └─────────────┘
```

---

## Appendix D: Sound Categories

The R2D2 has 500+ sounds organized into categories:

- **Happy** (0x00-0x0F): Cheerful beeps and whistles
- **Sad** (0x10-0x1F): Mournful tones
- **Excited** (0x20-0x2F): Energetic sounds
- **Scared** (0x30-0x3F): Worried sounds
- **Chatty** (0x40-0x7F): Conversational beeps
- **Acknowledgment** (0x80-0x8F): Confirmation sounds
- **Alarm** (0x90-0x9F): Warning tones
- **Processing** (0xA0-0xAF): Thinking sounds
- **Misc** (0xB0+): Various other sounds

See `docs/reference/sounds.md` for complete listing.

---

*Document Version: 2.0*
*Created: 2026-01-16*
*Last Updated: 2026-01-16*
*Focus: R2D2 Hardware Compatibility*
