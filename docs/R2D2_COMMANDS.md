# R2-D2 Command Reference

Complete reference for all commands supported by the Sphero R2-D2.

## Command Structure

Commands are sent as V2 protocol packets with:
- **DID** (Device ID): Identifies the subsystem
- **CID** (Command ID): Identifies the specific command
- **DATA**: Command parameters

## Device IDs

| DID | Name | Description |
|-----|------|-------------|
| 0x13 (19) | Power | Battery, sleep, wake |
| 0x16 (22) | Drive | Movement, motors |
| 0x17 (23) | Animatronic | Dome, legs, animations |
| 0x1A (26) | IO | LEDs, audio |

---

## Power Commands (DID=0x13)

### Get Battery Voltage (CID=0x03)

Returns the battery voltage in volts.

```python
voltage = Power.get_battery_voltage(toy)  # Returns float (e.g., 3.85)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| (none) | - | - |

| Response | Type | Description |
|----------|------|-------------|
| voltage | uint16 | Voltage × 100 (divide by 100 for volts) |

### Get Battery State (CID=0x04)

Returns the current battery state.

```python
state = Power.get_battery_state(toy)  # Returns BatteryStates enum
```

| State | Value | Description |
|-------|-------|-------------|
| CHARGED | 0 | Fully charged |
| CHARGING | 1 | Currently charging |
| NOT_CHARGING | 2 | On battery, not charging |
| OK | 3 | Battery level OK |
| LOW | 4 | Battery low |
| CRITICAL | 5 | Battery critical |

### Wake (CID=0x0D)

Wakes the robot from sleep mode.

```python
Power.wake(toy)
```

### Sleep (CID=0x01)

Puts the robot to sleep.

```python
Power.sleep(toy)
```

### Get Battery Percentage (CID=0x10)

Returns battery level as percentage (0-100).

```python
percent = Power.get_battery_percentage(toy)  # Returns 0-100
```

### Get Battery Voltage In Volts (CID=0x25)

Returns precise battery voltage as float.

```python
from spherov2.commands.power import BatteryVoltageReadingTypes
voltage = Power.get_battery_voltage_in_volts(toy, BatteryVoltageReadingTypes.CALIBRATED_AND_FILTERED)
```

| Reading Type | Value | Description |
|--------------|-------|-------------|
| CALIBRATED_AND_FILTERED | 0 | Most accurate |
| CALIBRATED_AND_UNFILTERED | 1 | Raw calibrated |
| UNCALIBRATED_AND_UNFILTERED | 2 | Raw ADC |

---

## Drive Commands (DID=0x16)

### Drive With Heading (CID=0x07)

Drive at specified speed and heading.

```python
from spherov2.commands.drive import DriveFlags
Drive.drive_with_heading(toy, speed=100, heading=180, drive_flags=DriveFlags.FORWARD)
```

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| speed | uint8 | 0-255 | Speed (0=stop, 255=max) |
| heading | uint16 | 0-359 | Direction in degrees |
| flags | DriveFlags | - | Direction and mode flags |

| Flag | Value | Description |
|------|-------|-------------|
| FORWARD | 0x00 | Drive forward |
| BACKWARD | 0x01 | Drive backward |
| TURBO | 0x02 | Enable turbo/boost |
| FAST_TURN | 0x04 | Fast turning mode |

### Set Raw Motors (CID=0x01)

Direct motor control.

```python
from spherov2.commands.drive import RawMotorModes
Drive.set_raw_motors(toy,
    left_mode=RawMotorModes.FORWARD, left_speed=100,
    right_mode=RawMotorModes.FORWARD, right_speed=100)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| left_mode | RawMotorModes | OFF/FORWARD/REVERSE |
| left_speed | uint8 | 0-255 |
| right_mode | RawMotorModes | OFF/FORWARD/REVERSE |
| right_speed | uint8 | 0-255 |

### Reset Yaw (CID=0x06)

Reset the heading reference to current orientation.

```python
Drive.reset_yaw(toy)
```

### Set Stabilization (CID=0x0C)

Enable/disable stabilization control system.

