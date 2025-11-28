#!/usr/bin/env python3
"""Example usage of LED Manager Client."""

import sys
import time
from pathlib import Path

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.led_manager.led_manager_client import LEDManagerClient
from shared.led_manager.led_protocol import Priority


def main():
    """Demonstrate LED manager client usage."""
    print("LED Manager Client - Example Usage")
    print("=" * 50)

    # Initialize client
    led = LEDManagerClient()
    print("✓ Connected to LED manager daemon\n")

    # Example 1: Show symbols
    print("Example 1: Symbols")
    symbols = ['w', 't', 'd', 'checkmark', 'error']
    for symbol in symbols:
        print(f"  Showing: {symbol}")
        led.show_symbol(symbol)
        time.sleep(1.5)
    print()

    # Example 2: Animations
    print("Example 2: Animations")
    print("  Boot animation (2 seconds)")
    led.show_boot()
    time.sleep(2.5)

    print("  WiFi searching (3 seconds)")
    led.show_animation('wifi_searching', duration=3)
    time.sleep(3.5)

    print("  Idle animation (3 seconds)")
    led.show_animation('idle', duration=3, frame_delay=0.3)
    time.sleep(3.5)
    print()

    # Example 3: Progress bar
    print("Example 3: Progress Bar")
    for percentage in range(0, 101, 25):
        print(f"  Progress: {percentage}%")
        led.show_progress(percentage, priority=Priority.LOW)
        time.sleep(1.5)
    print()

    # Example 4: Priority system
    print("Example 4: Priority System")
    print("  Starting low-priority idle animation...")
    led.show_animation('idle', priority=Priority.LOW)
    time.sleep(2)

    print("  Interrupting with high-priority error...")
    led.show_error()  # HIGH priority
    time.sleep(2)
    print()

    # Clear display
    print("Clearing display...")
    led.clear()
    print("✓ Done!\n")


if __name__ == "__main__":
    try:
        main()
    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure LED manager daemon is running:")
        print("  sudo systemctl status led-manager.service")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
