#!/usr/bin/env python3
"""
R2D2 Command Compatibility Test Script

This script tests all R2D2 commands to verify they work correctly
with the physical hardware. It's designed to be run on multiple
R2D2 units to identify any firmware-specific differences.

Usage:
    python r2d2_command_tests.py [robot_name] [--quick] [--interactive]

Options:
    --quick       Run only essential tests (skip sounds/animations)
    --interactive Prompt before each test category

Example:
    python r2d2_command_tests.py D2-55E3
    python r2d2_command_tests.py D2-55E3 --quick
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from spherov2 import scanner
from spherov2.toy.r2d2 import R2D2
from spherov2.commands.animatronic import R2LegActions


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class TestCategory:
    """Results for a category of tests."""
    name: str
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)


class R2D2Tester:
    """Test harness for R2D2 robots."""

    def __init__(self, toy: R2D2, quick: bool = False, interactive: bool = False):
        self.toy = toy
        self.quick = quick
        self.interactive = interactive
        self.categories: List[TestCategory] = []

    def run_test(self, name: str, test_func, category: TestCategory) -> TestResult:
        """Run a single test and record the result."""
        print(f"    Testing: {name}...", end=" ", flush=True)
        start = time.time()

        try:
            notes = test_func()
            duration = (time.time() - start) * 1000
            result = TestResult(name=name, passed=True, duration_ms=duration, notes=notes)
            print(f"PASS ({duration:.0f}ms)")
        except Exception as e:
            duration = (time.time() - start) * 1000
            result = TestResult(name=name, passed=False, duration_ms=duration, error=str(e))
            print(f"FAIL: {e}")

        category.results.append(result)
        return result

    def prompt_continue(self, category_name: str) -> bool:
        """Prompt user to continue with next category."""
        if not self.interactive:
            return True
        response = input(f"\n  Run {category_name} tests? [Y/n]: ").strip().lower()
        return response in ('', 'y', 'yes')

    def test_connection(self) -> TestCategory:
        """Test basic connection and info retrieval."""
        category = TestCategory(name="Connection")
        print("\n  [Connection Tests]")

        self.run_test("ping", lambda: self.toy.ping(), category)
        self.run_test("get_main_app_version", lambda: str(self.toy.get_main_app_version()), category)
        self.run_test("get_bootloader_version", lambda: str(self.toy.get_bootloader_version()), category)
        self.run_test("get_battery_voltage", lambda: f"{self.toy.get_battery_voltage()}V", category)
        self.run_test("get_battery_state", lambda: str(self.toy.get_battery_state()), category)

        self.categories.append(category)
        return category

    def test_dome(self) -> TestCategory:
        """Test dome/head position control."""
        category = TestCategory(name="Dome Control")
        print("\n  [Dome Control Tests]")

        # Get initial position
        self.run_test("get_head_position", lambda: f"{self.toy.get_head_position()}°", category)

        # Test setting positions
        def set_head_center():
            self.toy.set_head_position(0)
            time.sleep(0.5)
            pos = self.toy.get_head_position()
            assert -5 < pos < 5, f"Expected ~0°, got {pos}°"
            return f"Set to 0°, read {pos}°"

        def set_head_right():
            self.toy.set_head_position(90)
            time.sleep(0.5)
            pos = self.toy.get_head_position()
            assert 80 < pos < 100, f"Expected ~90°, got {pos}°"
            return f"Set to 90°, read {pos}°"

        def set_head_left():
            self.toy.set_head_position(-90)
            time.sleep(0.5)
            pos = self.toy.get_head_position()
            assert -100 < pos < -80, f"Expected ~-90°, got {pos}°"
            return f"Set to -90°, read {pos}°"

        def set_head_max_right():
            self.toy.set_head_position(180)
            time.sleep(0.5)
            pos = self.toy.get_head_position()
            return f"Set to 180°, read {pos}°"

        def set_head_max_left():
            self.toy.set_head_position(-160)
            time.sleep(0.5)
            pos = self.toy.get_head_position()
            return f"Set to -160°, read {pos}°"

        self.run_test("set_head_position(0)", set_head_center, category)
        self.run_test("set_head_position(90)", set_head_right, category)
        self.run_test("set_head_position(-90)", set_head_left, category)
        self.run_test("set_head_position(180)", set_head_max_right, category)
        self.run_test("set_head_position(-160)", set_head_max_left, category)

        # Return to center
        self.toy.set_head_position(0)
        time.sleep(0.5)

        self.categories.append(category)
        return category

    def test_stance(self) -> TestCategory:
        """Test leg/stance control."""
        category = TestCategory(name="Stance Control")
        print("\n  [Stance Control Tests]")

        self.run_test("get_leg_action", lambda: str(self.toy.get_leg_action()), category)
        self.run_test("get_leg_position", lambda: f"{self.toy.get_leg_position()}", category)

        def set_tripod():
            self.toy.perform_leg_action(R2LegActions.THREE_LEGS)
            time.sleep(2)  # Leg transitions take time
            action = self.toy.get_leg_action()
            return f"Action: {action}"

        def set_bipod():
            self.toy.perform_leg_action(R2LegActions.TWO_LEGS)
            time.sleep(2)
            action = self.toy.get_leg_action()
            return f"Action: {action}"

        def test_waddle():
            # Need to be in bipod for waddle
            self.toy.perform_leg_action(R2LegActions.TWO_LEGS)
            time.sleep(2)
            self.toy.perform_leg_action(R2LegActions.WADDLE)
            time.sleep(2)
            self.toy.perform_leg_action(R2LegActions.STOP)
            time.sleep(1)
            return "Waddle test complete"

        self.run_test("perform_leg_action(THREE_LEGS)", set_tripod, category)
        self.run_test("perform_leg_action(TWO_LEGS)", set_bipod, category)

        if not self.quick:
            self.run_test("perform_leg_action(WADDLE)", test_waddle, category)

        # Leave in tripod for drive tests
        self.toy.perform_leg_action(R2LegActions.THREE_LEGS)
        time.sleep(2)

        self.categories.append(category)
        return category

    def test_leds(self) -> TestCategory:
        """Test LED control."""
        category = TestCategory(name="LED Control")
        print("\n  [LED Control Tests]")

        from spherov2.commands.io import IO

        def test_front_led_red():
            self.toy.set_all_leds_with_16_bit_mask(0x07, [255, 0, 0])
            time.sleep(0.3)
            return "Front LED red"

        def test_front_led_green():
            self.toy.set_all_leds_with_16_bit_mask(0x07, [0, 255, 0])
            time.sleep(0.3)
            return "Front LED green"

        def test_front_led_blue():
            self.toy.set_all_leds_with_16_bit_mask(0x07, [0, 0, 255])
            time.sleep(0.3)
            return "Front LED blue"

        def test_back_led():
            self.toy.set_all_leds_with_16_bit_mask(0x70, [255, 255, 0])
            time.sleep(0.3)
            return "Back LED yellow"

        def test_logic_displays():
            self.toy.set_all_leds_with_16_bit_mask(0x08, [255])
            time.sleep(0.5)
            self.toy.set_all_leds_with_16_bit_mask(0x08, [0])
            return "Logic displays toggled"

        def test_holo_projector():
            self.toy.set_all_leds_with_16_bit_mask(0x80, [255])
            time.sleep(0.5)
            self.toy.set_all_leds_with_16_bit_mask(0x80, [0])
            return "Holo projector toggled"

        def test_all_leds_off():
            self.toy.set_all_leds_with_16_bit_mask(0xFF, [0, 0, 0, 0, 0, 0, 0, 0])
            return "All LEDs off"

        self.run_test("front_led_red", test_front_led_red, category)
        self.run_test("front_led_green", test_front_led_green, category)
        self.run_test("front_led_blue", test_front_led_blue, category)
        self.run_test("back_led", test_back_led, category)
        self.run_test("logic_displays", test_logic_displays, category)
        self.run_test("holo_projector", test_holo_projector, category)
        self.run_test("all_leds_off", test_all_leds_off, category)

        self.categories.append(category)
        return category

    def test_drive(self) -> TestCategory:
        """Test drive/movement control."""
        category = TestCategory(name="Drive Control")
        print("\n  [Drive Control Tests]")
        print("    WARNING: Robot will move! Ensure clear area.")

        if self.interactive:
            if input("    Continue with drive tests? [y/N]: ").strip().lower() != 'y':
                print("    Skipping drive tests.")
                self.categories.append(category)
                return category

        def test_reset_yaw():
            self.toy.reset_yaw()
            return "Yaw reset"

        def test_drive_forward():
            self.toy.drive_with_heading(50, 0, 0)  # speed, heading, flags
            time.sleep(0.5)
            self.toy.drive_with_heading(0, 0, 0)  # stop
            return "Drove forward briefly"

        def test_drive_backward():
            self.toy.drive_with_heading(50, 180, 0)
            time.sleep(0.5)
            self.toy.drive_with_heading(0, 0, 0)
            return "Drove backward briefly"

        def test_turn_right():
            self.toy.drive_with_heading(0, 90, 0)
            time.sleep(0.5)
            return "Turned right"

        def test_turn_left():
            self.toy.drive_with_heading(0, 270, 0)
            time.sleep(0.5)
            return "Turned left"

        def test_stabilization():
            self.toy.set_stabilization(True)
            time.sleep(0.2)
            self.toy.set_stabilization(False)
            time.sleep(0.2)
            self.toy.set_stabilization(True)
            return "Stabilization toggled"

        self.run_test("reset_yaw", test_reset_yaw, category)
        self.run_test("drive_forward", test_drive_forward, category)
        self.run_test("drive_backward", test_drive_backward, category)
        self.run_test("turn_right", test_turn_right, category)
        self.run_test("turn_left", test_turn_left, category)
        self.run_test("stabilization", test_stabilization, category)

        self.categories.append(category)
        return category

    def test_audio(self) -> TestCategory:
        """Test audio playback."""
        category = TestCategory(name="Audio")
        print("\n  [Audio Tests]")

        if self.quick:
            print("    Skipping audio tests (--quick mode)")
            self.categories.append(category)
            return category

        def test_play_sound():
            self.toy.play_audio_file(R2D2.Audio.R2_POSITIVE_1, 0)
            time.sleep(1)
            return "Played R2_POSITIVE_1"

        def test_play_sound_2():
            self.toy.play_audio_file(R2D2.Audio.R2_EXCITED_1, 0)
            time.sleep(1)
            return "Played R2_EXCITED_1"

        def test_get_volume():
            vol = self.toy.get_audio_volume()
            return f"Volume: {vol}"

        def test_set_volume():
            original = self.toy.get_audio_volume()
            self.toy.set_audio_volume(200)
            time.sleep(0.1)
            self.toy.set_audio_volume(original)
            return f"Volume set/restored: {original}"

        def test_stop_audio():
            self.toy.stop_all_audio()
            return "Audio stopped"

        self.run_test("get_audio_volume", test_get_volume, category)
        self.run_test("set_audio_volume", test_set_volume, category)
        self.run_test("play_audio_file", test_play_sound, category)
        self.run_test("play_audio_file_2", test_play_sound_2, category)
        self.run_test("stop_all_audio", test_stop_audio, category)

        self.categories.append(category)
        return category

    def test_animations(self) -> TestCategory:
        """Test animation playback."""
        category = TestCategory(name="Animations")
        print("\n  [Animation Tests]")

        if self.quick:
            print("    Skipping animation tests (--quick mode)")
            self.categories.append(category)
            return category

        def test_animation_1():
            self.toy.play_animation(R2D2.Animations.EMOTE_YES)
            time.sleep(3)
            return "Played EMOTE_YES"

        def test_animation_2():
            self.toy.play_animation(R2D2.Animations.EMOTE_EXCITED)
            time.sleep(3)
            return "Played EMOTE_EXCITED"

        def test_stop_animation():
            self.toy.stop_animation()
            return "Animation stopped"

        self.run_test("play_animation(EMOTE_YES)", test_animation_1, category)
        self.run_test("play_animation(EMOTE_EXCITED)", test_animation_2, category)
        self.run_test("stop_animation", test_stop_animation, category)

        self.categories.append(category)
        return category

    def test_sensors(self) -> TestCategory:
        """Test sensor streaming."""
        category = TestCategory(name="Sensors")
        print("\n  [Sensor Tests]")

        sensor_data = []

        def sensor_callback(data):
            sensor_data.append(data)

        def test_sensor_streaming():
            sensor_data.clear()
            self.toy.sensor_control.add_sensor_data_notify_listener(sensor_callback)
            self.toy.sensor_control.start()
            time.sleep(1)
            self.toy.sensor_control.stop()
            self.toy.sensor_control.remove_sensor_data_notify_listener(sensor_callback)
            return f"Received {len(sensor_data)} sensor packets"

        def test_collision_detection():
            # Just enable/disable to test the command works
            self.toy.configure_collision_detection(1, 50, 50, 50, 50, 10)
            time.sleep(0.2)
            self.toy.configure_collision_detection(0, 0, 0, 0, 0, 0)  # disable
            return "Collision detection configured"

        self.run_test("sensor_streaming", test_sensor_streaming, category)
        self.run_test("collision_detection", test_collision_detection, category)

        self.categories.append(category)
        return category

    def run_all_tests(self) -> dict:
        """Run all test categories."""
        print("\n" + "=" * 60)
        print(f"R2D2 COMMAND COMPATIBILITY TESTS: {self.toy.name}")
        print("=" * 60)

        test_methods = [
            ("Connection", self.test_connection),
            ("Dome Control", self.test_dome),
            ("Stance Control", self.test_stance),
            ("LED Control", self.test_leds),
            ("Drive Control", self.test_drive),
            ("Audio", self.test_audio),
            ("Animations", self.test_animations),
            ("Sensors", self.test_sensors),
        ]

        for name, method in test_methods:
            if self.prompt_continue(name):
                try:
                    method()
                except Exception as e:
                    print(f"\n  ERROR in {name}: {e}")
            else:
                print(f"\n  Skipping {name}")

        return self.generate_report()

    def generate_report(self) -> dict:
        """Generate a summary report."""
        total_passed = sum(c.passed for c in self.categories)
        total_failed = sum(c.failed for c in self.categories)
        total_tests = sum(c.total for c in self.categories)

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        for category in self.categories:
            status = "PASS" if category.failed == 0 else "FAIL"
            print(f"  {category.name}: {category.passed}/{category.total} ({status})")

        print("-" * 60)
        print(f"  TOTAL: {total_passed}/{total_tests} passed")
        if total_failed > 0:
            print(f"         {total_failed} FAILED")
        print("=" * 60)

        report = {
            'timestamp': datetime.now().isoformat(),
            'robot_name': self.toy.name,
            'robot_address': self.toy.address,
            'quick_mode': self.quick,
            'summary': {
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_tests': total_tests,
            },
            'categories': [
                {
                    'name': c.name,
                    'passed': c.passed,
                    'failed': c.failed,
                    'total': c.total,
                    'results': [asdict(r) for r in c.results]
                }
                for c in self.categories
            ]
        }

        return report


def main():
    # Parse arguments
    robot_name = None
    quick = False
    interactive = False

    for arg in sys.argv[1:]:
        if arg == '--quick':
            quick = True
        elif arg == '--interactive':
            interactive = True
        elif not arg.startswith('-'):
            robot_name = arg

    # Find robot
    if robot_name:
        print(f"Looking for robot: {robot_name}")
        toy = scanner.find_toy(toy_name=robot_name, toy_types=[R2D2])
        if not toy:
            print(f"Robot '{robot_name}' not found.")
            return 1
    else:
        print("Scanning for R2D2 robots...")
        toys = scanner.find_toys(toy_types=[R2D2])
        if not toys:
            print("No R2D2 robots found.")
            return 1
        toy = toys[0]
        print(f"Using: {toy.name}")

    print(f"\nConnecting to {toy.name}...")

    try:
        with toy:
            print("Connected!")

            tester = R2D2Tester(toy, quick=quick, interactive=interactive)
            report = tester.run_all_tests()

            # Save report
            output_dir = Path(__file__).parent / "results"
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"command_tests_{toy.name}_{timestamp}.json"

            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

            print(f"\nResults saved to: {output_file}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0 if report['summary']['total_failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
