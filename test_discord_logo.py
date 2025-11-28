#!/usr/bin/env python3
"""Test script to verify Discord logo loading works correctly."""

import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.led_manager.led_hardware import LEDHardwareController
from PIL import Image


def test_discord_logo_exists():
    """Test 1: Verify the Discord logo file exists."""
    logo_path = Path(__file__).parent / "shared/led_manager/discord_logo.png"
    print(f"✓ Test 1: Checking if logo file exists at {logo_path}")
    assert logo_path.exists(), f"Logo file not found at {logo_path}"
    print(f"  ✓ Logo file exists ({logo_path.stat().st_size} bytes)")


def test_logo_image_loads():
    """Test 2: Verify PIL can open and process the logo."""
    logo_path = Path(__file__).parent / "shared/led_manager/discord_logo.png"
    print("\n✓ Test 2: Testing PIL image loading")

    image = Image.open(logo_path)
    print(f"  ✓ Image opened successfully")
    print(f"    - Mode: {image.mode}")
    print(f"    - Size: {image.size}")

    # Test the operations that show_discord_active does
    image.thumbnail((64, 64), Image.LANCZOS)
    print(f"  ✓ Thumbnail operation successful")

    rgb_image = image.convert('RGB')
    print(f"  ✓ RGB conversion successful (mode: {rgb_image.mode})")


def test_led_hardware_mock():
    """Test 3: Test show_discord_active in mock mode."""
    print("\n✓ Test 3: Testing LEDHardwareController.show_discord_active() in mock mode")

    # Create LED hardware in mock mode (no actual hardware needed)
    led = LEDHardwareController(mock_mode=True)
    print(f"  ✓ LEDHardwareController created in mock mode")

    # Call show_discord_active (should print "[LED] Discord Active" in mock mode)
    led.show_discord_active(duration=0.1)
    print(f"  ✓ show_discord_active() called successfully")


if __name__ == "__main__":
    print("=" * 60)
    print("Discord Logo Loading Test Suite")
    print("=" * 60)

    try:
        test_discord_logo_exists()
        test_logo_image_loads()
        test_led_hardware_mock()

        print("\n" + "=" * 60)
        print("✓ All tests passed! Discord logo is working correctly.")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
