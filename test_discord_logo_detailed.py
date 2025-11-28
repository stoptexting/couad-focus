#!/usr/bin/env python3
"""Detailed test to check actual hardware LED display."""

import sys
from pathlib import Path
import time

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.led_manager.led_hardware import LEDHardwareController
from PIL import Image


def test_hardware_mode():
    """Test Discord logo on actual hardware (not mock mode)."""
    print("=" * 60)
    print("Discord Logo Hardware Test")
    print("=" * 60)

    # Create LED controller in HARDWARE mode (not mock)
    print("\n1. Creating LEDHardwareController (hardware mode)...")
    led = LEDHardwareController(mock_mode=False)

    if led.mock_mode:
        print("⚠️  WARNING: Controller is in MOCK MODE!")
        print("   This means hardware is not available or initialization failed.")
        print("   Check GPIO permissions and hardware setup.")
        return False

    print("✓ Hardware mode active")
    print(f"✓ Device initialized: {led.device is not None}")

    # Test showing Discord logo
    print("\n2. Displaying Discord logo...")
    try:
        led.show_discord_active(duration=3.0)
        print("✓ Discord logo displayed for 3 seconds")
    except Exception as e:
        print(f"✗ Error displaying logo: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test fallback to other symbols
    print("\n3. Testing fallback (showing checkmark)...")
    try:
        led.show_checkmark(duration=2.0)
        print("✓ Checkmark displayed")
    except Exception as e:
        print(f"✗ Error displaying checkmark: {e}")

    print("\n" + "=" * 60)
    print("✓ Hardware test complete")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_hardware_mode()
    sys.exit(0 if success else 1)
