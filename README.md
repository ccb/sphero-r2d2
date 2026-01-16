# sphero-r2d2

A Python library for controlling Sphero R2-D2 robots via Bluetooth Low Energy (BLE).

## Overview

This library provides a modern, async-first Python API for the discontinued Sphero R2-D2 robot. It's designed to reliably control large fleets of R2D2 units for educational and research purposes.

**Status**: Under active development (Phase 0 - Validation)

## Features

- Full R2D2 control: movement, dome rotation, leg stance, LEDs, sounds, animations
- Sensor streaming: accelerometer, gyroscope, orientation, head angle
- Async-first design with sync wrappers for convenience
- Fleet management for controlling multiple robots
- Cross-platform: macOS, Linux, Windows (via Bleak)

## Installation

```bash
# Clone the repository
git clone https://github.com/ccb/sphero-r2d2.git
cd sphero-r2d2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Quick Start

```python
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.toy.r2d2 import R2D2

# Find and connect to an R2D2
toy = scanner.find_toy(toy_types=[R2D2])

with SpheroEduAPI(toy) as r2:
    # Move forward
    r2.roll(0, 100, 2)  # heading=0, speed=100, duration=2s

    # Rotate dome
    r2.set_dome_position(90)

    # Change LED color
    r2.set_main_led(255, 0, 0)  # Red

    # Play a sound
    r2.play_sound(R2D2.Audio.R2_EXCITED_1)
```

## R2D2 Capabilities

| Feature | Description |
|---------|-------------|
| **Movement** | Roll, turn, raw motor control |
| **Dome** | Rotate head -160° to 180° |
| **Stance** | Bipod (2 legs), Tripod (3 legs), Waddle |
| **LEDs** | Front RGB, Back RGB, Logic Displays, Holo Projector |
| **Audio** | 388 sound effects |
| **Animations** | 51 built-in animations |
| **Sensors** | Accelerometer, Gyroscope, Orientation, Head angle |

## Documentation

- [Improvement Plan](SPHEROV2_IMPROVEMENT_PLAN.md) - Development roadmap
- [Validation Tests](tests/validation/README.md) - Hardware testing scripts

## Requirements

- Python 3.9+
- Bluetooth 4.0+ adapter
- Sphero R2-D2 robot with firmware 7.x

## Tested Firmware Versions

| Robot | Main App | Bootloader | Board Rev | Status |
|-------|----------|------------|-----------|--------|
| D2-55E3 | 7.0.101 | 4.1.18 | 3 | Working |

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

This project builds on the work of:
- [spherov2.py](https://github.com/artificial-intelligence-class/spherov2.py) - Original reverse-engineered API
- [Bleak](https://github.com/hbldh/bleak) - Cross-platform BLE library
- Sphero's discontinued Star Wars droids line

## Contributing

Contributions welcome! Please see the [Improvement Plan](SPHEROV2_IMPROVEMENT_PLAN.md) for current development priorities.
