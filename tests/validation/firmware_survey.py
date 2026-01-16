#!/usr/bin/env python3
"""
R2D2 Firmware Survey Script

This script connects to an R2D2 robot and collects detailed information
about its firmware, hardware, and capabilities for documentation purposes.

Usage:
    python firmware_survey.py [robot_name]

    If no robot_name is provided, it will scan for available R2D2 robots.

Example:
    python firmware_survey.py D2-55E3
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from spherov2 import scanner
from spherov2.toy.r2d2 import R2D2
from spherov2.commands.system_info import SystemInfo
from spherov2.commands.power import Power


def format_version(version):
    """Format a Version named tuple as a string."""
    return f"{version.major}.{version.minor}.{version.revision}"


def format_mac(mac_bytes):
    """Format MAC address bytes as a readable string."""
    return ':'.join(f'{b:02X}' for b in mac_bytes)


def collect_robot_info(toy):
    """Collect all available information from the robot."""
    info = {
        'survey_timestamp': datetime.now().isoformat(),
        'robot_name': toy.name,
        'robot_address': toy.address,
    }

    # System Info
    print("Collecting system information...")

    try:
        version = toy.get_main_app_version()
        info['main_app_version'] = format_version(version)
        print(f"  Main App Version: {info['main_app_version']}")
    except Exception as e:
        info['main_app_version'] = f"ERROR: {e}"
        print(f"  Main App Version: ERROR - {e}")

    try:
        version = toy.get_bootloader_version()
        info['bootloader_version'] = format_version(version)
        print(f"  Bootloader Version: {info['bootloader_version']}")
    except Exception as e:
        info['bootloader_version'] = f"ERROR: {e}"
        print(f"  Bootloader Version: ERROR - {e}")

    try:
        info['board_revision'] = toy.get_board_revision()
        print(f"  Board Revision: {info['board_revision']}")
    except Exception as e:
        info['board_revision'] = f"ERROR: {e}"
        print(f"  Board Revision: ERROR - {e}")

    try:
        mac = toy.get_mac_address()
        info['mac_address'] = format_mac(mac)
        print(f"  MAC Address: {info['mac_address']}")
    except Exception as e:
        info['mac_address'] = f"ERROR: {e}"
        print(f"  MAC Address: ERROR - {e}")

    try:
        info['processor_name'] = toy.get_processor_name().decode('utf-8')
        print(f"  Processor Name: {info['processor_name']}")
    except Exception as e:
        info['processor_name'] = f"ERROR: {e}"
        print(f"  Processor Name: ERROR - {e}")

    try:
        info['stats_id'] = toy.get_stats_id().hex()
        print(f"  Stats ID: {info['stats_id']}")
    except Exception as e:
        info['stats_id'] = f"ERROR: {e}"
        print(f"  Stats ID: ERROR - {e}")

    try:
        sku = toy.get_three_character_sku()
        info['three_char_sku'] = sku.decode('utf-8') if isinstance(sku, bytes) else str(sku)
        print(f"  Three Char SKU: {info['three_char_sku']}")
    except Exception as e:
        info['three_char_sku'] = f"ERROR: {e}"
        print(f"  Three Char SKU: ERROR - {e}")

    # Secondary MCU info (R2D2 has two processors)
    print("\nCollecting secondary MCU information...")

    try:
        version = toy.get_secondary_main_app_version()
        info['secondary_main_app_version'] = format_version(version)
        print(f"  Secondary Main App Version: {info['secondary_main_app_version']}")
    except Exception as e:
        info['secondary_main_app_version'] = f"ERROR: {e}"
        print(f"  Secondary Main App Version: ERROR - {e}")

    try:
        version = toy.get_secondary_mcu_bootloader_version()
        info['secondary_bootloader_version'] = format_version(version)
        print(f"  Secondary Bootloader Version: {info['secondary_bootloader_version']}")
    except Exception as e:
        info['secondary_bootloader_version'] = f"ERROR: {e}"
        print(f"  Secondary Bootloader Version: ERROR - {e}")

    # Power/Battery Info
    print("\nCollecting power information...")

    try:
        info['battery_voltage'] = toy.get_battery_voltage()
        print(f"  Battery Voltage: {info['battery_voltage']}V")
    except Exception as e:
        info['battery_voltage'] = f"ERROR: {e}"
        print(f"  Battery Voltage: ERROR - {e}")

    try:
        state = toy.get_battery_state()
        info['battery_state'] = state.name if hasattr(state, 'name') else str(state)
        print(f"  Battery State: {info['battery_state']}")
    except Exception as e:
        info['battery_state'] = f"ERROR: {e}"
        print(f"  Battery State: ERROR - {e}")

    try:
        voltage_state = toy.get_battery_voltage_state()
        info['battery_voltage_state'] = voltage_state.name if hasattr(voltage_state, 'name') else str(voltage_state)
        print(f"  Battery Voltage State: {info['battery_voltage_state']}")
    except Exception as e:
        info['battery_voltage_state'] = f"ERROR: {e}"
        print(f"  Battery Voltage State: ERROR - {e}")

    # R2D2 Specific Info
    print("\nCollecting R2D2-specific information...")

    try:
        info['head_position'] = toy.get_head_position()
        print(f"  Current Head Position: {info['head_position']}°")
    except Exception as e:
        info['head_position'] = f"ERROR: {e}"
        print(f"  Current Head Position: ERROR - {e}")

    try:
        leg_action = toy.get_leg_action()
        info['current_leg_action'] = leg_action.name if hasattr(leg_action, 'name') else str(leg_action)
        print(f"  Current Leg Action: {info['current_leg_action']}")
    except Exception as e:
        info['current_leg_action'] = f"ERROR: {e}"
        print(f"  Current Leg Action: ERROR - {e}")

    try:
        info['leg_position'] = toy.get_leg_position()
        print(f"  Current Leg Position: {info['leg_position']}")
    except Exception as e:
        info['leg_position'] = f"ERROR: {e}"
        print(f"  Current Leg Position: ERROR - {e}")

    # Metadata
    info['toy_type'] = 'R2D2'
    info['led_count'] = len(R2D2.LEDs)
    info['sound_count'] = len(R2D2.Audio)
    info['animation_count'] = len(R2D2.Animations)

    print(f"\n  LED Count: {info['led_count']}")
    print(f"  Sound Count: {info['sound_count']}")
    print(f"  Animation Count: {info['animation_count']}")

    return info


def scan_for_robots():
    """Scan for available R2D2 robots."""
    print("Scanning for R2D2 robots...")
    toys = scanner.find_toys(toy_types=[R2D2])

    if not toys:
        print("No R2D2 robots found. Make sure your robot is:")
        print("  1. Powered on (not on charger or just off charger)")
        print("  2. Bluetooth is enabled on this computer")
        print("  3. Robot is in pairing range")
        return None

    print(f"\nFound {len(toys)} R2D2 robot(s):")
    for toy in toys:
        print(f"  - {toy.name} ({toy.address})")

    return toys


def main():
    robot_name = sys.argv[1] if len(sys.argv) > 1 else None

    if robot_name:
        print(f"Looking for robot: {robot_name}")
        toy = scanner.find_toy(toy_name=robot_name, toy_types=[R2D2])
        if not toy:
            print(f"Robot '{robot_name}' not found.")
            toys = scan_for_robots()
            if toys:
                print("\nTry specifying one of the robot names above.")
            return 1
    else:
        toys = scan_for_robots()
        if not toys:
            return 1
        toy = toys[0]
        print(f"\nUsing first robot found: {toy.name}")

    print(f"\nConnecting to {toy.name}...")

    try:
        with toy:
            print("Connected!\n")
            print("=" * 60)
            print(f"FIRMWARE SURVEY: {toy.name}")
            print("=" * 60)

            info = collect_robot_info(toy)

            # Save results
            output_dir = Path(__file__).parent / "results"
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"firmware_survey_{toy.name}_{timestamp}.json"

            with open(output_file, 'w') as f:
                json.dump(info, f, indent=2, default=str)

            print("\n" + "=" * 60)
            print(f"Survey complete! Results saved to:")
            print(f"  {output_file}")
            print("=" * 60)

            # Also append to master survey file
            master_file = output_dir / "firmware_survey_all.json"
            all_surveys = []
            if master_file.exists():
                with open(master_file, 'r') as f:
                    all_surveys = json.load(f)
            all_surveys.append(info)
            with open(master_file, 'w') as f:
                json.dump(all_surveys, f, indent=2, default=str)

            print(f"\nAlso appended to master survey: {master_file}")

    except Exception as e:
        print(f"\nError during survey: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
