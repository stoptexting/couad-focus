"""LED matrix hardware controller for 64x64 RGB LED matrix (HUB75E)."""

import time
import threading
from typing import Optional
from pathlib import Path

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
    from PIL import Image, ImageSequence
    RGB_MATRIX_AVAILABLE = True
except ImportError:
    RGB_MATRIX_AVAILABLE = False


class LEDHardwareController:
    """Hardware controller for 64x64 RGB LED matrix display (HUB75E interface)."""

    def __init__(self, mock_mode: bool = False):
        """
        Initialize LED matrix hardware controller.

        Args:
            mock_mode: If True, run in mock mode without hardware (for testing)
        """
        self.mock_mode = mock_mode or not RGB_MATRIX_AVAILABLE
        self.device: Optional[RGBMatrix] = None
        self.font: Optional[graphics.Font] = None
        self.matrix_width = 64
        self.matrix_height = 64
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_animation = threading.Event()
        self.scroll_thread: Optional[threading.Thread] = None
        self.stop_scroll: Optional[threading.Event] = None
        self.current_state = "off"
        self._lock = threading.Lock()  # Thread safety for hardware access

        # Color definitions
        self.COLOR_GREEN = graphics.Color(0, 255, 0) if not self.mock_mode else None
        self.COLOR_RED = graphics.Color(255, 0, 0) if not self.mock_mode else None
        self.COLOR_BLUE = graphics.Color(0, 100, 255) if not self.mock_mode else None
        self.COLOR_WHITE = graphics.Color(255, 255, 255) if not self.mock_mode else None
        self.COLOR_YELLOW = graphics.Color(255, 255, 0) if not self.mock_mode else None
        self.COLOR_ORANGE = graphics.Color(255, 165, 0) if not self.mock_mode else None
        self.COLOR_PURPLE = graphics.Color(128, 0, 255) if not self.mock_mode else None

        if not self.mock_mode:
            try:
                # Configure RGB matrix options for 64x64 panel with HUB75E
                options = RGBMatrixOptions()
                options.rows = 64
                options.cols = 64
                options.chain_length = 1
                options.parallel = 1
                options.hardware_mapping = 'regular'
                options.multiplexing = 0  # Direct mapping
                options.row_address_type = 0  # 0-based row addressing
                options.scan_mode = 1  # 1/32 scan mode as per datasheet
                options.pwm_bits = 11
                options.brightness = 100
                options.pwm_lsb_nanoseconds = 130
                options.led_rgb_sequence = 'RGB'
                options.pixel_mapper_config = ''
                options.panel_type = ''

                # GPIO pin mapping for HUB75E interface
                options.gpio_slowdown = 4  # Adjust if needed for stability
                options.disable_hardware_pulsing = True  # Disable hardware pulse to run without root

                self.device = RGBMatrix(options=options)

                # Load font once at startup
                self._load_font()

                self.clear()
                print("[LED] Using RGB Matrix (64x64) - HARDWARE MODE")
            except Exception as e:
                error_msg = f"[ERROR] Failed to initialize RGB LED matrix: {e}"
                print(error_msg)
                print("[ERROR] Check GPIO permissions - user must be in 'gpio' and 'video' groups")
                print("[ERROR] Running in mock mode - LED sync will not work!")
                self.mock_mode = True
                self.device = None
                # Log to help debug systemd service issues
                import traceback
                traceback.print_exc()
        else:
            print("[LED] Running in MOCK MODE")

    def _load_font(self) -> None:
        """Load font for text rendering."""
        if self.mock_mode or not self.device:
            return

        try:
            import os
            import sys
            self.font = graphics.Font()

            # Check environment variable first
            font_path = os.environ.get("LED_FONT_PATH", "/opt/focus/fonts/6x10.bdf")

            if not Path(font_path).exists():
                # Fallback to user home directory
                font_path = "/home/focus/focus/external/rpi-rgb-led-matrix/fonts/6x10.bdf"

            if not Path(font_path).exists():
                # Final fallback to relative path (development)
                font_path = str(Path(__file__).parent.parent.parent / "external" / "rpi-rgb-led-matrix" / "fonts" / "6x10.bdf")

            print(f"[LED] DEBUG: Attempting to load font from: {font_path}", file=sys.stderr)
            sys.stderr.flush()
            self.font.LoadFont(font_path)
            print(f"[LED] DEBUG: Font loaded successfully from: {font_path}", file=sys.stderr)
            sys.stderr.flush()
        except Exception as e:
            print(f"[LED] WARNING: Could not load font: {e}")
            self.font = None

    def _create_canvas(self):
        """Create and clear a new canvas for drawing."""
        if self.mock_mode or not self.device:
            return None
        canvas = self.device.CreateFrameCanvas()
        canvas.Clear()
        return canvas

    def _display_canvas(self, canvas, duration: Optional[float] = None) -> None:
        """
        Display canvas on LED matrix.

        Args:
            canvas: Canvas to display
            duration: How long to keep displayed (None = indefinite, controlled by caller)
        """
        if self.mock_mode or not self.device or not canvas:
            return

        self.device.SwapOnVSync(canvas)

        if duration:
            time.sleep(duration)

    # ========== SYMBOL DRAWING METHODS ==========

    def show_checkmark(self, color=None, duration: Optional[float] = 2.0) -> None:
        """
        Display checkmark symbol (✓).

        Args:
            color: Color to use (default green)
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "checkmark"

        with self._lock:
            if self.mock_mode:
                print("[LED] Checkmark ✓")
                return

            color = color or self.COLOR_GREEN
            canvas = self._create_canvas()

            # Draw checkmark centered
            check_x = 25
            check_y = 35

            # Short upward stroke
            graphics.DrawLine(canvas, check_x, check_y, check_x + 5, check_y + 5, color)
            # Long downward stroke
            graphics.DrawLine(canvas, check_x + 5, check_y + 5, check_x + 15, check_y - 15, color)

            self._display_canvas(canvas, duration)

    def show_error(self, duration: Optional[float] = 2.0) -> None:
        """
        Display error symbol (X).

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "error"

        with self._lock:
            if self.mock_mode:
                print("[LED] Error X")
                return

            canvas = self._create_canvas()

            # Draw X centered
            x_start = 20
            y_start = 20
            x_size = 24

            # Diagonal line top-left to bottom-right
            graphics.DrawLine(canvas, x_start, y_start, x_start + x_size, y_start + x_size, self.COLOR_RED)
            # Diagonal line top-right to bottom-left
            graphics.DrawLine(canvas, x_start + x_size, y_start, x_start, y_start + x_size, self.COLOR_RED)

            self._display_canvas(canvas, duration)

    def show_wifi_connected(self, duration: Optional[float] = 2.0) -> None:
        """
        Display WiFi connected symbol (WiFi waves).

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "wifi_connected"

        with self._lock:
            if self.mock_mode:
                print("[LED] WiFi Connected")
                return

            canvas = self._create_canvas()

            # Draw WiFi symbol (3 arcs + dot)
            center_x = 32
            center_y = 40

            # Bottom dot
            graphics.DrawCircle(canvas, center_x, center_y, 2, self.COLOR_GREEN)

            # Small arc
            for angle in range(-45, 46, 5):
                import math
                r = 8
                x = int(center_x + r * math.sin(math.radians(angle)))
                y = int(center_y - r * math.cos(math.radians(angle)))
                canvas.SetPixel(x, y, 0, 255, 0)

            # Medium arc
            for angle in range(-60, 61, 4):
                import math
                r = 14
                x = int(center_x + r * math.sin(math.radians(angle)))
                y = int(center_y - r * math.cos(math.radians(angle)))
                canvas.SetPixel(x, y, 0, 255, 0)

            # Large arc
            for angle in range(-70, 71, 3):
                import math
                r = 20
                x = int(center_x + r * math.sin(math.radians(angle)))
                y = int(center_y - r * math.cos(math.radians(angle)))
                canvas.SetPixel(x, y, 0, 255, 0)

            self._display_canvas(canvas, duration)

    def show_wifi_error(self, duration: Optional[float] = 2.0) -> None:
        """
        Display WiFi error symbol (WiFi waves with slash).

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "wifi_error"

        with self._lock:
            if self.mock_mode:
                print("[LED] WiFi Error")
                return

            canvas = self._create_canvas()

            # Draw WiFi symbol in red
            center_x = 32
            center_y = 40

            # Bottom dot
            graphics.DrawCircle(canvas, center_x, center_y, 2, self.COLOR_RED)

            # Arcs
            for angle in range(-45, 46, 5):
                import math
                r = 8
                x = int(center_x + r * math.sin(math.radians(angle)))
                y = int(center_y - r * math.cos(math.radians(angle)))
                canvas.SetPixel(x, y, 255, 0, 0)

            for angle in range(-60, 61, 4):
                import math
                r = 14
                x = int(center_x + r * math.sin(math.radians(angle)))
                y = int(center_y - r * math.cos(math.radians(angle)))
                canvas.SetPixel(x, y, 255, 0, 0)

            # Diagonal slash through it
            graphics.DrawLine(canvas, 15, 15, 49, 49, self.COLOR_RED)

            self._display_canvas(canvas, duration)

    def show_tunnel_active(self, duration: Optional[float] = 2.0) -> None:
        """
        Display tunnel active symbol (converging lines).

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "tunnel_active"

        with self._lock:
            if self.mock_mode:
                print("[LED] Tunnel Active")
                return

            canvas = self._create_canvas()

            # Draw tunnel perspective (converging parallel lines)
            # Top lines
            graphics.DrawLine(canvas, 10, 15, 25, 32, self.COLOR_BLUE)
            graphics.DrawLine(canvas, 54, 15, 39, 32, self.COLOR_BLUE)

            # Bottom lines
            graphics.DrawLine(canvas, 10, 49, 25, 32, self.COLOR_BLUE)
            graphics.DrawLine(canvas, 54, 49, 39, 32, self.COLOR_BLUE)

            # Center rectangle
            graphics.DrawLine(canvas, 25, 25, 39, 25, self.COLOR_BLUE)
            graphics.DrawLine(canvas, 25, 39, 39, 39, self.COLOR_BLUE)
            graphics.DrawLine(canvas, 25, 25, 25, 39, self.COLOR_BLUE)
            graphics.DrawLine(canvas, 39, 25, 39, 39, self.COLOR_BLUE)

            self._display_canvas(canvas, duration)

    def show_discord_active(self, duration: Optional[float] = 2.0) -> None:
        """
        Display Discord active symbol (real Discord logo).

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "discord_active"

        with self._lock:
            if self.mock_mode:
                print("[LED] Discord Active")
                return

            try:
                # Load the Discord logo image
                logo_path = Path(__file__).parent / "discord_logo.png"
                image = Image.open(logo_path)

                # Convert to RGB first
                image = image.convert('RGB')

                # Resize to fit the matrix (maintain aspect ratio)
                image.thumbnail((self.matrix_width, self.matrix_height), Image.LANCZOS)

                # Pad image to 64x64 if smaller (center it)
                if image.size != (self.matrix_width, self.matrix_height):
                    padded = Image.new('RGB', (self.matrix_width, self.matrix_height), (0, 0, 0))
                    offset = ((self.matrix_width - image.width) // 2, (self.matrix_height - image.height) // 2)
                    padded.paste(image, offset)
                    image = padded

                # Use canvas system to display the image
                canvas = self._create_canvas()
                if canvas:
                    # Load image pixels onto canvas
                    pixels = image.load()
                    for y in range(self.matrix_height):
                        for x in range(self.matrix_width):
                            r, g, b = pixels[x, y]
                            canvas.SetPixel(x, y, r, g, b)

                    self._display_canvas(canvas, duration)

            except Exception as e:
                print(f"[LED] Error loading Discord logo: {e}")
                # Fallback to simple display if image loading fails
                canvas = self._create_canvas()
                graphics.DrawCircle(canvas, 32, 32, 10, self.COLOR_PURPLE)
                self._display_canvas(canvas, duration)

    def show_hourglass(self, duration: Optional[float] = 2.0) -> None:
        """
        Display hourglass symbol (loading/waiting).

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "hourglass"

        with self._lock:
            if self.mock_mode:
                print("[LED] Hourglass")
                return

            canvas = self._create_canvas()

            # Draw hourglass (two triangles touching)
            center_x = 32
            center_y = 32
            size = 15

            # Top triangle
            graphics.DrawLine(canvas, center_x - size, center_y - size, center_x + size, center_y - size, self.COLOR_YELLOW)
            graphics.DrawLine(canvas, center_x - size, center_y - size, center_x, center_y, self.COLOR_YELLOW)
            graphics.DrawLine(canvas, center_x + size, center_y - size, center_x, center_y, self.COLOR_YELLOW)

            # Bottom triangle
            graphics.DrawLine(canvas, center_x - size, center_y + size, center_x + size, center_y + size, self.COLOR_YELLOW)
            graphics.DrawLine(canvas, center_x - size, center_y + size, center_x, center_y, self.COLOR_YELLOW)
            graphics.DrawLine(canvas, center_x + size, center_y + size, center_x, center_y, self.COLOR_YELLOW)

            self._display_canvas(canvas, duration)

    def show_dot(self, duration: Optional[float] = 2.0) -> None:
        """
        Display single dot in center.

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "dot"

        with self._lock:
            if self.mock_mode:
                print("[LED] Dot")
                return

            canvas = self._create_canvas()

            # Draw dot in center
            graphics.DrawCircle(canvas, 32, 32, 3, self.COLOR_WHITE)

            self._display_canvas(canvas, duration)

    def show_all_on(self, duration: Optional[float] = 2.0) -> None:
        """
        Fill entire screen (test pattern).

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "all_on"

        with self._lock:
            if self.mock_mode:
                print("[LED] All On")
                return

            canvas = self._create_canvas()

            # Fill entire screen
            for x in range(self.matrix_width):
                for y in range(self.matrix_height):
                    canvas.SetPixel(x, y, 255, 255, 255)

            self._display_canvas(canvas, duration)

    # ========== ANIMATION METHODS ==========

    def show_boot(self, duration: float = 2.0) -> None:
        """
        Display boot animation (progress bar with 'BOOTING...' text).

        Args:
            duration: Total animation duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "boot"

        def animate():
            start_time = time.time()

            while not self.stop_animation.is_set():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    break

                # Calculate progress (0-100%)
                progress = int((elapsed / duration) * 100)

                with self._lock:
                    if self.mock_mode or not self.device:
                        break

                    canvas = self._create_canvas()

                    # Draw "BOOTING..." text at top
                    if self.font:
                        text = "BOOTING..."
                        text_x = (64 - len(text) * 6) // 2
                        graphics.DrawText(canvas, self.font, text_x, 15, self.COLOR_WHITE, text)

                    # Draw progress bar
                    bar_width = 50
                    bar_height = 10
                    bar_x = (64 - bar_width) // 2
                    bar_y = 35

                    # Border
                    graphics.DrawLine(canvas, bar_x, bar_y, bar_x + bar_width, bar_y, self.COLOR_WHITE)
                    graphics.DrawLine(canvas, bar_x, bar_y + bar_height, bar_x + bar_width, bar_y + bar_height, self.COLOR_WHITE)
                    graphics.DrawLine(canvas, bar_x, bar_y, bar_x, bar_y + bar_height, self.COLOR_WHITE)
                    graphics.DrawLine(canvas, bar_x + bar_width, bar_y, bar_x + bar_width, bar_y + bar_height, self.COLOR_WHITE)

                    # Fill based on progress
                    fill_width = int((progress / 100.0) * (bar_width - 2))
                    for x in range(fill_width):
                        for y in range(bar_height - 1):
                            canvas.SetPixel(bar_x + 1 + x, bar_y + 1 + y, 0, 255, 0)

                    self._display_canvas(canvas)

                # Update every 50ms
                if self.stop_animation.wait(0.05):
                    break

        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()

    def show_wifi_searching(self, duration: Optional[float] = None) -> None:
        """
        Display WiFi searching animation (waves appearing sequentially).

        Args:
            duration: Total duration (None = loop forever)
        """
        self.stop_current_animation()
        self.current_state = "wifi_searching"

        def animate():
            start_time = time.time()
            frame = 0

            while not self.stop_animation.is_set():
                if duration and (time.time() - start_time) >= duration:
                    break

                with self._lock:
                    if self.mock_mode or not self.device:
                        break

                    canvas = self._create_canvas()

                    # Draw WiFi waves appearing one by one
                    center_x = 32
                    center_y = 40

                    # Bottom dot (always visible)
                    graphics.DrawCircle(canvas, center_x, center_y, 2, self.COLOR_BLUE)

                    # Show arcs based on frame
                    if frame >= 0:
                        # Small arc
                        for angle in range(-45, 46, 5):
                            import math
                            r = 8
                            x = int(center_x + r * math.sin(math.radians(angle)))
                            y = int(center_y - r * math.cos(math.radians(angle)))
                            canvas.SetPixel(x, y, 0, 100, 255)

                    if frame >= 1:
                        # Medium arc
                        for angle in range(-60, 61, 4):
                            import math
                            r = 14
                            x = int(center_x + r * math.sin(math.radians(angle)))
                            y = int(center_y - r * math.cos(math.radians(angle)))
                            canvas.SetPixel(x, y, 0, 100, 255)

                    if frame >= 2:
                        # Large arc
                        for angle in range(-70, 71, 3):
                            import math
                            r = 20
                            x = int(center_x + r * math.sin(math.radians(angle)))
                            y = int(center_y - r * math.cos(math.radians(angle)))
                            canvas.SetPixel(x, y, 0, 100, 255)

                    self._display_canvas(canvas)

                frame = (frame + 1) % 3

                if self.stop_animation.wait(0.4):
                    break

        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()

    def show_activity(self, duration: Optional[float] = None) -> None:
        """
        Display activity animation (blinking dot in corner).

        Args:
            duration: Total duration (None = loop forever)
        """
        self.stop_current_animation()
        self.current_state = "activity"

        def animate():
            start_time = time.time()
            on = True

            while not self.stop_animation.is_set():
                if duration and (time.time() - start_time) >= duration:
                    break

                with self._lock:
                    if self.mock_mode or not self.device:
                        break

                    canvas = self._create_canvas()

                    if on:
                        # Draw dot in top-right corner
                        graphics.DrawCircle(canvas, 58, 6, 3, self.COLOR_GREEN)

                    self._display_canvas(canvas)

                on = not on

                if self.stop_animation.wait(0.5):
                    break

        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()

    def show_idle(self, duration: Optional[float] = None) -> None:
        """
        Display idle animation (dot rotating around screen perimeter).

        Args:
            duration: Total duration (None = loop forever)
        """
        self.stop_current_animation()
        self.current_state = "idle"

        def animate():
            start_time = time.time()
            positions = [
                (32, 5),   # Top center
                (55, 10),  # Top right
                (58, 32),  # Right center
                (55, 54),  # Bottom right
                (32, 59),  # Bottom center
                (9, 54),   # Bottom left
                (6, 32),   # Left center
                (9, 10),   # Top left
            ]
            frame = 0

            while not self.stop_animation.is_set():
                if duration and (time.time() - start_time) >= duration:
                    break

                with self._lock:
                    if self.mock_mode or not self.device:
                        break

                    canvas = self._create_canvas()

                    # Draw dot at current position
                    x, y = positions[frame]
                    graphics.DrawCircle(canvas, x, y, 2, self.COLOR_BLUE)

                    self._display_canvas(canvas)

                frame = (frame + 1) % len(positions)

                if self.stop_animation.wait(0.3):
                    break

        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()

    def show_gif(self, gif_name: str, loop: bool = True) -> None:
        """
        Display a GIF animation from the gifs/ directory.

        Args:
            gif_name: Name of the GIF file (without .gif extension)
            loop: Whether to loop the animation (default True = loop forever)
        """
        self.stop_current_animation()
        self.current_state = f"gif_{gif_name}"

        # Locate GIF file
        gif_path = Path(__file__).parent / "gifs" / f"{gif_name}.gif"

        if not gif_path.exists():
            print(f"[LED] GIF not found: {gif_path}")
            return

        if self.mock_mode:
            print(f"[LED] Playing GIF: {gif_name} (loop={loop})")
            return

        def animate():
            try:
                # Load GIF
                gif = Image.open(gif_path)
                frames = []
                delays = []

                # Extract all frames
                for frame in ImageSequence.Iterator(gif):
                    # Convert to RGB and resize to 64x64
                    frame_rgb = frame.convert('RGB')
                    frame_rgb.thumbnail((self.matrix_width, self.matrix_height), Image.LANCZOS)

                    # Center if smaller than 64x64
                    if frame_rgb.size != (self.matrix_width, self.matrix_height):
                        padded = Image.new('RGB', (self.matrix_width, self.matrix_height), (0, 0, 0))
                        offset = (
                            (self.matrix_width - frame_rgb.width) // 2,
                            (self.matrix_height - frame_rgb.height) // 2
                        )
                        padded.paste(frame_rgb, offset)
                        frame_rgb = padded

                    frames.append(frame_rgb)
                    # Get frame duration (default 100ms if not specified)
                    delay = frame.info.get('duration', 100) / 1000.0
                    delays.append(delay)

                gif.close()

                if not frames:
                    print(f"[LED] No frames found in GIF: {gif_name}")
                    return

                frame_idx = 0

                while not self.stop_animation.is_set():
                    with self._lock:
                        if self.mock_mode or not self.device:
                            break

                        canvas = self._create_canvas()
                        if canvas:
                            # Draw frame pixels
                            frame = frames[frame_idx]
                            pixels = frame.load()
                            for y in range(self.matrix_height):
                                for x in range(self.matrix_width):
                                    r, g, b = pixels[x, y]
                                    canvas.SetPixel(x, y, r, g, b)

                            self._display_canvas(canvas)

                    # Wait for frame duration
                    if self.stop_animation.wait(delays[frame_idx]):
                        break

                    # Move to next frame
                    frame_idx += 1
                    if frame_idx >= len(frames):
                        if loop:
                            frame_idx = 0
                        else:
                            break

            except Exception as e:
                print(f"[LED] Error playing GIF {gif_name}: {e}")
                import traceback
                traceback.print_exc()

        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()

    # ========== PROGRESS BAR ==========

    def show_progress(self, percentage: int) -> None:
        """
        Display progress bar on 64x64 RGB LED matrix.

        Progress is shown as a vertical bar from bottom to top.

        Args:
            percentage: Progress value from 0 to 100
        """
        self.stop_current_animation()

        with self._lock:
            if self.mock_mode:
                print(f"[LED] Progress: {percentage}%")
                return

            if self.device is None:
                return

            # Clamp percentage to 0-100
            percentage = max(0, min(100, percentage))

            # Create canvas
            canvas = self._create_canvas()

            # Calculate number of rows to light (0-64)
            rows_to_light = int((percentage / 100.0) * self.matrix_height)

            # Color gradient from green (low) to yellow (mid) to red (high)
            for y in range(self.matrix_height):
                # Calculate if this row should be lit (from bottom to top)
                row_from_bottom = self.matrix_height - 1 - y
                if row_from_bottom < rows_to_light:
                    # Calculate color based on position
                    if y < self.matrix_height // 3:
                        # Top third: red
                        color = (255, 0, 0)
                    elif y < 2 * self.matrix_height // 3:
                        # Middle third: yellow
                        color = (255, 255, 0)
                    else:
                        # Bottom third: green
                        color = (0, 255, 0)

                    # Draw full row
                    for x in range(self.matrix_width):
                        canvas.SetPixel(x, y, color[0], color[1], color[2])

            self.current_state = f"progress_{percentage}%"
            self._display_canvas(canvas)

    # ========== CONNECTED TEST ==========

    def show_connected_test(self, duration: float = 3.0) -> None:
        """
        Display 'CONNECTED' with green checkmark for communication test.

        Args:
            duration: Display duration in seconds
        """
        self.stop_current_animation()
        self.current_state = "connected_test"

        with self._lock:
            if self.mock_mode:
                print("[LED] CONNECTED ✓")
                return

            if self.device is None:
                return

            try:
                canvas = self._create_canvas()

                # Green color for text and checkmark
                green = self.COLOR_GREEN

                if self.font:
                    # Draw "CONNECTED" text centered
                    text = "CONNECTED"
                    text_x = (64 - len(text) * 6) // 2
                    text_y = 20
                    graphics.DrawText(canvas, self.font, text_x, text_y, green, text)

                # Draw green checkmark (✓) below text
                check_x = 28
                check_y = 35

                # Short upward stroke
                graphics.DrawLine(canvas, check_x, check_y, check_x + 5, check_y + 5, green)
                # Long downward stroke
                graphics.DrawLine(canvas, check_x + 5, check_y + 5, check_x + 15, check_y - 10, green)

                self._display_canvas(canvas, duration)

            except Exception as e:
                print(f"[LED] Error in show_connected_test: {e}")

    # ========== UTILITY METHODS ==========

    def show_symbol(self, symbol: str, duration: Optional[float] = 2.0) -> None:
        """
        Display a static symbol by name.

        Args:
            symbol: Symbol name (checkmark, error, wifi, wifi_error, tunnel, discord, hourglass, dot, all_on)
            duration: Display duration in seconds
        """
        symbol_lower = symbol.lower()

        # Map symbol names to methods
        symbol_methods = {
            "checkmark": lambda: self.show_checkmark(duration=duration),
            "check": lambda: self.show_checkmark(duration=duration),
            "error": lambda: self.show_error(duration=duration),
            "x": lambda: self.show_error(duration=duration),
            "wifi": lambda: self.show_wifi_connected(duration=duration),
            "wifi_connected": lambda: self.show_wifi_connected(duration=duration),
            "wifi_error": lambda: self.show_wifi_error(duration=duration),
            "tunnel": lambda: self.show_tunnel_active(duration=duration),
            "tunnel_active": lambda: self.show_tunnel_active(duration=duration),
            "t": lambda: self.show_tunnel_active(duration=duration),
            "discord": lambda: self.show_discord_active(duration=duration),
            "discord_active": lambda: self.show_discord_active(duration=duration),
            "d": lambda: self.show_discord_active(duration=duration),
            "hourglass": lambda: self.show_hourglass(duration=duration),
            "dot": lambda: self.show_dot(duration=duration),
            "all_on": lambda: self.show_all_on(duration=duration),
            "w": lambda: self.show_wifi_connected(duration=duration),
        }

        if symbol_lower in symbol_methods:
            symbol_methods[symbol_lower]()
        else:
            print(f"[LED] Unknown symbol: {symbol}")

    def show_animation(self, animation: str, duration: Optional[float] = None, frame_delay: float = 0.2) -> None:
        """
        Display an animation by name.

        Args:
            animation: Animation name (boot, wifi_searching, activity, idle)
            duration: Total duration (None = loop forever)
            frame_delay: Not used in new implementation (kept for compatibility)
        """
        animation_lower = animation.lower()

        # Map animation names to methods
        animation_methods = {
            "boot": lambda: self.show_boot(duration=duration or 2.0),
            "wifi_searching": lambda: self.show_wifi_searching(duration=duration),
            "activity": lambda: self.show_activity(duration=duration),
            "idle": lambda: self.show_idle(duration=duration),
        }

        if animation_lower in animation_methods:
            animation_methods[animation_lower]()
        else:
            print(f"[LED] Unknown animation: {animation}")

    def stop_current_animation(self) -> None:
        """Stop any currently running animation."""
        if self.animation_thread and self.animation_thread.is_alive():
            self.stop_animation.set()
            self.animation_thread.join(timeout=1.0)
            self.stop_animation.clear()
            self.animation_thread = None

    def stop_scrolling_text(self) -> None:
        """Stop any running scrolling text animation."""
        if self.stop_scroll:
            self.stop_scroll.set()
        if self.scroll_thread and self.scroll_thread.is_alive():
            self.scroll_thread.join(timeout=0.5)
        self.scroll_thread = None
        self.stop_scroll = None

    def stop_all_animations(self) -> None:
        """Stop all running animations (GIF, scrolling text, etc.)."""
        self.stop_current_animation()
        self.stop_scrolling_text()

    def clear(self) -> None:
        """Clear the LED matrix (all LEDs off)."""
        self.stop_current_animation()
        self.current_state = "off"

        with self._lock:
            if self.mock_mode:
                print("[LED] Clear")
                return

            if self.device is None:
                return

            # Clear all pixels
            canvas = self._create_canvas()
            self._display_canvas(canvas)

    def test(self) -> None:
        """Run a test sequence to verify LED matrix functionality."""
        print("[LED] Running test sequence...")

        # Test 1: All on
        print("[LED] Test 1: All LEDs on")
        self.show_all_on(duration=1.0)
        time.sleep(1.5)

        # Test 2: All off
        print("[LED] Test 2: All LEDs off")
        self.clear()
        time.sleep(0.5)

        # Test 3: Symbols
        symbols = ["checkmark", "error", "wifi", "wifi_error", "tunnel", "discord"]
        for sym in symbols:
            print(f"[LED] Test 3: Showing '{sym}'")
            self.show_symbol(sym, duration=0.8)
            time.sleep(1.0)

        # Test 4: Progress bar
        print("[LED] Test 4: Progress bar (0% -> 100%)")
        for pct in range(0, 101, 25):
            print(f"[LED] Progress: {pct}%")
            self.show_progress(pct)
            time.sleep(0.8)

        # Test 5: Boot animation
        print("[LED] Test 5: Boot animation")
        self.show_boot(duration=2.0)
        time.sleep(2.5)

        # Test 6: Wi-Fi searching
        print("[LED] Test 6: Wi-Fi searching animation (3s)")
        self.show_wifi_searching(duration=3.0)
        time.sleep(3.5)

        # Clear at end
        self.clear()
        print("[LED] Test sequence complete")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_current_animation()
        self.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
