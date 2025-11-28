#!/usr/bin/env python3
"""
Test script for LED display system.
Tests all symbols and animations via the LED manager daemon.

Run this after starting the LED manager daemon to verify all displays work.
"""

import sys
import time
from pathlib import Path

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from led_manager.led_manager_client import LEDManagerClient


def test_symbols(led):
    """Test all static symbols."""
    print("\n=== TESTING SYMBOLS ===\n")

    symbols = [
        ("checkmark", "Checkmark (✓)"),
        ("error", "Error (X)"),
        ("wifi_connected", "WiFi Connected"),
        ("wifi_error", "WiFi Error"),
        ("tunnel_active", "Tunnel Active"),
        ("discord_active", "Discord Active"),
        ("hourglass", "Hourglass"),
        ("dot", "Center Dot"),
    ]

    for symbol_name, description in symbols:
        print(f"Testing: {description}")
        led.show_symbol(symbol_name)
        time.sleep(2.5)  # Wait for display duration + buffer

    print("✓ All symbols tested\n")


def test_animations(led):
    """Test all animations."""
    print("=== TESTING ANIMATIONS ===\n")

    # Test boot animation (fixed duration)
    print("Testing: Boot Animation (progress bar)")
    led.show_boot()
    time.sleep(3.0)

    # Test WiFi searching animation (looping - stop after 3s)
    print("Testing: WiFi Searching Animation")
    led.show_wifi_searching()
    time.sleep(3.0)
    led.stop_current_animation()
    time.sleep(0.5)

    # Test activity animation (looping - stop after 2s)
    print("Testing: Activity Animation (blinking dot)")
    led.show_activity(duration=2.0)
    time.sleep(2.5)

    # Test idle animation (looping - stop after 3s)
    print("Testing: Idle Animation (rotating dot)")
    led.show_idle()
    time.sleep(3.0)
    led.stop_current_animation()
    time.sleep(0.5)

    print("✓ All animations tested\n")


def test_progress_bar(led):
    """Test progress bar display."""
    print("=== TESTING PROGRESS BAR ===\n")

    percentages = [0, 25, 50, 75, 100]

    for pct in percentages:
        print(f"Testing: Progress {pct}%")
        led.show_progress(pct)
        time.sleep(1.5)

    print("✓ Progress bar tested\n")


def test_special_displays(led):
    """Test special displays."""
    print("=== TESTING SPECIAL DISPLAYS ===\n")

    print("Testing: Connected Test (CONNECTED text + checkmark)")
    led.show_connected_test()
    time.sleep(3.5)

    print("Testing: All On (full white screen)")
    led.show_symbol("all_on")
    time.sleep(2.0)

    print("Testing: Clear")
    led.clear()
    time.sleep(1.0)

    print("✓ Special displays tested\n")


def main():
    """Main test sequence."""
    print("=" * 60)
    print("LED Display System Test")
    print("=" * 60)
    print("\nThis script tests all symbols, animations, and displays.")
    print("Make sure the LED manager daemon is running before starting.")
    print("\nPress Enter to begin testing...")
    input()

    try:
        # Connect to LED manager daemon
        print("\n Connecting to LED manager daemon...")
        led = LEDManagerClient()

        # Test connection
        print("Testing connection...")
        led.show_connected_test()
        time.sleep(3.5)

        # Run all tests
        test_symbols(led)
        test_animations(led)
        test_progress_bar(led)
        test_special_displays(led)

        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        # Clear display at end
        led.clear()

    except ConnectionError as e:
        print(f"\n✗ ERROR: Could not connect to LED manager daemon")
        print(f"  {e}")
        print("\n  Make sure the daemon is running:")
        print("  sudo python3 /home/focus/focus/shared/led_manager/led_manager_daemon.py")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ ERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
