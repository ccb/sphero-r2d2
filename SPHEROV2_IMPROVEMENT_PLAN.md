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