```python
from spherov2.commands.drive import StabilizationIndexes
Drive.set_stabilization(toy, StabilizationIndexes.FULL_CONTROL_SYSTEM)
```

| Index | Value | Description |
|-------|-------|-------------|
| NO_CONTROL_SYSTEM | 0 | Disable stabilization |
| FULL_CONTROL_SYSTEM | 1 | Full stabilization |
| PITCH_CONTROL_SYSTEM | 2 | Pitch only |
| ROLL_CONTROL_SYSTEM | 3 | Roll only |
| YAW_CONTROL_SYSTEM | 4 | Yaw only |

---

## Animatronic Commands (DID=0x17)

### Set Head Position (CID=0x0F)

Rotate the dome to specified angle.

```python
Animatronic.set_head_position(toy, angle)  # angle is float in degrees
```

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| angle | float32 | -160 to 180 | Dome rotation angle |

**Note:** Dome rotation requires adequate battery (>3.7V). May fail silently at low voltage.

### Get Head Position (CID=0x14)

Read current dome position.

```python
angle = Animatronic.get_head_position(toy)  # Returns float
```

### Perform Leg Action (CID=0x0D)

Change leg stance.

```python
from spherov2.commands.animatronic import R2LegActions
Animatronic.perform_leg_action(toy, R2LegActions.THREE_LEGS)
```

| Action | Value | Description |
|--------|-------|-------------|
| STOP | 0 | Stop current action |
| THREE_LEGS | 1 | Deploy third leg (tripod) |
| TWO_LEGS | 2 | Retract third leg (bipod) |
| WADDLE | 3 | Waddle walk mode |

### Get Leg Action (CID=0x25)

Get current leg state.

```python
state = Animatronic.get_leg_action(toy)  # Returns R2DoLegActions enum
```

| State | Value | Description |
|-------|-------|-------------|
| UNKNOWN | 0 | State unknown |
| THREE_LEGS | 1 | Tripod stance |
| TWO_LEGS | 2 | Bipod stance |
| WADDLE | 3 | Waddling |
| TRANSITIONING | 4 | Changing stance |

### Play Animation (CID=0x05)

Play a pre-defined animation.

```python
Animatronic.play_animation(toy, animation_id)
```

