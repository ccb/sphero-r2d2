"""
Protocol constants for Sphero V2 protocol.
"""

from enum import IntEnum, IntFlag

# Packet framing bytes
SOP = 0x8D  # Start of Packet
EOP = 0xD8  # End of Packet
ESCAPE = 0xAB  # Escape byte

# Escaped versions
ESCAPED_ESCAPE = 0x23  # 0xAB -> 0xAB 0x23
ESCAPED_SOP = 0x05     # 0x8D -> 0xAB 0x05
ESCAPED_EOP = 0x50     # 0xD8 -> 0xAB 0x50


class DeviceId(IntEnum):
    """Device IDs for R2D2 subsystems."""
    CORE = 0x00
    BOOTLOADER = 0x01
    POWER = 0x13
    DRIVE = 0x16
    ANIMATRONIC = 0x17
    SENSOR = 0x18
    IO = 0x1A
    CONNECTION = 0x19
    SYSTEM_INFO = 0x11
    API_AND_SHELL = 0x10
    FIRMWARE = 0x1F


class PowerCommand(IntEnum):
    """Command IDs for Power device (0x13)."""
    ENTER_DEEP_SLEEP = 0x00
    SLEEP = 0x01
    GET_BATTERY_VOLTAGE = 0x03
    GET_BATTERY_STATE = 0x04
    ENABLE_BATTERY_STATE_NOTIFY = 0x05
    FORCE_BATTERY_REFRESH = 0x0C
    WAKE = 0x0D
    GET_BATTERY_PERCENTAGE = 0x10
    GET_BATTERY_VOLTAGE_STATE = 0x17
    ENABLE_BATTERY_VOLTAGE_STATE_NOTIFY = 0x1B
    GET_CHARGER_STATE = 0x1F
    GET_BATTERY_VOLTAGE_IN_VOLTS = 0x25
    GET_BATTERY_VOLTAGE_STATE_THRESHOLDS = 0x26


class DriveCommand(IntEnum):
    """Command IDs for Drive device (0x16)."""
    SET_RAW_MOTORS = 0x01
    RESET_YAW = 0x06
    DRIVE_WITH_HEADING = 0x07
    GENERIC_RAW_MOTOR = 0x0B
    SET_STABILIZATION = 0x0C
    SET_CONTROL_SYSTEM_TYPE = 0x0E
    SET_CUSTOM_CONTROL_SYSTEM_TIMEOUT = 0x22
    ENABLE_MOTOR_STALL_NOTIFY = 0x25
    ENABLE_MOTOR_FAULT_NOTIFY = 0x27
    GET_MOTOR_FAULT_STATE = 0x29


class AnimatronicCommand(IntEnum):
    """Command IDs for Animatronic device (0x17)."""
    PLAY_ANIMATION = 0x05
    PERFORM_LEG_ACTION = 0x0D
    SET_HEAD_POSITION = 0x0F
    GET_HEAD_POSITION = 0x14
    SET_LEG_POSITION = 0x15
    GET_LEG_POSITION = 0x16
    GET_LEG_ACTION = 0x25
    ENABLE_LEG_ACTION_NOTIFY = 0x2A
    STOP_ANIMATION = 0x2B
    ENABLE_IDLE_ANIMATIONS = 0x2C
    ENABLE_TROPHY_MODE = 0x2D
    GET_TROPHY_MODE_ENABLED = 0x2E
    ENABLE_HEAD_RESET_NOTIFY = 0x39


class IOCommand(IntEnum):
    """Command IDs for IO device (0x1A)."""
    SET_LED = 0x04
    PLAY_AUDIO_FILE = 0x07
    SET_AUDIO_VOLUME = 0x08
    GET_AUDIO_VOLUME = 0x09
    STOP_ALL_AUDIO = 0x0A
    SET_ALL_LEDS_16_BIT_MASK = 0x0E
    START_IDLE_LED_ANIMATION = 0x19
    SET_ALL_LEDS_32_BIT_MASK = 0x1A
    SET_ALL_LEDS_8_BIT_MASK = 0x1C
    RELEASE_LED_REQUESTS = 0x4E


class SensorCommand(IntEnum):
    """Command IDs for Sensor device (0x18)."""
    SET_SENSOR_STREAMING_MASK = 0x00
    GET_SENSOR_STREAMING_MASK = 0x01
    SET_EXTENDED_SENSOR_STREAMING_MASK = 0x0C
    GET_EXTENDED_SENSOR_STREAMING_MASK = 0x0D
    ENABLE_GYRO_MAX_NOTIFY = 0x0F
    CONFIGURE_COLLISION_DETECTION = 0x11
    ENABLE_COLLISION_DETECTED_NOTIFY = 0x14
    CONFIGURE_STREAMING_SERVICE = 0x39
    START_STREAMING_SERVICE = 0x3A
    STOP_STREAMING_SERVICE = 0x3B
    CLEAR_STREAMING_SERVICE = 0x3C


