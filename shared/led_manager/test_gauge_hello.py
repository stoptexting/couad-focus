#!/usr/bin/env python3
"""
Test script for 64x64 RGB LED Matrix
Displays: White background + Green gauge (50%) + "Hello" text
"""

import time
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

def main():
    """Display white background with green gauge and hello text."""

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
    print("Initializing 64x64 RGB LED Matrix...")
    try:
        matrix = RGBMatrix(options=options)
    except Exception as e:
        print(f"ERROR: Failed to initialize matrix: {e}")
        print("Make sure you run this with sudo and the library is installed.")
        sys.exit(1)

    print("Matrix initialized successfully!")

    # Create frame canvas
    canvas = matrix.CreateFrameCanvas()

    # Step 1: Fill entire screen with white
    print("Drawing white background...")
    for x in range(64):
        for y in range(64):
            canvas.SetPixel(x, y, 255, 255, 255)  # White

    # Step 2: Draw green gauge in the middle (50% = 32 rows)
    print("Drawing green gauge (50%) in center...")
    gauge_width = 16  # Width of gauge bar
    gauge_start_x = (64 - gauge_width) // 2  # Center horizontally
    gauge_height = 32  # 50% of 64 rows

    # Draw gauge from bottom to middle
    for y in range(64 - gauge_height, 64):
        for x in range(gauge_start_x, gauge_start_x + gauge_width):
            canvas.SetPixel(x, y, 0, 255, 0)  # Bright green

    # Step 3: Load font and draw "Hello" text
    print("Loading font and drawing text...")
    font = graphics.Font()
    font_path = "../../external/rpi-rgb-led-matrix/fonts/7x13.bdf"

    try:
        font.LoadFont(font_path)
    except Exception as e:
        print(f"WARNING: Could not load font from {font_path}: {e}")
        print("Trying alternative font path...")
        try:
            # Try alternative path if running from different directory
            font.LoadFont("/home/focus/focus/external/rpi-rgb-led-matrix/fonts/7x13.bdf")
        except Exception as e2:
            print(f"WARNING: Could not load font: {e2}")
            print("Continuing without text...")
            font = None

    if font:
        text_color = graphics.Color(255, 0, 0)  # Red text for visibility on white
        text = "Hello"

        # Position text at top center
        text_x = 10
        text_y = 15

        graphics.DrawText(canvas, font, text_x, text_y, text_color, text)
        print(f"Text '{text}' drawn at position ({text_x}, {text_y})")

    # Display the canvas
    print("Displaying on LED matrix...")
    matrix.SwapOnVSync(canvas)

    print("\n" + "="*50)
    print("LED Matrix Test Display Active!")
    print("="*50)
    print("Display shows:")
    print("  - White background (full screen)")
    print("  - Green gauge (50%, centered)")
    print("  - 'Hello' text (red, top)")
    print("\nPress Ctrl+C to exit...")
    print("="*50)

    # Keep display active for 30 seconds or until Ctrl+C
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("\nInterrupted by user")

    # Clear display
    print("Clearing display...")
    canvas.Clear()
    matrix.SwapOnVSync(canvas)

    print("Test complete!")

if __name__ == "__main__":
    main()
