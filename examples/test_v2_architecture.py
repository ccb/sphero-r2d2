#!/usr/bin/env python3
"""
Test script for validating the new v2 architecture with a physical R2D2 robot.

Run this script with a powered-on R2D2 nearby:
    python examples/test_v2_architecture.py

Or specify a robot by name:
    python examples/test_v2_architecture.py --name D2-55E3
"""

import asyncio
import argparse
import sys

# Add parent to path for development
sys.path.insert(0, '.')

from r2d2 import R2D2, scan


async def test_scan():
    """Test BLE scanning."""
    print("\n=== Test: BLE Scanning ===")
    print("Scanning for R2D2 robots...")

    devices = await scan(timeout=5.0)

    if not devices:
        print("No R2D2 robots found!")
        return None

    print(f"Found {len(devices)} robot(s):")
    for d in devices:
        print(f"  - {d.name} ({d.address})")

    return devices[0]


async def test_connection(robot: R2D2):
    """Test basic connection."""
    print("\n=== Test: Connection ===")
    print(f"Connecting to {robot.name}...")

    await robot.connect()

    print(f"Connected: {robot.is_connected}")
    print(f"Name: {robot.name}")
    print(f"Address: {robot.address}")


async def test_battery(robot: R2D2):
    """Test battery info commands."""
    print("\n=== Test: Battery Info ===")

    voltage = await robot.get_battery_voltage()
    print(f"Battery voltage: {voltage:.2f}V")

    percentage = await robot.get_battery_percentage()
    print(f"Battery percentage: {percentage}%")

    state = await robot.get_battery_state()
    print(f"Battery state: {state.name}")


async def test_firmware(robot: R2D2):
    """Test firmware version command."""
    print("\n=== Test: Firmware Version ===")

    version = await robot.get_firmware_version()
    print(f"Firmware version: {version}")


async def test_leds(robot: R2D2):
    """Test LED controls."""
    print("\n=== Test: LEDs ===")

    print("Setting front LED to red...")
    await robot.leds.red()
    await asyncio.sleep(0.5)

    print("Setting front LED to green...")
    await robot.leds.green()
    await asyncio.sleep(0.5)

    print("Setting front LED to blue...")
    await robot.leds.blue()
    await asyncio.sleep(0.5)

    print("Setting front LED to white...")
    await robot.leds.white()
    await asyncio.sleep(0.5)

    print("Setting back LED to purple...")
    await robot.leds.set_back(128, 0, 255)
    await asyncio.sleep(0.5)

    print("Setting logic displays to full brightness...")
    await robot.leds.set_logic_displays(255)
    await asyncio.sleep(0.5)

    print("Turning off all LEDs...")
    await robot.leds.off()


async def test_dome(robot: R2D2):
    """Test dome rotation."""
    print("\n=== Test: Dome Rotation ===")

    print("Rotating dome to 90 degrees...")
    await robot.dome.set_position(90)
    await asyncio.sleep(1.0)

    print("Rotating dome to -90 degrees...")
    await robot.dome.set_position(-90)
    await asyncio.sleep(1.0)

    print("Centering dome...")
    await robot.dome.center()
    await asyncio.sleep(0.5)


async def test_stance(robot: R2D2):
    """Test stance changes."""
    print("\n=== Test: Stance ===")

    print("Setting tripod stance...")
    await robot.stance.set_tripod()
    await asyncio.sleep(2.0)

    print("Setting bipod stance...")
    await robot.stance.set_bipod()
    await asyncio.sleep(2.0)


async def test_audio(robot: R2D2):
    """Test audio playback."""
    print("\n=== Test: Audio ===")

    print("Playing happy sound...")
    await robot.audio.happy()
    await asyncio.sleep(2.0)

    print("Playing excited sound...")
    await robot.audio.excited()
    await asyncio.sleep(2.0)


async def test_drive(robot: R2D2):
    """Test basic movement (careful - robot will move!)."""
    print("\n=== Test: Drive ===")
    print("WARNING: Robot will move! Ensure clear area.")
    await asyncio.sleep(1.0)

    print("Rolling forward briefly...")
    await robot.drive.roll(heading=0, speed=50, duration=0.5)
    await asyncio.sleep(1.0)

    print("Stopping...")
    await robot.drive.stop()


async def main():
    parser = argparse.ArgumentParser(description="Test v2 architecture with physical R2D2")
    parser.add_argument("--name", help="Robot name (e.g., D2-55E3)")
    parser.add_argument("--skip-drive", action="store_true", help="Skip drive tests")
    parser.add_argument("--skip-stance", action="store_true", help="Skip stance tests")
    args = parser.parse_args()

    print("=" * 50)
    print("R2D2 v2 Architecture Test")
    print("=" * 50)

    # Scan for robots
    device = await test_scan()
    if not device and not args.name:
        print("\nNo robots found and no name specified. Exiting.")
        return

    # Create and connect to robot
    try:
        async with R2D2(device=device, name=args.name) as robot:
            # Run tests
            await test_battery(robot)
            await test_firmware(robot)
            await test_leds(robot)
            await test_dome(robot)
            await test_audio(robot)

            if not args.skip_stance:
                await test_stance(robot)

            if not args.skip_drive:
                await test_drive(robot)

            print("\n" + "=" * 50)
            print("All tests completed!")
            print("=" * 50)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code or 0)
