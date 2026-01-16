# R2D2 Validation Tests

This directory contains scripts to validate R2D2 compatibility and gather
firmware information across multiple robots.

## Prerequisites

1. Install the spherov2 library:
   ```bash
   cd /path/to/spherov2-py
   pip install -e .
   ```

2. Ensure Bluetooth is enabled on your computer

3. Power on your R2D2 (off the charger)

## Scripts

### firmware_survey.py

Collects detailed firmware and hardware information from an R2D2 robot.
Run this on each robot to build a compatibility database.

```bash
# Scan for robots and survey the first one found
python firmware_survey.py

# Survey a specific robot by name
python firmware_survey.py D2-55E3
```

Results are saved to:
- `results/firmware_survey_<name>_<timestamp>.json` - Individual survey
- `results/firmware_survey_all.json` - Master file with all surveys

### r2d2_command_tests.py

Tests all R2D2 commands to verify they work correctly with the hardware.

```bash
# Run all tests on first robot found
python r2d2_command_tests.py

# Run tests on a specific robot
python r2d2_command_tests.py D2-55E3

# Quick mode (skip audio/animation tests)
python r2d2_command_tests.py D2-55E3 --quick

# Interactive mode (prompt before each test category)
python r2d2_command_tests.py D2-55E3 --interactive
```

**WARNING**: Drive tests will move the robot! Ensure a clear area.

Results are saved to `results/command_tests_<name>_<timestamp>.json`

## Test Categories

1. **Connection** - Basic connectivity and info retrieval
2. **Dome Control** - Head/dome positioning (-160° to 180°)
3. **Stance Control** - Leg actions (bipod, tripod, waddle)
4. **LED Control** - All 8 LEDs (front RGB, back RGB, logic, holo)
5. **Drive Control** - Movement commands (requires clear space!)
6. **Audio** - Sound playback and volume control
7. **Animations** - Built-in animation playback
8. **Sensors** - Sensor streaming and collision detection

## Results Directory

Test results are saved as JSON files in the `results/` subdirectory:

```
results/
├── firmware_survey_D2-55E3_20260116_143022.json
├── firmware_survey_all.json
└── command_tests_D2-55E3_20260116_143530.json
```

## Multi-Robot Testing

To survey your entire fleet:

```bash
# Survey each robot (repeat for each robot)
python firmware_survey.py D2-XXXX

# After surveying all robots, the master file contains all data:
cat results/firmware_survey_all.json
```

## Troubleshooting

**Robot not found:**
- Ensure robot is powered on (not on charger)
- Make sure Bluetooth is enabled
- Try moving closer to the robot
- Check that no other app is connected to the robot

**Command timeouts:**
- Try power cycling the robot
- Ensure good Bluetooth signal
- Some commands take time (leg transitions ~2 seconds)

**Drive tests fail:**
- Robot must be in tripod stance to roll
- Ensure battery is adequately charged
