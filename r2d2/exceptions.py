"""
Exception hierarchy for R2D2 library.

All exceptions inherit from R2D2Error for easy catching.
"""

from typing import Optional


class R2D2Error(Exception):
    """Base exception for all R2D2 errors."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class ConnectionError(R2D2Error):
    """Failed to connect to robot."""
    pass


class DisconnectedError(R2D2Error):
    """Robot disconnected unexpectedly."""
    pass


class TimeoutError(R2D2Error):
    """Operation timed out."""

    def __init__(self, message: str, timeout: float, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.timeout = timeout


class CommandError(R2D2Error):
    """Command execution failed."""

    def __init__(self, message: str, error_code: int, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.error_code = error_code


class ProtocolError(R2D2Error):
    """Protocol encoding/decoding error."""
    pass


class PacketError(ProtocolError):
    """Invalid packet structure."""
    pass


class ChecksumError(ProtocolError):
    """Packet checksum mismatch."""
    pass


class ScanError(R2D2Error):
    """Robot scanning/discovery error."""
    pass


class NotFoundError(ScanError):
    """Robot not found during scan."""

    def __init__(self, name: Optional[str] = None, timeout: float = 0):
        if name:
            message = f"Robot '{name}' not found within {timeout}s"
        else:
            message = f"No R2D2 robots found within {timeout}s"
        super().__init__(message)
        self.name = name
        self.timeout = timeout


class BusyError(R2D2Error):
    """Robot is busy and cannot execute command."""
    pass


class LowBatteryError(R2D2Error):
    """Battery too low for operation."""

    def __init__(self, voltage: float, required: float):
        message = f"Battery voltage {voltage}V too low (requires {required}V)"
        super().__init__(message)
        self.voltage = voltage
        self.required = required
