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
