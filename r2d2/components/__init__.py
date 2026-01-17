"""
Robot components.

Each component provides high-level control over a specific robot subsystem.
"""

from r2d2.components.drive import DriveComponent
from r2d2.components.dome import DomeComponent
from r2d2.components.stance import StanceComponent
from r2d2.components.leds import LEDComponent
from r2d2.components.audio import AudioComponent
from r2d2.components.sensors import SensorComponent

__all__ = [
    "DriveComponent",
    "DomeComponent",
    "StanceComponent",
    "LEDComponent",
    "AudioComponent",
    "SensorComponent",
]
