# Sphero R2-D2 Protocol Documentation (V2)

This document provides a comprehensive specification of the Sphero V2 protocol as used by R2-D2 and related droids (BB-9E, BB-8). It is based on analysis of the spherov2-py library implementation.

## Table of Contents

1. [Packet Structure](#1-packet-structure)
2. [Escape Sequences](#2-escape-sequences)
3. [Flags](#3-flags)
4. [Device IDs and Command IDs](#4-device-ids-and-command-ids)
5. [Response Matching](#5-response-matching)
6. [Error Codes](#6-error-codes)
7. [Sensor Streaming Protocol](#7-sensor-streaming-protocol)
8. [BLE Characteristics](#8-ble-characteristics)

---

## 1. Packet Structure

The Sphero V2 protocol uses a binary packet format with the following structure:

### 1.1 Packet Format Overview

```
[SOP] [FLAGS] [TID?] [SID?] [DID] [CID] [SEQ] [ERR?] [DATA...] [CHK] [EOP]
```

| Field | Size | Description |
|-------|------|-------------|
| SOP | 1 byte | Start of Packet marker: `0x8D` |
| FLAGS | 1 byte | Packet flags (see section 3) |
| TID | 1 byte | Target ID (optional, if `has_target_id` flag set) |
| SID | 1 byte | Source ID (optional, if `has_source_id` flag set) |
| DID | 1 byte | Device ID |
| CID | 1 byte | Command ID |
| SEQ | 1 byte | Sequence number (0-254) |
| ERR | 1 byte | Error code (response packets only, if `is_response` flag set) |
| DATA | N bytes | Command/response data payload |
| CHK | 1 byte | Checksum |
| EOP | 1 byte | End of Packet marker: `0xD8` |

### 1.2 Checksum Calculation

The checksum is calculated as:
```
CHK = 0xFF - (sum of all bytes between SOP and CHK, exclusive) & 0xFF
```

Python implementation:
```python
def packet_chk(payload):
    return 0xff - (sum(payload) & 0xff)
```

The checksum covers: FLAGS, TID (if present), SID (if present), DID, CID, SEQ, ERR (if present), and DATA.

### 1.3 Packet Size

- Minimum packet size (command without data): 7 bytes (`SOP + FLAGS + DID + CID + SEQ + CHK + EOP`)
- Minimum packet size (response without data): 8 bytes (adds ERR byte)
- With TID/SID: Add 1-2 bytes
- Data can be variable length

---

## 2. Escape Sequences

Since SOP (`0x8D`) and EOP (`0xD8`) are reserved markers, they must be escaped when they appear in the packet body. An escape byte (`0xAB`) is used.

### 2.1 Encoding Values

| Name | Value | Description |
|------|-------|-------------|
| ESCAPE | `0xAB` | Escape character |
| START (SOP) | `0x8D` | Start of Packet |
| END (EOP) | `0xD8` | End of Packet |
| ESCAPED_ESCAPE | `0x23` | Escaped form of 0xAB |
| ESCAPED_START | `0x05` | Escaped form of 0x8D |
| ESCAPED_END | `0x50` | Escaped form of 0xD8 |

### 2.2 Escape Rules

**When building a packet (encoding):**
- `0xAB` becomes `0xAB 0x23`
- `0x8D` becomes `0xAB 0x05`
- `0xD8` becomes `0xAB 0x50`

**When parsing a packet (decoding):**
- `0xAB 0x23` becomes `0xAB`
- `0xAB 0x05` becomes `0x8D`
- `0xAB 0x50` becomes `0xD8`

### 2.3 Example

If the data contains byte `0x8D`:
```
Original:  [0x8D, 0x..., 0x8D, ..., 0xD8]
Escaped:   [0x8D, 0x..., 0xAB, 0x05, ..., 0xD8]
                         ^^^^^^^^^ escaped
```

---

## 3. Flags

The FLAGS byte is a bitmask with the following bits:

| Bit | Value | Name | Description |
|-----|-------|------|-------------|
| 0 | `0x01` | is_response | Packet is a response (contains ERR field) |
| 1 | `0x02` | requests_response | Request expects a response |
| 2 | `0x04` | requests_only_error_response | Only respond on error |
| 3 | `0x08` | is_activity | Packet is an activity/command |
| 4 | `0x10` | has_target_id | TID field is present |
| 5 | `0x20` | has_source_id | SID field is present |
| 6 | `0x40` | unused | Reserved |
| 7 | `0x80` | extended_flags | Extended flags follow |

### 3.1 Common Flag Combinations

**Standard Command (requests response):**
```python
flags = requests_response | is_activity  # 0x0A
```

**Command with Target ID:**
```python
flags = requests_response | is_activity | has_target_id | has_source_id  # 0x3A
# SID is typically 0x01 (host), TID is processor nibble
```

### 3.2 Target ID (TID) Format

When addressing a specific processor, TID uses a nibble format:
```python
TID = (high_nibble << 4) | low_nibble
# high_nibble = 1 (host identifier)
# low_nibble = processor ID (1=PRIMARY, 2=SECONDARY)
```

Example: `TID = 0x12` targets the SECONDARY processor.

---

## 4. Device IDs and Command IDs

### 4.1 Device ID Summary

| DID | Name | Description |
|-----|------|-------------|
| 0x00 | Core | Basic device functions (V1 compatibility) |
| 0x11 (17) | SystemInfo | System information and configuration |
| 0x13 (19) | Power | Power management |
| 0x16 (22) | Drive | Motor control and driving |
| 0x17 (23) | Animatronic | Animations and R2-D2 specific features |
| 0x18 (24) | Sensor | Sensor streaming and collision detection |
| 0x1A (26) | IO | LEDs and audio |

---

### 4.2 Core Commands (DID: 0x00)

| CID | Command | Parameters | Response |
|-----|---------|------------|----------|
| 0x01 | Ping | None | Empty |
| 0x02 | Get Versions | None | 8 bytes version info |
| 0x10 | Set Bluetooth Name | Name (null-terminated) | Empty |
| 0x11 | Get Bluetooth Info | None | Name + Address |
| 0x20 | Get Power State | None | Power state struct |
| 0x21 | Enable Battery Changed Notify | 1 byte (bool) | Empty |
| 0x22 | Sleep | 5 bytes (interval, unk, unk2) | Empty |
| 0x25 | Set Inactivity Timeout | 2 bytes (timeout) | Empty |
| 0x26 | Get Charger State | None | 1 byte state |
| 0x27 | Get Factory Config Block CRC | None | 4 bytes CRC |
| 0x30 | Jump to Bootloader | None | Empty |

---

### 4.3 System Info Commands (DID: 0x11 / 17)

| CID | Command | Parameters | Response |
|-----|---------|------------|----------|
| 0x00 | Get Main App Version | None | 6 bytes (major, minor, patch as uint16) |
| 0x01 | Get Bootloader Version | None | 6 bytes |
| 0x03 | Get Board Revision | None | 1 byte |
| 0x06 | Get MAC Address | None | 6 bytes |
| 0x12 | Get Model Number | None | Variable |
| 0x13 | Get Stats ID | None | Variable |
| 0x17 | Get Secondary Main App Version | None | Triggers notify 0x18 |
| 0x1F | Get Processor Name | None | Null-terminated string |
| 0x20 | Get Boot Reason | None | 1 byte BootReason |
| 0x21 | Get Last Error Info | None | 46 bytes |
| 0x24 | Get Secondary MCU Bootloader Version | None | Triggers notify 0x25 |
| 0x28 | Get Three Character SKU | None | 3 bytes |
| 0x2B | Write Config Block | None | Empty |
| 0x2C | Get Config Block | None | Config block data |
| 0x2D | Set Config Block | Variable | Empty |
| 0x2E | Erase Config Block | 4 bytes | Empty |
| 0x30 | Get SWD Locking Status | None | 1 byte bool |
| 0x33 | Get Manufacturing Date | None | 4 bytes (year, month, day) |
| 0x38 | Get SKU | None | Null-terminated string |
| 0x39 | Get Core Up Time | None | 4 bytes (milliseconds) |
| 0x3A | Get Event Log Status | None | 12 bytes |
| 0x3B | Get Event Log Data | 8 bytes (offset, size) | Variable |
| 0x3C | Clear Event Log | None | Empty |
| 0x3D | Enable SOS Message Notify | 1 byte (bool) | Empty |
| 0x3F | Get SOS Message | None | Empty |
| 0x44 | Clear SOS Message | None | Empty |

---

### 4.4 Power Commands (DID: 0x13 / 19)

| CID | Command | Parameters | Response |
|-----|---------|------------|----------|
| 0x00 | Enter Deep Sleep | 1 byte | Empty |
| 0x01 | Sleep | None | Empty |
| 0x03 | Get Battery Voltage | None | 2 bytes (voltage * 100) |
| 0x04 | Get Battery State | None | 1 byte BatteryState |
| 0x05 | Enable Battery State Changed Notify | 1 byte (bool) | Empty |
| 0x0C | Force Battery Refresh | None | Empty |
| 0x0D | Wake | None | Empty |
| 0x10 | Get Battery Percentage | None | 1 byte (0-100) |
| 0x17 | Get Battery Voltage State | None | 1 byte BatteryVoltageState |
| 0x1B | Enable Battery Voltage State Change Notify | 1 byte (bool) | Empty |
| 0x1F | Get Charger State | None | 1 byte |
| 0x20 | Enable Charger State Changed Notify | 1 byte (bool) | Empty |
| 0x22 | Get Battery ADC Reading | None | 1 byte |
| 0x23 | Set Battery Calibration | 2 bytes | Empty |
| 0x24 | Get Battery Calibration | None | 1 byte |
| 0x25 | Get Battery Voltage In Volts | 1 byte (reading type) | 4 bytes float |
| 0x26 | Get Battery Voltage State Thresholds | None | 12 bytes (3 floats) |
| 0x27 | Get Current Sense Amplifier Current | 1 byte (amplifier ID) | 4 bytes float |
| 0x28 | Get EFuse Fault Status | 1 byte (EFuse ID) | 1 byte |
| 0x2A | Enable EFuse | 1 byte (EFuse ID) | Empty |

#### Battery States
| Value | State |
|-------|-------|
| 0 | CHARGED |
| 1 | CHARGING |
| 2 | NOT_CHARGING |
| 3 | OK |
| 4 | LOW |
| 5 | CRITICAL |
| 255 | UNKNOWN |

#### Battery Voltage States
| Value | State |
|-------|-------|
| 0 | UNKNOWN |
| 1 | OK |
| 2 | LOW |
| 3 | CRITICAL |

---

### 4.5 Drive Commands (DID: 0x16 / 22)

| CID | Command | Parameters | Response |
|-----|---------|------------|----------|
| 0x01 | Set Raw Motors | 4 bytes (left_mode, left_speed, right_mode, right_speed) | Empty |
| 0x06 | Reset Yaw | None | Empty |
| 0x07 | Drive With Heading | 4 bytes (speed, heading[2], flags) | Empty |
| 0x0B | Generic Raw Motor | Variable (index, mode, speed bytes) | Empty |
| 0x0C | Set Stabilization | 1 byte (stabilization index) | Empty |
| 0x0E | Set Control System Type | 2 bytes | Empty |
| 0x0F | Set Pitch Torque Modification | 1 byte | Empty |
| 0x20 | Set Component Parameters | Variable | Empty |
| 0x21 | Get Component Parameters | 2 bytes | Variable floats |
| 0x22 | Set Custom Control System Timeout | 2 bytes | Empty |
| 0x25 | Enable Motor Stall Notify | 1 byte (bool) | Empty |
| 0x27 | Enable Motor Fault Notify | 1 byte (bool) | Empty |
| 0x29 | Get Motor Fault State | None | 1 byte bool |

#### Drive Flags
| Bit | Value | Name |
|-----|-------|------|
| 0 | 0x01 | BACKWARD |
| 1 | 0x02 | TURBO |
| 2 | 0x04 | FAST_TURN |
| 3 | 0x08 | LEFT_DIRECTION |
| 4 | 0x10 | RIGHT_DIRECTION |
| 5 | 0x20 | ENABLE_DRIFT |

#### Raw Motor Modes
| Value | Mode |
|-------|------|
| 0 | OFF |
| 1 | FORWARD |
| 2 | REVERSE |

#### Stabilization Indexes
| Value | Mode |
|-------|------|
| 0 | NO_CONTROL_SYSTEM |
| 1 | FULL_CONTROL_SYSTEM |
| 2 | PITCH_CONTROL_SYSTEM |
| 3 | ROLL_CONTROL_SYSTEM |
| 4 | YAW_CONTROL_SYSTEM |
| 5 | SPEED_AND_YAW_CONTROL_SYSTEM |

#### Generic Raw Motor Indexes (R2-D2)
| Value | Motor |
|-------|-------|
| 0 | LEFT_DRIVE |
| 1 | RIGHT_DRIVE |
| 2 | HEAD |
| 3 | LEG |

---

### 4.6 Animatronic Commands (DID: 0x17 / 23)

These commands are specific to R2-D2 and BB-9E droids.

| CID | Command | Parameters | Response |
|-----|---------|------------|----------|
| 0x05 | Play Animation | 2 bytes (animation ID) | Empty |
| 0x0D | Perform Leg Action | 1 byte (leg action) | Empty |
| 0x0F | Set Head Position | 4 bytes (float, radians) | Empty |
| 0x14 | Get Head Position | None | 4 bytes float |
| 0x15 | Set Leg Position | 4 bytes (float) | Empty |
| 0x16 | Get Leg Position | None | 4 bytes float |
| 0x25 | Get Leg Action | None | 1 byte R2DoLegActions |
| 0x2A | Enable Leg Action Notify | 1 byte (bool) | Empty |
| 0x2B | Stop Animation | None | Empty |
| 0x2C | Enable Idle Animations | 1 byte (bool) | Empty |
| 0x2D | Enable Trophy Mode | 1 byte (bool) | Empty |
| 0x2E | Get Trophy Mode Enabled | None | 1 byte bool |
| 0x39 | Enable Head Reset to Zero Notify | 1 byte (bool) | Empty |

#### R2 Leg Actions
| Value | Action |
|-------|--------|
| 0 | STOP |
| 1 | THREE_LEGS |
| 2 | TWO_LEGS |
| 3 | WADDLE |

#### R2 Do Leg Actions (Response)
| Value | State |
|-------|-------|
| 0 | UNKNOWN |
| 1 | THREE_LEGS |
| 2 | TWO_LEGS |
| 3 | WADDLE |
| 4 | TRANSITIONING |

#### Notifications
| CID | Notification |
|-----|--------------|
| 0x11 | play_animation_complete_notify |
| 0x26 | leg_action_complete_notify |
| 0x3A | head_reset_to_zero_notify |

---

### 4.7 Sensor Commands (DID: 0x18 / 24)

| CID | Command | Parameters | Response |
|-----|---------|------------|----------|
| 0x00 | Set Sensor Streaming Mask | 7 bytes (interval[2], count, mask[4]) | Empty |
| 0x01 | Get Sensor Streaming Mask | None | 7 bytes |
| 0x0C | Set Extended Sensor Streaming Mask | 4 bytes (mask) | Empty |
| 0x0D | Get Extended Sensor Streaming Mask | None | 4 bytes |
| 0x0F | Enable Gyro Max Notify | 1 byte (bool) | Empty |
| 0x11 | Configure Collision Detection | 6 bytes | Empty |
| 0x13 | Reset Locator X and Y | None | Empty |
| 0x14 | Enable Collision Detected Notify | 1 byte (bool) | Empty |
| 0x17 | Set Locator Flags | 1 byte (bool) | Empty |
| 0x18 | Set Accelerometer Activity Threshold | 4 bytes float | Empty |
| 0x19 | Enable Accelerometer Activity Notify | 1 byte (bool) | Empty |
| 0x1B | Set Gyro Activity Threshold | 4 bytes float | Empty |
| 0x1C | Enable Gyro Activity Notify | 1 byte (bool) | Empty |
| 0x22 | Get Bot To Bot Infrared Readings | None | 4 bytes |
| 0x23 | Get RGBC Sensor Values | None | 8 bytes |
| 0x25 | Magnetometer Calibrate To North | None | Empty |
| 0x27 | Start Robot To Robot IR Broadcasting | 2 bytes | Empty |
| 0x28 | Start Robot To Robot IR Following | 2 bytes | Empty |
| 0x29 | Stop Robot To Robot IR Broadcasting | None | Empty |
| 0x2A | Send Robot To Robot IR Message | 5 bytes | Empty |
| 0x2B | Listen For Robot To Robot IR Message | 2 bytes | Empty |
| 0x30 | Get Ambient Light Sensor Value | None | 4 bytes float |
| 0x32 | Stop Robot To Robot IR Following | None | Empty |
| 0x33 | Start Robot To Robot IR Evading | 2 bytes | Empty |
| 0x34 | Stop Robot To Robot IR Evading | None | Empty |
| 0x35 | Enable Color Detection Notify | 4 bytes | Empty |
| 0x37 | Get Current Detected Color Reading | None | Variable |
| 0x38 | Enable Color Detection | 1 byte (bool) | Empty |
| 0x39 | Configure Streaming Service | Variable | Empty |
| 0x3A | Start Streaming Service | 2 bytes (period) | Empty |
| 0x3B | Stop Streaming Service | None | Empty |
| 0x3C | Clear Streaming Service | None | Empty |
| 0x3E | Enable Robot IR Message Notify | 1 byte (bool) | Empty |
| 0x3F | Send Infrared Message | 5 bytes | Empty |
| 0x41 | Enable Motor Current Notify | 1 byte (bool) | Empty |
| 0x42 | Get Motor Temperature | 1 byte (index) | 8 bytes (2 floats) |
| 0x47 | Configure Sensitivity Based Collision | 4 bytes | Empty |
| 0x48 | Enable Sensitivity Based Collision Notify | 1 byte (bool) | Empty |
| 0x4B | Get Motor Thermal Protection Status | None | 10 bytes |
| 0x4C | Enable Motor Thermal Protection Notify | 1 byte (bool) | Empty |

#### Collision Detection Parameters
```
[method, x_threshold, y_threshold, x_speed, y_speed, dead_time]
```

| Method Value | Detection Method |
|--------------|------------------|
| 0 | NO_COLLISION_DETECTION |
| 1 | ACCELEROMETER_BASED_DETECTION |
| 2 | ACCELEROMETER_BASED_WITH_EXTRA_FILTERING |
| 3 | HYBRID_ACCELEROMETER_AND_CONTROL_SYSTEM_DETECTION |

#### Notifications
| CID | Notification | Data Format |
|-----|--------------|-------------|
| 0x02 | sensor_streaming_data_notify | N floats (4 bytes each) |
| 0x10 | gyro_max_notify | 1 byte flags |
| 0x12 | collision_detected_notify | 17 bytes (see below) |
| 0x1A | accelerometer_activity_notify | Empty |
| 0x1D | gyro_activity_notify | Empty |
| 0x26 | magnetometer_north_yaw_notify | 2 bytes |
| 0x2C | robot_to_robot_ir_message_notify | 1 byte |
| 0x36 | color_detection_notify | 5 bytes |
| 0x3D | streaming_service_data_notify | Token + sensor data |
| 0x40 | motor_current_notify | 16 bytes |
| 0x49 | sensitivity_collision_notify | 4 bytes |
| 0x4D | motor_thermal_protection_notify | 10 bytes |

---

### 4.8 IO Commands (DID: 0x1A / 26)

| CID | Command | Parameters | Response |
|-----|---------|------------|----------|
| 0x04 | Set LED | 5 bytes | Empty |
| 0x07 | Play Audio File | 3 bytes (sound[2], mode) | Empty |
| 0x08 | Set Audio Volume | 1 byte (0-255) | Empty |
| 0x09 | Get Audio Volume | None | 1 byte |
| 0x0A | Stop All Audio | None | Empty |
| 0x0E | Set All LEDs With 16-bit Mask | 2 + N bytes (mask[2], values) | Empty |
| 0x19 | Start Idle LED Animation | None | Empty |
| 0x1A | Set All LEDs With 32-bit Mask | 4 + N bytes (mask[4], values) | Empty |
| 0x1C | Set All LEDs With 8-bit Mask | 1 + N bytes (mask, values) | Empty |
| 0x1D | Enable Color Tap Notify | 1 byte | Empty |

#### Audio Playback Modes
| Value | Mode |
|-------|------|
| 0 | PLAY_IMMEDIATELY |
| 1 | PLAY_ONLY_IF_NOT_PLAYING |
| 2 | PLAY_AFTER_CURRENT_SOUND |

#### R2-D2 LED Indices (for mask bits)
| Bit | LED |
|-----|-----|
| 0 | FRONT_RED |
| 1 | FRONT_GREEN |
| 2 | FRONT_BLUE |
| 3 | LOGIC_DISPLAYS |
| 4 | BACK_RED |
| 5 | BACK_GREEN |
| 6 | BACK_BLUE |
| 7 | HOLO_PROJECTOR |

---

## 5. Response Matching

### 5.1 Sequence Numbers

Each command packet contains a sequence number (SEQ) in the range 0-254. The sequence number is incremented for each new command and wraps around after 254.

```python
self.__seq = (self.__seq + 1) % 0xff  # 0-254
```

### 5.2 Response Identification

Responses are matched to requests using a tuple key:
```python
packet.id = (DID, CID, SEQ)
```

When a command is sent, the caller waits for a response with the same `(DID, CID, SEQ)` tuple.

### 5.3 Notifications vs Responses

**Responses:**
- Have `is_response` flag (0x01) set
- Match the SEQ of the request
- Contain ERR byte

**Notifications (Async Events):**
- Have SEQ = 0xFF (255)
- Registered listeners receive them based on `(DID, CID, 0xFF)` key
- Do not contain ERR byte typically (depends on implementation)

---

## 6. Error Codes

Response packets contain an ERR byte when the `is_response` flag is set.

| Code | Name | Description |
|------|------|-------------|
| 0x00 | success | Command executed successfully |
| 0x01 | bad_device_id | Unknown device ID |
| 0x02 | bad_command_id | Unknown command ID for device |
| 0x03 | not_yet_implemented | Command not implemented |
| 0x04 | command_is_restricted | Command is restricted/requires auth |
| 0x05 | bad_data_length | Data payload length is incorrect |
| 0x06 | command_failed | Command execution failed |
| 0x07 | bad_parameter_value | Invalid parameter value |
| 0x08 | busy | Device is busy |
| 0x09 | bad_target_id | Invalid target processor ID |
| 0x0A | target_unavailable | Target processor not responding |

### 6.1 Error Handling

```python
def check_error(self):
    if self.err != Packet.Error.success:
        raise CommandExecuteError(self.err)
```

---

## 7. Sensor Streaming Protocol

### 7.1 Overview

R2-D2 supports two sensor streaming mechanisms:
1. **Legacy Sensor Streaming** - Uses mask-based configuration
2. **Streaming Service** - More flexible slot-based configuration

### 7.2 Legacy Sensor Streaming Mask Bits

Set using `set_sensor_streaming_mask` and `set_extended_sensor_streaming_mask`.

#### Standard Sensors Mask (32-bit)

| Bit | Hex Value | Sensor | Components |
|-----|-----------|--------|------------|
| 25 | 0x2000000 | Quaternion | X |
| 24 | 0x1000000 | Quaternion | Y |
| 23 | 0x0800000 | Quaternion | Z |
| 22 | 0x0400000 | Quaternion | W |
| 18 | 0x0040000 | Attitude | Pitch |
| 17 | 0x0020000 | Attitude | Roll |
| 16 | 0x0010000 | Attitude | Yaw |
| 15 | 0x0008000 | Accelerometer | X |
| 14 | 0x0004000 | Accelerometer | Y |
| 13 | 0x0002000 | Accelerometer | Z |
| 9 | 0x0000200 | Accel One | Combined acceleration |
| 6 | 0x0000040 | Locator | X position |
| 5 | 0x0000020 | Locator | Y position |
| 4 | 0x0000010 | Velocity | X |
| 3 | 0x0000008 | Velocity | Y |
| 2 | 0x0000004 | Speed | Speed magnitude |
| 1 | 0x0000002 | Core Time | Timestamp |

#### Extended Sensors Mask (32-bit) - R2-D2 Specific

| Bit | Hex Value | Sensor | Components | Range |
|-----|-----------|--------|------------|-------|
| 26 | 0x4000000 | R2 Head Angle | Angle | -162 to 182 degrees |
| 25 | 0x2000000 | Gyroscope | X | -20000 to 20000 |
| 24 | 0x1000000 | Gyroscope | Y | -20000 to 20000 |
| 23 | 0x0800000 | Gyroscope | Z | -20000 to 20000 |

### 7.3 Sensor Value Ranges

| Sensor | Component | Min | Max | Modifier |
|--------|-----------|-----|-----|----------|
| Quaternion | X, Y, Z, W | -1.0 | 1.0 | None |
| Attitude | Pitch, Roll, Yaw | -179 | 180 | Degrees |
| Accelerometer | X, Y, Z | -8.19 | 8.19 | g |
| Accel One | - | 0 | 8000 | None |
| Locator | X, Y | -32768 | 32767 | x100 (cm) |
| Velocity | X, Y | -32768 | 32767 | x100 (cm/s) |
| Speed | - | 0 | 32767 | None |
| Gyroscope | X, Y, Z | -20000 | 20000 | deg/s |
| R2 Head Angle | - | -162 | 182 | Degrees |

### 7.4 Streaming Service Configuration

The streaming service uses a slot-based system:

```python
# Configure streaming service
configure_streaming_service(slot, configuration, processor)

# Configuration format per sensor:
# [sensor_index (2 bytes), data_size (1 byte)]

# Data sizes:
EIGHT_BIT = 0
SIXTEEN_BIT = 1
THIRTY_TWO_BIT = 2
```

#### Streaming Service Sensors

| Index | Sensor | Slot | Processor | Data Size |
|-------|--------|------|-----------|-----------|
| 0 | Quaternion (W, X, Y, Z) | 1 | Secondary | 32-bit |
| 1 | IMU (Pitch, Roll, Yaw) | 1 | Secondary | 32-bit |
| 2 | Accelerometer (X, Y, Z) | 1 | Secondary | 32-bit |
| 3 | Color Detection (R, G, B, Index, Confidence) | 1 | Primary | 8-bit |
| 4 | Gyroscope (X, Y, Z) | 1 | Secondary | 32-bit |
| 5 | Core Time Lower | 3 | Secondary | 32-bit |
| 6 | Locator (X, Y) | 2 | Secondary | 32-bit |
| 7 | Velocity (X, Y) | 2 | Secondary | 32-bit |
| 8 | Speed | 2 | Secondary | 32-bit |
| 9 | Core Time Upper | 3 | Secondary | 32-bit |
| 10 | Ambient Light | 2 | Primary | 32-bit |

### 7.5 Streaming Data Format

**Legacy streaming (CID 0x02):**
```
[float, float, float, ...]  # Big-endian IEEE 754 floats
```

**Streaming service (CID 0x3D):**
```
[token (1 byte), sensor_data...]
# Token low nibble indicates slot
# Data size depends on configuration
```

---

## 8. BLE Characteristics

### 8.1 R2-D2 / BB-9E UUIDs

| UUID | Purpose |
|------|---------|
| `00020005-574f-4f20-5370-6865726f2121` | Handshake (write "usetheforce...band") |
| `00010002-574f-4f20-5370-6865726f2121` | Commands (send) and Responses (notify) |

### 8.2 Handshake Sequence

1. Connect to BLE device
2. Write `b'usetheforce...band'` to `00020005-574f-4f20-5370-6865726f2121`
3. Subscribe to notifications on `00010002-574f-4f20-5370-6865726f2121`
4. Device is ready for commands

### 8.3 Packet Transmission

Packets are sent in chunks of up to 20 bytes due to BLE MTU limitations:
```python
while payload:
    adapter.write(send_uuid, payload[:20])
    payload = payload[20:]
    time.sleep(cmd_safe_interval)  # 0.12 seconds for R2-D2
```

---

## Appendix A: R2-D2 Animation IDs

| ID | Name | Description |
|----|------|-------------|
| 0-6 | CHARGER_1 to CHARGER_7 | Charging animations |
| 7 | EMOTE_ALARM | Alarm emote |
| 8 | EMOTE_ANGRY | Angry emote |
| 9 | EMOTE_ATTENTION | Attention emote |
| 10 | EMOTE_FRUSTRATED | Frustrated emote |
| 11 | EMOTE_DRIVE | Driving emote |
| 12 | EMOTE_EXCITED | Excited emote |
| 13 | EMOTE_SEARCH | Searching emote |
| 14 | EMOTE_SHORT_CIRCUIT | Short circuit emote |
| 15 | EMOTE_LAUGH | Laughing emote |
| 16 | EMOTE_NO | No/negative emote |
| 17 | EMOTE_RETREAT | Retreat emote |
| 18 | EMOTE_FIERY | Fiery/angry emote |
| 19 | EMOTE_UNDERSTOOD | Understood emote |
| 21 | EMOTE_YES | Yes/affirmative emote |
| 22 | EMOTE_SCAN | Scanning emote |
| 24 | EMOTE_SURPRISED | Surprised emote |
| 25-27 | IDLE_1 to IDLE_3 | Idle animations |
| 31-54 | WWM_* | Watch With Me animations |
| 55 | MOTOR | Motor sound |

---

## Appendix B: R2-D2 Audio IDs (Selection)

The R2-D2 has over 400 audio clips. Key categories:

| ID Range | Category |
|----------|----------|
| 1704-1950 | R2 Access Panels, Alarm, Annoyed, Burnout |
| 1950-2600 | R2 Chatty (1-62) |
| 2600-2800 | R2 Excited (1-16) |
| 2797-2920 | R2 Head Spin, Hey (1-12) |
| 2919-3100 | R2 Laugh (1-4), Motor |
| 3101-3300 | R2 Negative (1-28) |
| 3302-3500 | R2 Positive (1-23) |
| 3484-3800 | R2 Sad (1-25) |
| 3797-3864 | R2 Scream, Short Out |
| 3864-3941 | R2Q5 sounds |
| 1609-1702 | R2 Fall, Hit (1-11), Step (1-6) |

---

## Appendix C: Collision Detection Data Format

The collision notification (CID 0x12) returns 17 bytes:

```python
struct.unpack('>3hB3hBL', packet.data)
# Results in:
# (accel_x, accel_y, accel_z, axis_flags, power_x, power_y, power_z, speed, timestamp)
```

| Field | Type | Description |
|-------|------|-------------|
| accel_x | int16 | X acceleration (/ 4096 for g) |
| accel_y | int16 | Y acceleration |
| accel_z | int16 | Z acceleration |
| axis_flags | uint8 | Bit 0=X axis, Bit 1=Y axis |
| power_x | int16 | Impact power X |
| power_y | int16 | Impact power Y |
| power_z | int16 | Impact power Z |
| speed | uint8 | Speed at impact |
| timestamp | uint32 | Time in milliseconds (/ 1000 for seconds) |

---

## Appendix D: Example Packet Construction

### Example: Set Head Position to 0.5 radians

```python
# Command
DID = 0x17  # Animatronic
CID = 0x0F  # Set Head Position
SEQ = 0x00  # Sequence number
DATA = struct.pack('>f', 0.5)  # Big-endian float

# With target processor (TID/SID)
FLAGS = 0x3A  # requests_response | is_activity | has_target_id | has_source_id
TID = 0x12    # Secondary processor
SID = 0x01    # Host

# Build packet body (before escaping)
body = [FLAGS, TID, SID, DID, CID, SEQ] + list(DATA)
CHK = 0xFF - (sum(body) & 0xFF)
body.append(CHK)

# Apply escaping and add SOP/EOP
packet = [0x8D] + escape(body) + [0xD8]
```

---

## References

- Sphero SDK API Specification: https://sdk.sphero.com/docs/api_spec/general_api
- spherov2-py library: https://github.com/artificial-intelligence-class/spherov2.py
