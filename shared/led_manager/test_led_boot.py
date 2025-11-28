#!/usr/bin/env python3
"""
LED Boot Test Script - Runs at system boot to verify LED hardware
Displays "CONNECTED" with green checkmark for 5 seconds
Tests LED panel independently of daemon/services
"""

import time
import sys
from pathlib import Path

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
except ImportError:
    print("ERROR: rgbmatrix library not installed")
    print("Run: bash scripts/install_led_library.sh")
    sys.exit(1)

def main():
    """Display CONNECTED message to verify LED hardware at boot."""

    print("[LED BOOT TEST] Starting LED hardware test...")

    # Configure RGB matrix options for 64x64 panel
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'regular'
    options.multiplexing = 0
    options.row_address_type = 0
    options.scan_mode = 1
    options.pwm_bits = 11
    options.brightness = 100
    options.pwm_lsb_nanoseconds = 130
    options.led_rgb_sequence = 'RGB'
    options.pixel_mapper_config = ''
    options.panel_type = ''
    options.gpio_slowdown = 4
    options.disable_hardware_pulsing = False

    # Initialize matrix
    try:
        matrix = RGBMatrix(options=options)
        print("[LED BOOT TEST] Matrix initialized successfully")
    except Exception as e:
        print(f"[LED BOOT TEST] ERROR: Failed to initialize matrix: {e}")
        sys.exit(1)

    # Create frame canvas
    canvas = matrix.CreateFrameCanvas()
    canvas.Clear()

    # Load font
    font = graphics.Font()

    # Try multiple font paths
    font_paths = [
        "/home/focus/focus/external/rpi-rgb-led-matrix/fonts/6x10.bdf",
        str(Path(__file__).parent.parent.parent / "external" / "rpi-rgb-led-matrix" / "fonts" / "6x10.bdf"),
        "/usr/local/share/fonts/6x10.bdf"
    ]

    font_loaded = False
    for font_path in font_paths:
        try:
            font.LoadFont(font_path)
            font_loaded = True
            print(f"[LED BOOT TEST] Font loaded from: {font_path}")
            break
        except Exception as e:
            continue

    if not font_loaded:
        print("[LED BOOT TEST] WARNING: Could not load font, displaying checkmark only")

    # Green color
    green = graphics.Color(0, 255, 0)

    # Draw "CONNECTED" text if font loaded
    if font_loaded:
        text = "CONNECTED"
        # Center text (6px font width)
        text_x = (64 - len(text) * 6) // 2
        text_y = 20
        graphics.DrawText(canvas, font, text_x, text_y, green, text)
        print("[LED BOOT TEST] Text drawn: CONNECTED")

    # Draw green checkmark (✓)
    # First line of check (short upward stroke)
    check_x = 28
    check_y = 35
    graphics.DrawLine(canvas, check_x, check_y, check_x + 5, check_y + 5, green)

    # Second line of check (longer downward stroke)
    graphics.DrawLine(canvas, check_x + 5, check_y + 5, check_x + 15, check_y - 10, green)

    print("[LED BOOT TEST] Checkmark drawn")

    # Display on matrix
    matrix.SwapOnVSync(canvas)
    print("[LED BOOT TEST] Display updated - CONNECTED message should be visible on LED panel")

    # Keep displayed for 5 seconds
    print("[LED BOOT TEST] Holding display for 5 seconds...")
    time.sleep(5)

    # Clear display
    canvas.Clear()
    matrix.SwapOnVSync(canvas)
    print("[LED BOOT TEST] Test complete - display cleared")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[LED BOOT TEST] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[LED BOOT TEST] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
