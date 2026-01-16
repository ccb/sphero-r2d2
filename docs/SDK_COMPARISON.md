# SDK Comparison: Official Sphero SDK vs spherov2-py

This document compares the official Sphero RVR SDK (`sphero-sdk-raspberrypi-python`) with the community `spherov2-py` library to identify useful patterns and features we could adopt.

**Note:** The official SDK only supports RVR robots (via serial connection to Raspberry Pi), while spherov2-py supports multiple toys via Bluetooth LE. Despite targeting different robots and connection methods, the design patterns are valuable for comparison.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Async Handling Approaches](#async-handling-approaches)
3. [Parameter Validation and Type Safety](#parameter-validation-and-type-safety)
4. [Error Handling](#error-handling)
5. [Sensor Streaming Design](#sensor-streaming-design)
6. [Connection Management](#connection-management)
7. [High-Level Control Abstractions](#high-level-control-abstractions)
8. [Patterns Worth Adopting](#patterns-worth-adopting)
9. [Features to Consider Implementing](#features-to-consider-implementing)
10. [Recommendations](#recommendations)

---

## Architecture Overview

### Official Sphero SDK

```
sphero_sdk/
├── common/                    # Shared components
│   ├── commands/             # Command dictionaries with Parameter objects
│   ├── enums/                # Comprehensive enumeration types
│   ├── sensors/              # Sensor streaming infrastructure
│   │   ├── sensor_streaming_control.py
│   │   ├── sensor_stream_slot.py
│   │   ├── sensor_stream_service.py
│   │   └── sensor_stream_attribute.py
│   ├── protocol/             # Message encoding/decoding
│   ├── parameter.py          # Strongly-typed Parameter class
│   └── exceptions.py         # Custom exception hierarchy
├── asyncio/                  # Async implementation
│   ├── client/toys/          # Toy-specific async classes
│   ├── controls/             # High-level control abstractions
│   └── server/               # Server-side components
└── observer/                 # Observer pattern implementation
    ├── events/               # Event dispatching
    └── controls/             # Observer-based controls
```

**Key Characteristics:**
- Dual API: Both `asyncio` and `observer` (callback-based) implementations
- Auto-generated command files from JSON specifications
- Strongly-typed Parameter objects with metadata
- Dedicated sensor streaming infrastructure with slots/services
- Event-driven observer pattern for notifications

### spherov2-py

```
spherov2/
├── adapter/                  # BLE adapters (bleak, tcp)
├── commands/                 # Command classes organized by device
├── controls/                 # Control abstractions (v1, v2)
├── listeners/                # Listener definitions for async events
├── toy/                      # Toy-specific classes
├── scanner.py                # Device discovery
├── sphero_edu.py            # High-level Sphero Edu API
├── utils.py                  # ToyUtil unified API across toys
└── types.py                  # Type definitions
```

**Key Characteristics:**
- Synchronous API with threading for background operations
- Context manager pattern for connections (`with toy:`)
- Inheritance hierarchy for different toy versions
- Protocol versions (v1 for older toys, v2 for newer)
- Unified `ToyUtil` for cross-toy compatibility

### Key Architectural Differences

| Aspect | Official SDK | spherov2-py |
|--------|--------------|-------------|
| Connection | Serial (UART) | Bluetooth LE |
| Async Model | True asyncio | Threading + synchronous |
| Commands | Dictionary + Parameter objects | Static methods in command classes |
| Sensors | Slots + Services architecture | Mask-based streaming |
| Code Generation | Auto-generated from JSON | Hand-written |
| API Style | Single robot focus | Multi-robot unified API |

---

## Async Handling Approaches

### Official SDK (True Asyncio)

```python
# Using asyncio throughout
async def main():
    await rvr.wake()
    await asyncio.sleep(2)
    await rvr.sensor_control.add_sensor_data_handler(
        service=RvrStreamingServices.accelerometer,
        handler=accelerometer_handler
    )
    await rvr.sensor_control.start(interval=250)

# Handler is also async
async def accelerometer_handler(data):
    print('Accelerometer:', data)

# Cleanup is also async
await rvr.close()
```

**Pros:**
- Non-blocking I/O throughout
- Clean async/await syntax
- Easy to compose with other async operations
- Better for resource utilization

**Cons:**
- Requires understanding of asyncio
- More complex error handling
- Harder to use in simple scripts

### spherov2-py (Threading + Synchronous)

```python
# Context manager with synchronous API
with toy as api:
    api.roll(180, 100, 2)  # Blocks for 2 seconds
    api.set_main_led(255, 0, 0)

# Background processing via threading
def __background(self):
    while not self.__stopped.wait(0.8):
        with self.__updating:
            self.__update_speeds()

# Sensor listeners run in separate threads
for f in self.__listeners:
    threading.Thread(target=f, args=(data,)).start()
```

**Pros:**
- Simpler for beginners
- Easy to use in scripts
- Context manager handles cleanup

**Cons:**
- Thread synchronization complexity
- Not truly non-blocking
- Harder to scale

### Recommendation

Consider offering both APIs:
1. Keep synchronous API for simple use cases
2. Add optional async API for advanced users
3. Use `asyncio` internally for BLE operations (bleak is already async)

---

## Parameter Validation and Type Safety

### Official SDK (Strong Parameter Objects)

```python
# sphero_sdk/common/parameter.py
class Parameter:
    __slots__ = ['__name', '__data_type', '__index', '__size', '__value']

    def __init__(self, *, name, data_type, index, size, value=None):
        self.__name = name
        self.__data_type = data_type  # 'uint8_t', 'float', 'bool', etc.
        self.__index = index
        self.__size = size
        self.__value = value

# Usage in commands
def drive_with_heading(speed, heading, flags, target, timeout):
    return {
        'did': DevicesEnum.drive,
        'cid': CommandsEnum.drive_with_heading,
        'seq': SequenceNumberGenerator.get_sequence_number(),
        'target': target,
        'timeout': timeout,
        'inputs': [
            Parameter(name='speed', data_type='uint8_t', index=0, value=speed, size=1),
            Parameter(name='heading', data_type='uint16_t', index=1, value=heading, size=1),
            Parameter(name='flags', data_type='uint8_t', index=2, value=flags, size=1),
        ],
    }
```

**Advantages:**
- Self-documenting command structures
- Clear data type specifications
- Enables automatic serialization based on type
- Support for input/output parameters

### spherov2-py (Direct Encoding)

```python
# spherov2/commands/drive.py
class Drive(Commands):
    _did = 22

    @staticmethod
    def drive_with_heading(toy, speed, heading, drive_flags: DriveFlags, proc=None):
        toy._execute(Drive._encode(toy, 7, proc, [speed, *to_bytes(heading, 2), drive_flags]))

# spherov2/helper.py
def to_bytes(value, size):
    return value.to_bytes(size, 'big')
```

**Current Limitations:**
- No validation of parameter ranges
- No type hints enforced at runtime
- Manual byte encoding
- No documentation of expected types in command signatures

### Recommendation

Add a validation layer:
```python
# Proposed validation decorator
def validate_params(**validators):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            for name, validator in validators.items():
                if name in bound.arguments:
                    validator(bound.arguments[name], name)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@validate_params(
    speed=lambda v, n: 0 <= v <= 255 or raise_(ValueError(f"{n} must be 0-255")),
    heading=lambda v, n: 0 <= v <= 359 or raise_(ValueError(f"{n} must be 0-359"))
)
def drive_with_heading(toy, speed, heading, drive_flags, proc=None):
    ...
```

---

## Error Handling

### Official SDK

```python
# sphero_sdk/common/exceptions.py
class BaseError(Exception):
    pass

class BadConnection(BaseError):
    pass

class BadResponse(BaseError):
    def __str__(self):
        return 'The Response returned from the Server suggests a mismatch between library versions'

# Error codes in packet
class Error(IntEnum):
    success = 0x00
    bad_device_id = 0x01
    bad_command_id = 0x02
    not_yet_implemented = 0x03
    command_is_restricted = 0x04
    bad_data_length = 0x05
    command_failed = 0x06
    bad_parameter_value = 0x07
    busy = 0x08
    bad_target_id = 0x09
    target_unavailable = 0x0a
```

### spherov2-py

```python
# spherov2/controls/__init__.py
class PacketDecodingException(Exception):
    ...

class CommandExecuteError(Exception):
    def __init__(self, err: 'Packet.Error'):
        self.err = err

# Packet.Error enum
class Error(IntEnum):
    success = 0x00
    bad_device_id = 0x01
    # ... same codes

def check_error(self):
    if self.err != Packet.Error.success:
        raise CommandExecuteError(self.err)
```

### Recommendations

1. **Create Exception Hierarchy:**
```python
class SpheroError(Exception):
    """Base class for all Sphero errors."""
    pass

class ConnectionError(SpheroError):
    """Connection-related errors."""
    pass

class CommandError(SpheroError):
    """Command execution errors."""
    def __init__(self, error_code, command_name=None):
        self.error_code = error_code
        self.command_name = command_name
        super().__init__(f"Command {command_name or 'unknown'} failed: {error_code.name}")

class TimeoutError(SpheroError):
    """Command timeout errors."""
    pass

class ValidationError(SpheroError):
    """Parameter validation errors."""
    pass
```

2. **Add error context to exceptions**
3. **Create recovery suggestions for common errors**

---

## Sensor Streaming Design

This is one of the most significant architectural differences.

### Official SDK (Slots and Services)

The official SDK uses a sophisticated streaming architecture:

```python
# Architecture:
# SensorStreamingControl
#   └── SensorStreamSlot (tokens 1-4, per processor)
#         └── SensorStreamService (e.g., IMU, Accelerometer)
#               └── SensorStreamAttribute (e.g., Pitch, Roll, Yaw)

class SensorStreamingControl:
    slot_token_1 = 0x01
    slot_token_2 = 0x02
    # ...

    def add_sensor_data_handler(self, service, handler):
        """Adds callback for a specific service."""
        self._sensor_handlers[service] = handler

    def start(self, interval):
        """Starts streaming at specified interval."""
        self.__add_service_handlers()
        self.__configure_services()
        self.__start_services()

class SensorStreamService:
    def __init__(self, id, name, data_size, attributes, processors):
        self.__attributes = attributes  # List of SensorStreamAttribute
        self.__processors = processors  # Which processor handles this

class SensorStreamAttribute:
    def __init__(self, name, min_value, max_value):
        self.__name = name
        self.__min_value = min_value
        self.__max_value = max_value
        self.__number_type = int if isinstance(min_value + max_value, int) else float
```

**Key Features:**
- Per-service handlers (register for specific sensors)
- Automatic normalization from raw bytes to meaningful values
- Multi-processor support (Nordic + ST microcontrollers on RVR)
- Slot-based configuration for optimal bandwidth usage
- Constants class for service names: `RvrStreamingServices.accelerometer`

### spherov2-py (Mask-Based + StreamingControl)

```python
# v1 control (older toys)
class SensorControl:
    def enable(self, *sensors):
        for sensor in sensors:
            if sensor in self.__toy.sensors:
                self.__enabled[sensor] = self.__toy.sensors[sensor]
        self.__update()

    def __update(self):
        sensors_mask = 0
        for sensor in self.__enabled.values():
            for component in sensor.values():
                sensors_mask |= component.bit
        self.__toy.set_sensor_streaming_mask(self.__interval, self.__count, sensors_mask)

# v2 control (newer toys)
class StreamingControl:
    __streaming_services = {
        'quaternion': StreamingService(OrderedDict(
            w=StreamingServiceAttribute(-1, 1),
            x=StreamingServiceAttribute(-1, 1),
            # ...
        ), slot=1),
        'imu': StreamingService(OrderedDict(
            pitch=StreamingServiceAttribute(-180, 180),
            # ...
        ), slot=1),
    }
```

**Current Limitations:**
- Single callback for all sensor data
- Less flexible service configuration
- Mixed abstractions between v1 and v2

### Recommendations

1. **Adopt per-service handler pattern:**
```python
class SensorControl:
    def add_handler(self, sensor_name: str, handler: Callable[[dict], None]):
        """Add handler for specific sensor."""
        self._handlers[sensor_name] = handler

    def remove_handler(self, sensor_name: str):
        """Remove handler for sensor."""
        self._handlers.pop(sensor_name, None)
```

2. **Create sensor service constants:**
```python
class StreamingServices:
    ACCELEROMETER = 'accelerometer'
    GYROSCOPE = 'gyroscope'
    IMU = 'imu'
    QUATERNION = 'quaternion'
    LOCATOR = 'locator'
    VELOCITY = 'velocity'
    # R2D2 specific
    HEAD_ANGLE = 'r2_head_angle'
```

3. **Add data validation:**
```python
class SensorStreamAttribute:
    def validate(self, value: float) -> bool:
        return self.min_value <= value <= self.max_value

    def normalize(self, raw_value: int, max_raw: int) -> float:
        ratio = raw_value / max_raw
        return self.min_value + ratio * (self.max_value - self.min_value)
```

---

## Connection Management

### Official SDK (Serial + DAL Pattern)

```python
# Data Access Layer abstraction
class SerialAsyncDal:
    def __init__(self, loop):
        self._loop = loop
        # ...

    async def send_command(self, **command_dict):
        # Serialize and send
        pass

# Toy initialization
rvr = SpheroRvrAsync(dal=SerialAsyncDal(loop))

# Explicit close
await rvr.close()
```

**Pros:**
- Clean abstraction via DAL (Data Access Layer)
- Easy to mock for testing
- Explicit lifecycle management

### spherov2-py (Context Manager + BLE)

```python
# BLE Adapter
class BleakAdapter:
    def __init__(self, address):
        self.__event_loop = asyncio.new_event_loop()
        self.__device = bleak.BleakClient(address)
        self.__thread = threading.Thread(target=self.__event_loop.run_forever)
        self.__thread.start()
        self.__execute(self.__device.connect())

    def close(self, disconnect=True):
        if disconnect:
            self.__execute(self.__device.disconnect())
        self.__event_loop.call_soon_threadsafe(self.__event_loop.stop)
        self.__thread.join()

# Toy usage
with find_R2D2() as toy:
    toy.roll(180, 100, 2)
```

**Current Limitations:**
- No reconnection logic
- No connection state tracking
- No event hooks for connection changes

### Recommendations

1. **Add connection state tracking:**
```python
class ConnectionState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    ERROR = auto()

class Toy:
    @property
    def connection_state(self) -> ConnectionState:
        return self._connection_state

    def on_connection_state_changed(self, handler: Callable[[ConnectionState], None]):
        self._connection_handlers.add(handler)
```

2. **Add auto-reconnection:**
```python
class BleakAdapter:
    def __init__(self, address, auto_reconnect=True, max_retries=3):
        self._auto_reconnect = auto_reconnect
        self._max_retries = max_retries

    async def _handle_disconnect(self, client):
        if self._auto_reconnect:
            for attempt in range(self._max_retries):
                try:
                    await self._reconnect()
                    break
                except Exception as e:
                    await asyncio.sleep(2 ** attempt)
```

3. **Add timeout configuration:**
```python
class ConnectionConfig:
    connect_timeout: float = 10.0
    command_timeout: float = 5.0
    reconnect_delay: float = 2.0
    max_reconnect_attempts: int = 3
```

---

## High-Level Control Abstractions

### Official SDK (Control Classes)

```python
# Drive Control abstraction
class DriveControlAsync:
    def __init__(self, rvr):
        self.__rvr = rvr

    async def reset_heading(self):
        await self.__rvr.reset_yaw()

    async def drive_forward_seconds(self, speed=0, heading=0, time_to_drive=1):
        await self.__timed_drive(speed, heading, self.__drive_no_flag, time_to_drive)

    async def roll_start(self, speed, heading):
        # Handles negative speed, heading normalization
        flags = 0
        while heading < 0:
            heading += 360
        if speed < 0:
            flags = flags | self.__drive_reverse_flag
        speed = abs(speed)
        if speed > 255:
            speed = 255
        heading = heading % 360
        await self.__rvr.drive_with_heading(speed, heading, flags)
```

### spherov2-py (ToyUtil + SpheroEduAPI)

```python
# ToyUtil - Cross-toy compatibility
class ToyUtil:
    @staticmethod
    def roll_start(toy: Toy, heading: int, speed: int, not_supported_handler=None):
        if hasattr(toy, 'drive_control'):
            toy.drive_control.roll_start(heading, speed)
        elif not_supported_handler:
            not_supported_handler()

# SpheroEduAPI - High-level educational API
class SpheroEduAPI:
    def roll(self, heading: int, speed: int, duration: float):
        """Roll the robot."""
        self.__update_heading(heading)
        self.__update_speed(speed)
        self.set_speed(speed)
        time.sleep(duration)
        self.set_speed(0)
```

**Comparison:**
- Official SDK: Focused, async control classes per subsystem
- spherov2-py: Polymorphic utilities + high-level API

---

## Patterns Worth Adopting

### 1. Parameter Object Pattern
Create strongly-typed parameter definitions that enable validation and self-documentation.

### 2. Service-Based Sensor Streaming
Allow registering handlers per sensor type rather than a single callback for all data.

### 3. Constants Classes
Define named constants for all magic values:
```python
class StreamingServices:
    ACCELEROMETER = 'accelerometer'
    # ...

class DriveFlags:
    FORWARD = 0x00
    REVERSE = 0x01
    # ...
```

### 4. Separate Async and Observer APIs
Offer both async (for advanced use) and callback-based (for simple use) APIs.

### 5. DAL (Data Access Layer) Pattern
Abstract the communication layer to enable easy testing and alternative transports.

### 6. Control Abstractions
Provide high-level control classes that handle edge cases (negative speeds, heading wrap-around).

### 7. Comprehensive Enums
Use enums extensively for error codes, flags, modes, and states.

---

## Features to Consider Implementing

### High Priority

1. **Parameter Validation**
   - Range checking for all command parameters
   - Meaningful error messages on validation failure
   - Type hints with runtime validation

2. **Per-Sensor Handlers**
   - Register callbacks for specific sensors
   - Filter sensor data before dispatching

3. **Connection State Management**
   - Connection state enum and events
   - Auto-reconnection with configurable retry logic
   - Connection health monitoring

4. **Enhanced Error Handling**
   - Exception hierarchy with specific error types
   - Error context and recovery suggestions

### Medium Priority

5. **Command Timeout Configuration**
   - Per-command timeout settings
   - Global timeout defaults
   - Timeout error with retry option

6. **Logging Infrastructure**
   - Configurable log levels
   - Structured logging for debugging
   - Performance metrics logging

7. **Firmware Version Checking**
   - Validate firmware compatibility
   - Warn about unsupported features

### Lower Priority

8. **Command Recording/Playback**
   - Record command sequences
   - Playback with timing

9. **Simulation Mode**
   - Mock adapter for testing without hardware
   - State simulation for development

---

## Recommendations

### Short-term Improvements

1. **Add validation decorators to commands**
   - Validate parameter ranges
   - Provide clear error messages
   - Minimal performance impact

2. **Implement per-sensor handlers**
   - Add `add_sensor_handler(sensor_name, callback)` method
   - Maintain backward compatibility with existing single-callback API

3. **Create comprehensive constants/enums**
   - Replace magic numbers with named constants
   - Improve code readability

### Medium-term Improvements

4. **Add async API option**
   - Create `AsyncToy` wrapper class
   - Use bleak's native async capabilities
   - Maintain sync API for backward compatibility

5. **Implement connection state tracking**
   - Add `ConnectionState` enum
   - Emit events on state changes
   - Support reconnection logic

6. **Create exception hierarchy**
   - `SpheroError` base class
   - Specific errors for connection, command, validation, timeout

### Long-term Improvements

7. **Add DAL abstraction layer**
   - Abstract communication protocol
   - Enable alternative transports (TCP proxy, mock)
   - Improve testability

8. **Create comprehensive test suite**
   - Unit tests with mock adapter
   - Integration tests for protocol compliance
   - Sensor data parsing tests

9. **Documentation improvements**
   - API documentation generation
   - Examples for each feature
   - Troubleshooting guide

---

## Conclusion

The official Sphero SDK provides valuable patterns for building robust robot control libraries, particularly in:

1. **Type safety** through Parameter objects
2. **Sensor streaming** via the slots/services architecture
3. **API design** with dual async/observer patterns
4. **Code organization** with clear separation of concerns

While spherov2-py has different requirements (multi-robot BLE support vs. single-robot serial), many of these patterns can be adapted to improve code quality, maintainability, and user experience.

The most impactful improvements would be:
1. Parameter validation for safer API usage
2. Per-sensor handlers for flexible sensor data processing
3. Connection state management for robust operation
4. Comprehensive error handling for better debugging