class SystemInfoCommand(IntEnum):
    """Command IDs for SystemInfo device (0x11)."""
    GET_MAIN_APP_VERSION = 0x00
    GET_BOOTLOADER_VERSION = 0x01
    GET_BOARD_REVISION = 0x03
    GET_MAC_ADDRESS = 0x06
    GET_STATS_ID = 0x13
    GET_PROCESSOR_NAME = 0x1F
    GET_SKU = 0x38


class CoreCommand(IntEnum):
    """Command IDs for Core device (0x00)."""
    PING = 0x00
    GET_API_PROTOCOL_VERSION = 0x01


class ErrorCode(IntEnum):
    """Error codes returned in response packets."""
    SUCCESS = 0x00
    BAD_DEVICE_ID = 0x01
    BAD_COMMAND_ID = 0x02
    NOT_YET_IMPLEMENTED = 0x03
    COMMAND_IS_RESTRICTED = 0x04
    BAD_DATA_LENGTH = 0x05
    COMMAND_FAILED = 0x06
    BAD_PARAMETER_VALUE = 0x07
    BUSY = 0x08
    BAD_TARGET_ID = 0x09
    TARGET_UNAVAILABLE = 0x0A

    @property
    def is_success(self) -> bool:
        return self == ErrorCode.SUCCESS

    @property
    def message(self) -> str:
        messages = {
            ErrorCode.SUCCESS: "Success",
            ErrorCode.BAD_DEVICE_ID: "Bad device ID",
            ErrorCode.BAD_COMMAND_ID: "Bad command ID",
            ErrorCode.NOT_YET_IMPLEMENTED: "Not yet implemented",
            ErrorCode.COMMAND_IS_RESTRICTED: "Command is restricted",
            ErrorCode.BAD_DATA_LENGTH: "Bad data length",
            ErrorCode.COMMAND_FAILED: "Command failed",
            ErrorCode.BAD_PARAMETER_VALUE: "Bad parameter value",
            ErrorCode.BUSY: "Robot is busy",
            ErrorCode.BAD_TARGET_ID: "Bad target ID",
            ErrorCode.TARGET_UNAVAILABLE: "Target unavailable",
        }
        return messages.get(self, f"Unknown error {self.value}")


class PacketFlags(IntFlag):
    """Flags byte in V2 packets."""
    IS_RESPONSE = 0x01
    REQUESTS_RESPONSE = 0x02
    REQUESTS_ONLY_ERROR_RESPONSE = 0x04
    IS_ACTIVITY = 0x08
    HAS_TARGET_ID = 0x10
    HAS_SOURCE_ID = 0x20
    UNUSED = 0x40
    EXTENDED_FLAGS = 0x80


class DriveFlags(IntFlag):
    """Flags for drive commands."""
    FORWARD = 0x00
    BACKWARD = 0x01
    TURBO = 0x02
    FAST_TURN = 0x04
    LEFT_DIRECTION = 0x08
    RIGHT_DIRECTION = 0x10
    ENABLE_DRIFT = 0x20


class RawMotorMode(IntEnum):
    """Motor modes for raw motor control."""
    OFF = 0
    FORWARD = 1
    REVERSE = 2


class LegAction(IntEnum):
    """Leg action commands."""
    STOP = 0
    TRIPOD = 1   # Three legs (deploy third leg)
    BIPOD = 2    # Two legs (retract third leg)
    WADDLE = 3   # Waddle mode


class LegState(IntEnum):
    """Current leg state."""
    UNKNOWN = 0
    TRIPOD = 1
    BIPOD = 2
    WADDLE = 3
    TRANSITIONING = 4


class BatteryState(IntEnum):
    """Battery state values."""
    CHARGED = 0
    CHARGING = 1
    NOT_CHARGING = 2
    OK = 3
    LOW = 4
    CRITICAL = 5
    UNKNOWN = 255


class AudioPlaybackMode(IntEnum):
    """Audio playback modes."""
    PLAY_IMMEDIATELY = 0
    PLAY_ONLY_IF_NOT_PLAYING = 1
    PLAY_AFTER_CURRENT = 2


class StabilizationMode(IntEnum):
    """Stabilization control modes."""
    DISABLED = 0
    FULL = 1
    PITCH_ONLY = 2
    ROLL_ONLY = 3
    YAW_ONLY = 4
    SPEED_AND_YAW = 5


# R2D2 LED indices
class LED(IntEnum):
    """R2D2 LED indices for the LED mask."""
    FRONT_RED = 0
    FRONT_GREEN = 1
    FRONT_BLUE = 2
    LOGIC_DISPLAYS = 3
    BACK_RED = 4
    BACK_GREEN = 5
    BACK_BLUE = 6
    HOLO_PROJECTOR = 7


# BLE UUIDs
API_V2_UUID = "00010002-574f-4f20-5370-6865726f2121"
HANDSHAKE_UUID = "00020005-574f-4f20-5370-6865726f2121"
HANDSHAKE_DATA = b"usetheforce...band"

# Timing
COMMAND_SAFE_INTERVAL = 0.12  # 120ms between commands for R2D2
DEFAULT_TIMEOUT = 10.0  # Default command timeout