See [Animations List](#animations) for available animation IDs.

### Stop Animation (CID=0x2B)

Stop currently playing animation.

```python
Animatronic.stop_animation(toy)
```

### Enable Idle Animations (CID=0x2C)

Enable/disable automatic idle animations.

```python
Animatronic.enable_idle_animations(toy, enable=True)
```

### Enable Trophy Mode (CID=0x2D)

Trophy/display mode - robot stays stationary.

```python
Animatronic.enable_trophy_mode(toy, enable=True)
```

---

## IO Commands (DID=0x1A)

### Set All LEDs (CID=0x1A / 0x0E)

Set multiple LEDs at once using a bitmask.

```python
# Using 32-bit mask (R2-D2)
IO.set_all_leds_with_32_bit_mask(toy, mask, values)

# Using 16-bit mask
IO.set_all_leds_with_16_bit_mask(toy, mask, values)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| mask | uint32/uint16 | Bitmask of LEDs to set |
| values | bytes | LED values (one per set bit) |

### R2-D2 LED Map

| LED | Bit | Description |
|-----|-----|-------------|
| FRONT_RED | 0 | Front LED red channel |
| FRONT_GREEN | 1 | Front LED green channel |
| FRONT_BLUE | 2 | Front LED blue channel |
| LOGIC_DISPLAYS | 3 | Logic display brightness |
| BACK_RED | 4 | Back LED red channel |
| BACK_GREEN | 5 | Back LED green channel |
| BACK_BLUE | 6 | Back LED blue channel |
| HOLO_PROJECTOR | 7 | Holographic projector brightness |

### Play Audio File (CID=0x07)

Play a pre-recorded sound.

```python
from spherov2.commands.io import AudioPlaybackModes
IO.play_audio_file(toy, sound_id, AudioPlaybackModes.PLAY_IMMEDIATELY)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| sound_id | uint16 | Sound ID (0-500+) |
| mode | AudioPlaybackModes | Playback behavior |

| Mode | Value | Description |
|------|-------|-------------|
| PLAY_IMMEDIATELY | 0 | Interrupt current sound |
| PLAY_ONLY_IF_NOT_PLAYING | 1 | Skip if already playing |
| PLAY_AFTER_CURRENT_SOUND | 2 | Queue after current |

### Set Audio Volume (CID=0x08)

Set speaker volume.

```python
IO.set_audio_volume(toy, volume)  # 0-255
```

### Get Audio Volume (CID=0x09)

Get current volume.

```python
volume = IO.get_audio_volume(toy)  # Returns 0-255
```

### Stop All Audio (CID=0x0A)

Stop all audio playback.

```python
IO.stop_all_audio(toy)
```

---

## Animations

R2-D2 supports 51 pre-defined animations:

| Animation | ID | Description |
|-----------|-----|-------------|
| CHARGER_1 through CHARGER_7 | 0-6 | Charger placement animations |
| EMOTE_ALARM | 7 | Alarm/alert |
| EMOTE_ANGRY | 8 | Angry expression |
| EMOTE_ANNOYED | 9 | Annoyed |
| EMOTE_ATTENTION | 10 | Getting attention |
| EMOTE_CHATTY | 12 | Chatty/talkative |
| EMOTE_DRIVE | 13 | Driving mode |
| EMOTE_EXCITED | 14 | Excited |
| EMOTE_FIERY | 15 | Fiery/intense |
| EMOTE_ION_BLAST | 17 | Ion blast effect |
| EMOTE_LAUGH | 18 | Laughing |
| EMOTE_LONG_FALL | 19 | Long fall |
| EMOTE_NO | 20 | Negative/no |
| EMOTE_PROUD | 21 | Proud |
| EMOTE_SCARED | 23 | Scared |
| EMOTE_SHORT_FALL | 24 | Short fall |
| EMOTE_SLEEP | 25 | Going to sleep |
| EMOTE_SURPRISED | 26 | Surprised |
| EMOTE_YES | 28 | Affirmative/yes |
| HIT | 29 | Getting hit |
| WWM_ANGRY | 30 | Watch with me - angry |
| WWM_ANXIOUS | 31 | Watch with me - anxious |
| WWM_BOW | 32 | Watch with me - bow |
| WWM_CONCERN | 33 | Watch with me - concern |
| WWM_CURIOUS | 34 | Watch with me - curious |
| WWM_DOUBLE_TAKE | 35 | Watch with me - double take |
| WWM_EXCITED | 36 | Watch with me - excited |
| WWM_FIERY | 37 | Watch with me - fiery |
| WWM_HAPPY | 38 | Watch with me - happy |
| WWM_JITTERY | 39 | Watch with me - jittery |
| WWM_LAUGH | 40 | Watch with me - laugh |
| WWM_LONG_SHAKE | 41 | Watch with me - long shake |
| WWM_NO | 42 | Watch with me - no |
| WWM_OMINOUS | 43 | Watch with me - ominous |
| WWM_RELIEVED | 44 | Watch with me - relieved |
| WWM_SAD | 45 | Watch with me - sad |
| WWM_SCARED | 46 | Watch with me - scared |
| WWM_SHAKE | 47 | Watch with me - shake |
| WWM_SURPRISED | 48 | Watch with me - surprised |
| WWM_TAUNTING | 49 | Watch with me - taunting |
| WWM_WHISPER | 50 | Watch with me - whisper |

---

## Audio Sounds

R2-D2 has 500+ pre-recorded sounds. Major categories:

### R2-D2 Specific Sounds (IDs 1704-2110)

| Category | ID Range | Count | Description |
|----------|----------|-------|-------------|
| Access Panels | 1704-1707 | 4 | Panel sounds |
| Alarm | 1708-1720 | 13 | Alarm beeps |
| Annoyed | 1721-1750 | 30 | Annoyed sounds |
| Burnout | 1751-1758 | 8 | Burnout/malfunction |
| Chatty | 1759-1820 | 62 | Conversational beeps |
| Excited | 1821-1836 | 16 | Excited sounds |
| Head Spin | 1837-1843 | 7 | Head spinning |
| Hey | 1844-1852 | 9 | Getting attention |
| Laugh | 1853-1861 | 9 | Laughing |
| Negative | 1862-1889 | 28 | Negative responses |
| Positive | 1890-1912 | 23 | Positive responses |
| Sad | 1913-1937 | 25 | Sad sounds |
| Scream | 1938-1976 | 39 | Screaming |
| Short Out | 1977-1982 | 6 | Short circuit |

### Test Tones

| Sound | ID | Frequency |
|-------|-----|-----------|
| TEST_1497HZ | 1 | 1497 Hz |
| TEST_200HZ | 32 | 200 Hz |
| TEST_2517HZ | 63 | 2517 Hz |
| TEST_3581HZ | 94 | 3581 Hz |
| TEST_431HZ | 125 | 431 Hz |
| TEST_6011HZ | 156 | 6011 Hz |
| TEST_853HZ | 187 | 853 Hz |

---

## Notifications (Async Events)

Some commands can enable asynchronous notifications:

| Event | DID | CID | Description |
|-------|-----|-----|-------------|
| battery_state_changed | 0x13 | 0x06 | Battery state changed |
| will_sleep | 0x13 | 0x19 | Robot about to sleep |
| did_sleep | 0x13 | 0x1A | Robot went to sleep |
| motor_stall | 0x16 | 0x26 | Motor stalled |
| motor_fault | 0x16 | 0x28 | Motor fault detected |
| play_animation_complete | 0x17 | 0x11 | Animation finished |
| leg_action_complete | 0x17 | 0x26 | Leg action finished |

### Enabling Notifications

```python
# Enable battery state notifications
Power.enable_battery_state_changed_notify(toy, enable=True)

# Enable motor stall notifications
Drive.enable_motor_stall_notify(toy, enable=True)

# Enable leg action complete notifications
Animatronic.enable_leg_action_notify(toy, enable=True)
```

---

## Error Codes

Commands may return error codes:

| Code | Name | Description |
|------|------|-------------|
| 0x00 | success | Command succeeded |
| 0x01 | bad_device_id | Invalid DID |
| 0x02 | bad_command_id | Invalid CID |
| 0x03 | not_yet_implemented | Command not implemented |
| 0x04 | command_is_restricted | Permission denied |
| 0x05 | bad_data_length | Wrong parameter length |
| 0x06 | command_failed | Command execution failed |
| 0x07 | bad_parameter_value | Invalid parameter value |
| 0x08 | busy | Robot busy, try again |
| 0x09 | bad_target_id | Invalid target ID |
| 0x0A | target_unavailable | Target not available |

---

## Quick Reference

### Common Operations

```python
from spherov2.commands.power import Power
from spherov2.commands.drive import Drive, DriveFlags
from spherov2.commands.animatronic import Animatronic, R2LegActions
from spherov2.commands.io import IO, AudioPlaybackModes

# Wake up
Power.wake(toy)

# Check battery
voltage = Power.get_battery_voltage(toy)
state = Power.get_battery_state(toy)

# Drive forward
Drive.drive_with_heading(toy, 100, 0, DriveFlags.FORWARD)

# Stop
Drive.drive_with_heading(toy, 0, 0, DriveFlags.FORWARD)

# Rotate dome
Animatronic.set_head_position(toy, 90.0)  # 90 degrees right

# Change stance
Animatronic.perform_leg_action(toy, R2LegActions.THREE_LEGS)

# Set LEDs (front = red, back = blue)
from spherov2.toy.r2d2 import R2D2
toy.set_all_leds_with_32_bit_mask(
    (1 << R2D2.LEDs.FRONT_RED) | (1 << R2D2.LEDs.BACK_BLUE),
    [255, 255]
)

# Play sound
IO.play_audio_file(toy, 1862, AudioPlaybackModes.PLAY_IMMEDIATELY)

# Play animation
Animatronic.play_animation(toy, 14)  # Excited
```

---

*Last updated: 2026-01-16*
