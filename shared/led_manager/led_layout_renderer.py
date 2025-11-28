"""LED Layout Renderer for 64x64 matrix with 4 viewing modes."""

import threading
from typing import List, Dict, Optional, Tuple
from .led_hardware import LEDHardwareController

try:
    from rgbmatrix import graphics
    RGB_MATRIX_AVAILABLE = True
except ImportError:
    RGB_MATRIX_AVAILABLE = False
    graphics = None


class LEDLayoutRenderer:
    """Renders 4 different layout views on 64x64 LED matrix."""

    # Layout constants
    MATRIX_WIDTH = 64
    MATRIX_HEIGHT = 64

    # Color scheme (type-based)
    COLOR_PROJECT = (0, 100, 255)    # Blue
    COLOR_SPRINT = (0, 255, 0)       # Green
    COLOR_USER_STORY = (255, 255, 0) # Yellow

    # Color palette for user stories in sprint gauge (multi-segment display)
    USER_STORY_COLORS = [
        (0, 100, 255),    # Blue
        (255, 255, 0),    # Yellow
        (0, 255, 255),    # Cyan
        (255, 0, 255),    # Magenta
        (255, 128, 0),    # Orange
        (128, 255, 0),    # Lime
        (255, 0, 128),    # Pink
        (128, 0, 255),    # Purple
    ]

    # Color palette for sprints in single layout (project gauge multi-segment display)
    SPRINT_COLORS = [
        (0, 255, 0),      # Green
        (0, 200, 255),    # Light Blue
        (255, 165, 0),    # Orange
        (255, 0, 100),    # Pink
        (128, 0, 255),    # Purple
        (255, 255, 0),    # Yellow
    ]

    def __init__(self, controller: LEDHardwareController):
        """
        Initialize LED Layout Renderer.

        Args:
            controller: LEDHardwareController instance
        """
        self.controller = controller
        self.mock_mode = controller.mock_mode

    def _get_color_for_type(self, entity_type: str):
        """
        Get graphics.Color for entity type.

        Args:
            entity_type: 'project', 'sprint', or 'user_story'

        Returns:
            graphics.Color object or None if mock mode
        """
        if self.mock_mode:
            return None

        color_map = {
            'project': self.COLOR_PROJECT,
            'sprint': self.COLOR_SPRINT,
            'user_story': self.COLOR_USER_STORY
        }

        rgb = color_map.get(entity_type, self.COLOR_PROJECT)
        return graphics.Color(rgb[0], rgb[1], rgb[2])

    def _fill_vertical_bar(self, canvas, x_start: int, x_end: int, y_start: int, y_end: int,
                          percentage: float, color_rgb: Tuple[int, int, int]) -> None:
        """
        Fill a vertical progress bar from bottom to top.

        Args:
            canvas: RGB matrix canvas
            x_start: Left edge X coordinate
            x_end: Right edge X coordinate (exclusive)
            y_start: Top edge Y coordinate
            y_end: Bottom edge Y coordinate (exclusive)
            percentage: Progress percentage (0-100)
            color_rgb: RGB color tuple (r, g, b)
        """
        if self.mock_mode or not canvas:
            return

        height = y_end - y_start
        fill_height = int((percentage / 100.0) * height)

        # Fill from bottom to top
        for y in range(fill_height):
            actual_y = y_end - 1 - y  # Start from bottom
            for x in range(x_start, x_end):
                if 0 <= x < self.MATRIX_WIDTH and 0 <= actual_y < self.MATRIX_HEIGHT:
                    canvas.SetPixel(x, actual_y, color_rgb[0], color_rgb[1], color_rgb[2])

    def _fill_multi_segment_vertical_bar(self, canvas, x_start: int, x_end: int, y_start: int, y_end: int,
                                          sprints: List[Dict], colors: List[Tuple[int, int, int]]) -> None:
        """
        Fill a vertical bar with colored segments proportional to sprint contributions.

        The total fill represents project completion (average of all sprints).
        Each color segment is proportional to that sprint's contribution.
        Sprints at 0% don't appear (no contribution).

        Args:
            canvas: RGB matrix canvas
            x_start: Left edge X coordinate
            x_end: Right edge X coordinate (exclusive)
            y_start: Top edge Y coordinate
            y_end: Bottom edge Y coordinate (exclusive)
            sprints: List of sprint dicts with 'progress' containing 'percentage'
            colors: List of RGB color tuples for each segment
        """
        if self.mock_mode or not canvas:
            return

        if not sprints:
            return

        total_height = y_end - y_start
        num_sprints = len(sprints)

        # Calculate each sprint's percentage and total contribution
        percentages = [sprint.get('progress', {}).get('percentage', 0) for sprint in sprints]
        total_contribution = sum(percentages)

        # Project completion = average of all sprint completions
        project_percentage = total_contribution / num_sprints if num_sprints > 0 else 0

        # Total filled height based on project completion
        fill_height = int((project_percentage / 100.0) * total_height)

        if fill_height == 0 or total_contribution == 0:
            return  # Nothing to draw

        # Draw colored segments proportional to each sprint's contribution
        # Fill from bottom to top
        current_y = y_end - 1  # Start from bottom
        for i, percentage in enumerate(percentages):
            if percentage == 0:
                continue  # Skip sprints with 0% (no contribution)

            # Segment height proportional to contribution
            segment_height = int((percentage / total_contribution) * fill_height)

            # Handle rounding for last visible segment
            if i == len(percentages) - 1 or all(p == 0 for p in percentages[i+1:]):
                segment_height = current_y - (y_end - 1 - fill_height)

            if segment_height <= 0:
                continue

            color = colors[i % len(colors)]

            # Fill segment from bottom to top
            for y_offset in range(segment_height):
                actual_y = current_y - y_offset
                for x in range(x_start, x_end):
                    if 0 <= x < self.MATRIX_WIDTH and 0 <= actual_y < self.MATRIX_HEIGHT:
                        canvas.SetPixel(x, actual_y, color[0], color[1], color[2])

            current_y -= segment_height

    def _fill_horizontal_bar(self, canvas, x_start: int, x_end: int, y_start: int, y_end: int,
                            percentage: float, color_rgb: Tuple[int, int, int]) -> None:
        """
        Fill a horizontal progress bar from left to right.

        Args:
            canvas: RGB matrix canvas
            x_start: Left edge X coordinate
            x_end: Right edge X coordinate (exclusive)
            y_start: Top edge Y coordinate
            y_end: Bottom edge Y coordinate (exclusive)
            percentage: Progress percentage (0-100)
            color_rgb: RGB color tuple (r, g, b)
        """
        if self.mock_mode or not canvas:
            return

        width = x_end - x_start
        fill_width = int((percentage / 100.0) * width)

        # Fill from left to right
        for x in range(fill_width):
            actual_x = x_start + x
            for y in range(y_start, y_end):
                if 0 <= actual_x < self.MATRIX_WIDTH and 0 <= y < self.MATRIX_HEIGHT:
                    canvas.SetPixel(actual_x, y, color_rgb[0], color_rgb[1], color_rgb[2])

    def _fill_multi_segment_bar(self, canvas, x_start: int, x_end: int, y_start: int, y_end: int,
                                 user_stories: List[Dict], colors: List[Tuple[int, int, int]]) -> None:
        """
        Fill a horizontal bar with colored segments proportional to user story contributions.

        The total fill represents sprint completion (average of all user stories).
        Each color segment is proportional to that user story's contribution.
        User stories at 0% don't appear (no contribution).

        Args:
            canvas: RGB matrix canvas
            x_start: Left edge X coordinate
            x_end: Right edge X coordinate (exclusive)
            y_start: Top edge Y coordinate
            y_end: Bottom edge Y coordinate (exclusive)
            user_stories: List of user story dicts with 'progress' containing 'percentage'
            colors: List of RGB color tuples for each segment
        """
        if self.mock_mode or not canvas:
            return

        if not user_stories:
            return

        total_width = x_end - x_start
        num_stories = len(user_stories)

        # Calculate each user story's percentage and total contribution
        percentages = [story.get('progress', {}).get('percentage', 0) for story in user_stories]
        total_contribution = sum(percentages)

        # Sprint completion = average of all user story completions
        sprint_percentage = total_contribution / num_stories if num_stories > 0 else 0

        # Total filled width based on sprint completion
        fill_width = int((sprint_percentage / 100.0) * total_width)

        if fill_width == 0 or total_contribution == 0:
            return  # Nothing to draw

        # Draw colored segments proportional to each user story's contribution
        current_x = x_start
        for i, percentage in enumerate(percentages):
            if percentage == 0:
                continue  # Skip user stories with 0% (no contribution)

            # Segment width proportional to contribution
            segment_width = int((percentage / total_contribution) * fill_width)

            # Handle rounding for last visible segment to fill exactly to fill_width
            if i == len(percentages) - 1 or all(p == 0 for p in percentages[i+1:]):
                segment_width = (x_start + fill_width) - current_x

            if segment_width <= 0:
                continue

            color = colors[i % len(colors)]

            # Fill full height (no vertical gaps)
            for x in range(current_x, current_x + segment_width):
                for y in range(y_start, y_end):
                    if 0 <= x < self.MATRIX_WIDTH and 0 <= y < self.MATRIX_HEIGHT:
                        canvas.SetPixel(x, y, color[0], color[1], color[2])

            current_x += segment_width

    def _fill_multi_segment_horizontal_bar_fixed(self, canvas, x_start: int, x_end: int, y_start: int, y_end: int,
                                                   total_percentage: float, sprints: List[Dict],
                                                   colors: List[Tuple[int, int, int]]) -> None:
        """
        Fill a horizontal bar with colored segments using a fixed total percentage.

        The total fill is determined by total_percentage parameter (not calculated from sprints).
        Each sprint's color segment is proportional to its contribution to the total.

        Args:
            canvas: RGB matrix canvas
            x_start: Left edge X coordinate
            x_end: Right edge X coordinate (exclusive)
            y_start: Top edge Y coordinate
            y_end: Bottom edge Y coordinate (exclusive)
            total_percentage: The total percentage to fill (0-100)
            sprints: List of sprint dicts with 'progress' containing 'percentage'
            colors: List of RGB color tuples for each segment
        """
        if self.mock_mode or not canvas:
            return

        total_width = x_end - x_start

        # Total filled width based on provided percentage
        fill_width = int((total_percentage / 100.0) * total_width)

        if fill_width == 0:
            return  # Nothing to draw

        if not sprints:
            # No sprints - fill with first color (green)
            color = colors[0] if colors else (0, 255, 0)
            for x in range(x_start, x_start + fill_width):
                for y in range(y_start, y_end):
                    if 0 <= x < self.MATRIX_WIDTH and 0 <= y < self.MATRIX_HEIGHT:
                        canvas.SetPixel(x, y, color[0], color[1], color[2])
            return

        # Calculate each sprint's percentage
        percentages = [sprint.get('progress', {}).get('percentage', 0) for sprint in sprints]
        total_contribution = sum(percentages)

        if total_contribution == 0:
            # All sprints at 0% - draw gray placeholder
            return

        # Draw colored segments proportional to each sprint's contribution
        current_x = x_start
        for i, percentage in enumerate(percentages):
            if percentage == 0:
                continue  # Skip sprints with 0% (no contribution)

            # Segment width proportional to contribution
            segment_width = int((percentage / total_contribution) * fill_width)

            # Handle rounding for last visible segment
            if i == len(percentages) - 1 or all(p == 0 for p in percentages[i+1:]):
                segment_width = (x_start + fill_width) - current_x

            if segment_width <= 0:
                continue

            color = colors[i % len(colors)]

            # Fill full height
            for x in range(current_x, current_x + segment_width):
                for y in range(y_start, y_end):
                    if 0 <= x < self.MATRIX_WIDTH and 0 <= y < self.MATRIX_HEIGHT:
                        canvas.SetPixel(x, y, color[0], color[1], color[2])

            current_x += segment_width

    def _draw_outline_rectangle(self, canvas, x_start: int, x_end: int, y_start: int, y_end: int,
                               color_rgb: Tuple[int, int, int]) -> None:
        """
        Draw an outline rectangle (border only, not filled).

        Args:
            canvas: RGB matrix canvas
            x_start: Left edge X coordinate
            x_end: Right edge X coordinate (exclusive)
            y_start: Top edge Y coordinate
            y_end: Bottom edge Y coordinate (exclusive)
            color_rgb: RGB color tuple (r, g, b)
        """
        if self.mock_mode or not canvas:
            return

        # Draw top and bottom edges
        for x in range(x_start, x_end):
            if 0 <= x < self.MATRIX_WIDTH:
                # Top edge
                if 0 <= y_start < self.MATRIX_HEIGHT:
                    canvas.SetPixel(x, y_start, color_rgb[0], color_rgb[1], color_rgb[2])
                # Bottom edge
                if 0 <= y_end - 1 < self.MATRIX_HEIGHT:
                    canvas.SetPixel(x, y_end - 1, color_rgb[0], color_rgb[1], color_rgb[2])

        # Draw left and right edges
        for y in range(y_start, y_end):
            if 0 <= y < self.MATRIX_HEIGHT:
                # Left edge
                if 0 <= x_start < self.MATRIX_WIDTH:
                    canvas.SetPixel(x_start, y, color_rgb[0], color_rgb[1], color_rgb[2])
                # Right edge
                if 0 <= x_end - 1 < self.MATRIX_WIDTH:
                    canvas.SetPixel(x_end - 1, y, color_rgb[0], color_rgb[1], color_rgb[2])

    def _draw_text(self, canvas, text: str, x: int, y: int, color_rgb: Tuple[int, int, int]) -> None:
        """
        Draw text on canvas.

        Args:
            canvas: RGB matrix canvas
            text: Text to draw
            x: X coordinate
            y: Y baseline coordinate
            color_rgb: RGB color tuple (r, g, b)
        """
        if self.mock_mode or not canvas or not self.controller.font:
            return

        color = graphics.Color(color_rgb[0], color_rgb[1], color_rgb[2])
        graphics.DrawText(canvas, self.controller.font, x, y, color, text)

    def _draw_text_centered(self, canvas, text: str, x: int, y: int, color_rgb: Tuple[int, int, int]) -> None:
        """
        Draw text centered at x coordinate.

        Args:
            canvas: RGB matrix canvas
            text: Text to draw
            x: X coordinate (center point)
            y: Y baseline coordinate
            color_rgb: RGB color tuple (r, g, b)
        """
        if self.mock_mode or not canvas or not self.controller.font:
            return

        # Calculate text width (approximate: each char is ~6px wide for 6x10 font)
        text_width = len(text) * 6
        text_x = x - (text_width // 2)
        self._draw_text(canvas, text, text_x, y, color_rgb)

    def _draw_percentage_number(self, canvas, percentage: float, x: int, y: int,
                               color_rgb: Tuple[int, int, int]) -> None:
        """
        Draw percentage number (e.g., "75").

        Args:
            canvas: RGB matrix canvas
            percentage: Percentage value
            x: X coordinate (center)
            y: Y coordinate
            color_rgb: RGB color tuple
        """
        text = str(int(percentage))
        # Center the text (approximate: each char is ~6px wide)
        text_width = len(text) * 6
        text_x = x - (text_width // 2)
        self._draw_text(canvas, text, text_x, y, color_rgb)

    def _draw_checkmark(self, canvas, x: int, y: int) -> None:
        """
        Draw a white checkmark in a green box (7x7 pixels).
        Used to indicate 100% completion.

        Args:
            canvas: RGB matrix canvas
            x: X coordinate (left edge)
            y: Y coordinate (top edge)
        """
        if self.mock_mode or not canvas:
            return

        # Colors
        GREEN_BG = (0, 200, 0)      # Slightly darker green for contrast
        WHITE_CHECK = (255, 255, 255)

        # 7x7 checkmark pattern: 0 = green bg, 1 = white checkmark
        pattern = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]

        for row in range(7):
            for col in range(7):
                pixel_x = x + col
                pixel_y = y + row
                if 0 <= pixel_x < self.MATRIX_WIDTH and 0 <= pixel_y < self.MATRIX_HEIGHT:
                    if pattern[row][col] == 1:
                        canvas.SetPixel(pixel_x, pixel_y, WHITE_CHECK[0], WHITE_CHECK[1], WHITE_CHECK[2])
                    else:
                        canvas.SetPixel(pixel_x, pixel_y, GREEN_BG[0], GREEN_BG[1], GREEN_BG[2])

    # ========== SCROLLING TEXT ANIMATION ==========

    def _stop_scrolling_text(self) -> None:
        """Stop any running scrolling text animation."""
        self.controller.stop_scrolling_text()

    def _render_single_frame(self, canvas, project_data: Dict, text_x_offset: int) -> None:
        """
        Render a single frame of the single view layout with text at a specific x offset.

        Layout (horizontal gauge):
        - Row 0-10: Project name (scrolling)
        - Row 12-22: Horizontal gauge (10px tall)
        - Row 26-36: Percentage display
        - Row 40-50: "Sprint: N" (current sprint number)
        - Row 54-64: "US: X/Y" (sprint user stories)

        Args:
            canvas: RGB matrix canvas
            project_data: Dict with project info
            text_x_offset: X position for the project name text
        """
        # Get project data
        project_name = project_data.get('name', 'Project')
        progress = project_data.get('progress', {})
        percentage = progress.get('percentage', 0)
        sprint_stats = project_data.get('sprint_stats', {})
        current_sprint = sprint_stats.get('current', 0)
        total_sprints = sprint_stats.get('total', 0)
        story_stats = project_data.get('story_stats', {})
        completed_stories = story_stats.get('completed', 0)
        total_stories = story_stats.get('total', 0)

        # Layout constants for horizontal gauge
        GAUGE_X_START = 2
        GAUGE_X_END = 62
        GAUGE_Y_START = 12
        GAUGE_Y_END = 22

        GRAY_OUTLINE = (100, 100, 100)
        GREEN_FILL = (0, 255, 0)
        WHITE_TEXT = (255, 255, 255)

        # 1. Draw project name at the scrolling position
        if self.controller.font:
            self._draw_text(canvas, project_name, text_x_offset, 8, WHITE_TEXT)

        # 2. Draw horizontal gauge outline (gray rectangle)
        self._draw_outline_rectangle(
            canvas,
            x_start=GAUGE_X_START,
            x_end=GAUGE_X_END,
            y_start=GAUGE_Y_START,
            y_end=GAUGE_Y_END,
            color_rgb=GRAY_OUTLINE
        )

        # 3. Fill horizontal gauge (multi-segment with sprint colors using fixed percentage)
        sprints = project_data.get('sprints', [])
        if sprints:
            # Multi-segment bar with sprint colors, using the actual project percentage
            self._fill_multi_segment_horizontal_bar_fixed(
                canvas,
                x_start=GAUGE_X_START + 1,
                x_end=GAUGE_X_END - 1,
                y_start=GAUGE_Y_START + 1,
                y_end=GAUGE_Y_END - 1,
                total_percentage=percentage,
                sprints=sprints,
                colors=self.SPRINT_COLORS
            )
        else:
            # Fallback to single green color
            self._fill_horizontal_bar(
                canvas,
                x_start=GAUGE_X_START + 1,
                x_end=GAUGE_X_END - 1,
                y_start=GAUGE_Y_START + 1,
                y_end=GAUGE_Y_END - 1,
                percentage=percentage,
                color_rgb=GREEN_FILL
            )

        # 4. Draw percentage centered (row 32)
        if percentage >= 100:
            self._draw_checkmark(canvas, 28, 26)
        elif self.controller.font:
            pct_text = f"{int(percentage)}%"
            self._draw_text_centered(canvas, pct_text, 32, 32, WHITE_TEXT)

        # 5. Draw "Sprint: N" (current sprint number, row 44)
        if self.controller.font and total_sprints > 0:
            sprint_label = f"Sprint: {current_sprint}"
            self._draw_text_centered(canvas, sprint_label, 32, 44, WHITE_TEXT)

        # 6. Draw "US: X/Y" (sprint user stories, row 56)
        if self.controller.font and total_stories > 0:
            us_label = f"US: {completed_stories}/{total_stories}"
            self._draw_text_centered(canvas, us_label, 32, 56, WHITE_TEXT)

    def _start_scrolling_text(self, project_data: Dict) -> None:
        """
        Start scrolling text animation for long project names.

        Args:
            project_data: Dict with project info
        """
        self._stop_scrolling_text()
        self.controller.stop_scroll = threading.Event()

        def scroll():
            project_name = project_data.get('name', 'Project')
            text_width = len(project_name) * 6  # ~6px per character
            x_offset = 64  # Start from right edge (off-screen)

            while not self.controller.stop_scroll.is_set():
                with self.controller._lock:
                    if self.mock_mode or not self.controller.device:
                        break

                    canvas = self.controller._create_canvas()
                    self._render_single_frame(canvas, project_data, x_offset)
                    self.controller._display_canvas(canvas)

                # Move text left (1 pixel at a time for smooth scrolling)
                x_offset -= 1

                # Reset when text fully exits left (continuous loop)
                if x_offset < -text_width:
                    x_offset = 64

                # Frame delay (150ms = ~6.7 FPS for slow, readable scrolling)
                if self.controller.stop_scroll.wait(0.15):
                    break

        self.controller.scroll_thread = threading.Thread(target=scroll, daemon=True)
        self.controller.scroll_thread.start()

    # ========== LAYOUT RENDERERS ==========

    def render_single_view(self, project_data: Dict) -> None:
        """
        Render Single View: Horizontal gauge with project info.

        Layout (64x64 matrix):
        - Rows 0-10: Project name (white text, centered)
        - Rows 12-22: Horizontal gauge (10px tall, full width)
                     Gray outline, multi-segment fill with sprint colors
        - Row 32: Percentage text (white, centered)
        - Row 44: "Sprint: N" (current sprint number)
        - Row 56: "US: X/Y" (sprint user stories completed/total)

        Args:
            project_data: Dict with 'name', 'progress', 'sprint_stats', and 'story_stats'
        """
        self.controller.stop_current_animation()
        self._stop_scrolling_text()

        # Get project data
        project_name = project_data.get('name', 'Project')
        progress = project_data.get('progress', {})
        percentage = progress.get('percentage', 0)
        sprint_stats = project_data.get('sprint_stats', {})
        current_sprint = sprint_stats.get('current', 0)
        total_sprints = sprint_stats.get('total', 0)
        story_stats = project_data.get('story_stats', {})
        completed_stories = story_stats.get('completed', 0)
        total_stories = story_stats.get('total', 0)

        if self.mock_mode:
            print(f"[LED] Single View: {project_name} {percentage}% (Sprint: {current_sprint}) US: {completed_stories}/{total_stories}")
            return

        # If project name is too long, start scrolling animation
        if len(project_name) > 10:
            self._start_scrolling_text(project_data)
            return

        with self.controller._lock:
            canvas = self.controller._create_canvas()

            # Layout constants for horizontal gauge
            GAUGE_X_START = 2
            GAUGE_X_END = 62
            GAUGE_Y_START = 12
            GAUGE_Y_END = 22

            GRAY_OUTLINE = (100, 100, 100)
            GREEN_FILL = (0, 255, 0)
            WHITE_TEXT = (255, 255, 255)

            # 1. Draw project name at top (row 8 - baseline for text)
            if self.controller.font:
                # Short name - display centered
                self._draw_text_centered(canvas, project_name, 32, 8, WHITE_TEXT)

            # 2. Draw horizontal gauge outline (gray rectangle)
            self._draw_outline_rectangle(
                canvas,
                x_start=GAUGE_X_START,
                x_end=GAUGE_X_END,
                y_start=GAUGE_Y_START,
                y_end=GAUGE_Y_END,
                color_rgb=GRAY_OUTLINE
            )

            # 3. Fill horizontal gauge (multi-segment with sprint colors using fixed percentage)
            sprints = project_data.get('sprints', [])
            if sprints:
                # Multi-segment bar with sprint colors, using the actual project percentage
                self._fill_multi_segment_horizontal_bar_fixed(
                    canvas,
                    x_start=GAUGE_X_START + 1,
                    x_end=GAUGE_X_END - 1,
                    y_start=GAUGE_Y_START + 1,
                    y_end=GAUGE_Y_END - 1,
                    total_percentage=percentage,
                    sprints=sprints,
                    colors=self.SPRINT_COLORS
                )
            else:
                # Fallback to single green color
                self._fill_horizontal_bar(
                    canvas,
                    x_start=GAUGE_X_START + 1,
                    x_end=GAUGE_X_END - 1,
                    y_start=GAUGE_Y_START + 1,
                    y_end=GAUGE_Y_END - 1,
                    percentage=percentage,
                    color_rgb=GREEN_FILL
                )

            # 4. Draw percentage centered (row 32)
            if percentage >= 100:
                self._draw_checkmark(canvas, 28, 26)
            elif self.controller.font:
                pct_text = f"{int(percentage)}%"
                self._draw_text_centered(canvas, pct_text, 32, 32, WHITE_TEXT)

            # 5. Draw "Sprint: N" (current sprint number, row 44)
            if self.controller.font and total_sprints > 0:
                sprint_label = f"Sprint: {current_sprint}"
                self._draw_text_centered(canvas, sprint_label, 32, 44, WHITE_TEXT)

            # 6. Draw "US: X/Y" (sprint user stories, row 56)
            if self.controller.font and total_stories > 0:
                us_label = f"US: {completed_stories}/{total_stories}"
                self._draw_text_centered(canvas, us_label, 32, 56, WHITE_TEXT)

            self.controller._display_canvas(canvas)

    def render_sprint_view(self, project_data: Dict, sprints: List[Dict]) -> None:
        """
        Render Sprint View: Top horizontal project bar with outline + 3 vertical sprint bars.

        Layout:
        - Top 10px: Horizontal project bar (blue) with outline, percentage inside
        - Row 11: Sprint labels ("S1", "S2", "S3")
        - Rows 13-63: 3 active sprint bars (green), each ~21px wide
        - Sprint percentages shown inside bars
        - Outline visible even at 0% progress

        Args:
            project_data: Dict with 'progress' key
            sprints: List of sprint dicts with 'name' and 'progress' (first 3 used)
        """
        self.controller.stop_current_animation()
        self._stop_scrolling_text()

        if self.mock_mode:
            project_pct = project_data.get('progress', {}).get('percentage', 0)
            print(f"[LED] Sprint View: Project {project_pct}%")
            for i, sprint in enumerate(sprints[:3]):
                sprint_pct = sprint.get('progress', {}).get('percentage', 0)
                print(f"  Sprint {i+1}: {sprint.get('name', 'N/A')} - {sprint_pct}%")
            return

        with self.controller._lock:
            canvas = self.controller._create_canvas()

            # 1. Top horizontal project bar (10px tall)
            PROJECT_BAR_HEIGHT = 10
            project_progress = project_data.get('progress', {})
            project_percentage = project_progress.get('percentage', 0)

            # Draw filled bar
            self._fill_horizontal_bar(
                canvas,
                x_start=0,
                x_end=self.MATRIX_WIDTH,
                y_start=0,
                y_end=PROJECT_BAR_HEIGHT,
                percentage=project_percentage,
                color_rgb=self.COLOR_PROJECT
            )

            # Draw outline around project bar (visible even at 0%)
            self._draw_outline_rectangle(
                canvas,
                x_start=0,
                x_end=self.MATRIX_WIDTH,
                y_start=0,
                y_end=PROJECT_BAR_HEIGHT,
                color_rgb=(100, 100, 100)  # Dark gray outline
            )

            # Add percentage text or checkmark inside project bar (centered)
            if project_percentage >= 100:
                # Draw checkmark centered in project bar (7px wide, center at x=28)
                self._draw_checkmark(canvas, 28, 1)
            elif self.controller.font:
                text = f"{int(project_percentage)}%"
                text_x = self.MATRIX_WIDTH // 2 - (len(text) * 3)
                text_y = 7  # Centered in 10px bar
                self._draw_text(canvas, text, text_x, text_y, (255, 255, 255))

            # 2. Sprint labels row (row 12)
            LABEL_ROW_Y = 16  # Y baseline for text drawing

            # 3. Three sprint bars (divided equally across width)
            sprint_width = self.MATRIX_WIDTH // 3  # ~21 pixels each
            sprint_bars_y_start = 13
            sprint_bars_y_end = self.MATRIX_HEIGHT

            # Process up to 3 sprints
            for sprint_idx in range(3):
                x_start = sprint_idx * sprint_width
                x_end = (sprint_idx + 1) * sprint_width if sprint_idx < 2 else self.MATRIX_WIDTH

                if sprint_idx < len(sprints):
                    # Sprint exists - draw with data
                    sprint = sprints[sprint_idx]
                    sprint_percentage = sprint.get('progress', {}).get('percentage', 0)

                    # Draw sprint label (S1, S2, S3)
                    label = f"S{sprint_idx + 1}"
                    if self.controller.font:
                        label_x = x_start + 7
                        self._draw_text(canvas, label, label_x, LABEL_ROW_Y, (255, 255, 255))

                    # Draw sprint bar
                    self._fill_vertical_bar(
                        canvas,
                        x_start=x_start,
                        x_end=x_end,
                        y_start=sprint_bars_y_start,
                        y_end=sprint_bars_y_end,
                        percentage=sprint_percentage,
                        color_rgb=self.COLOR_SPRINT
                    )

                    # Add percentage or checkmark inside sprint bar (if space available)
                    if sprint_percentage >= 100:
                        # Draw checkmark centered in sprint bar
                        check_x = x_start + ((x_end - x_start) // 2) - 3
                        self._draw_checkmark(canvas, check_x, 35)
                    elif self.controller.font and sprint_percentage > 0:
                        text = f"{int(sprint_percentage)}%"
                        text_x = x_start + ((x_end - x_start) // 2) - (len(text) * 3)
                        text_y = 40  # Middle of sprint bar
                        self._draw_text(canvas, text, text_x, text_y, (255, 255, 255))
                else:
                    # No sprint - show empty slot with label only
                    label = f"S{sprint_idx + 1}"
                    if self.controller.font:
                        label_x = x_start + 7
                        self._draw_text(canvas, label, label_x, LABEL_ROW_Y, (255, 255, 255))

                    # Draw very dim background to show slot is available
                    for x in range(x_start, x_end):
                        for y in range(sprint_bars_y_start, sprint_bars_y_end):
                            if 0 <= x < self.MATRIX_WIDTH and 0 <= y < self.MATRIX_HEIGHT:
                                canvas.SetPixel(x, y, 10, 10, 10)  # Very dim gray

            self.controller._display_canvas(canvas)

    def render_sprint_horizontal_layout(self, sprints: List[Dict]) -> None:
        """
        Render Sprint Horizontal Layout: 3 horizontal lines with labels, gauges, and percentages.

        Layout (64x64 matrix, 3 lines of 21px each):
        Line 1: "S1" | ████████████████░░░░░ | "75%" (Green)
        Line 2: "S2" | ████████░░░░░░░░░░░░░ | "50%" (Blue)
        Line 3: "S3" | ██░░░░░░░░░░░░░░░░░░░ | "25%" (Yellow)

        Args:
            sprints: List of sprint dicts with 'progress' key (first 3 used)
        """
        self.controller.stop_current_animation()
        self._stop_scrolling_text()

        if self.mock_mode:
            print(f"[LED] Sprint Horizontal Layout: {len(sprints)} sprints")
            for i, sprint in enumerate(sprints[:3]):
                sprint_pct = sprint.get('progress', {}).get('percentage', 0)
                print(f"  S{i+1}: {sprint_pct}%")
            return

        with self.controller._lock:
            canvas = self.controller._create_canvas()

            # Layout constants
            LINE_HEIGHT = 21
            GAUGE_OUTLINE = (100, 100, 100)  # Gray
            TEXT_COLOR = (255, 255, 255)      # White

            # Different colors per sprint
            SPRINT_COLORS = [
                (0, 255, 0),      # Sprint 1: Green
                (0, 100, 255),    # Sprint 2: Blue
                (255, 255, 0)     # Sprint 3: Yellow
            ]

            # Render up to 3 sprints
            for i in range(3):
                y_start = i * LINE_HEIGHT
                y_end = (i + 1) * LINE_HEIGHT
                y_center = y_start + (LINE_HEIGHT // 2)
                y_text = y_center + 3  # Baseline for text (centered vertically)

                # Gauge dimensions (horizontally centered in available space)
                gauge_y_start = y_start + 6  # Vertically center the gauge
                gauge_y_end = y_end - 6

                if i < len(sprints):
                    sprint = sprints[i]
                    percentage = sprint.get('progress', {}).get('percentage', 0)
                    sprint_color = SPRINT_COLORS[i]

                    # 1. Draw label "S1", "S2", "S3" on left
                    label = f"S{i+1}"
                    if self.controller.font:
                        self._draw_text(canvas, label, 2, y_text, TEXT_COLOR)

                    # 2. Draw gauge outline (middle section)
                    self._draw_outline_rectangle(
                        canvas,
                        x_start=14,
                        x_end=38,
                        y_start=gauge_y_start,
                        y_end=gauge_y_end,
                        color_rgb=GAUGE_OUTLINE
                    )

                    # 3. Fill gauge - use multi-segment if user stories available, else solid color
                    user_stories = sprint.get('user_stories', [])
                    if user_stories:
                        # Multi-segment bar with user story colors
                        self._fill_multi_segment_bar(
                            canvas,
                            x_start=15,  # Inside outline
                            x_end=37,
                            y_start=gauge_y_start + 1,
                            y_end=gauge_y_end - 1,
                            user_stories=user_stories,
                            colors=self.USER_STORY_COLORS
                        )
                    else:
                        # Fallback to solid sprint color
                        self._fill_horizontal_bar(
                            canvas,
                            x_start=15,  # Inside outline
                            x_end=37,
                            y_start=gauge_y_start + 1,
                            y_end=gauge_y_end - 1,
                            percentage=percentage,
                            color_rgb=sprint_color
                        )

                    # 4. Draw percentage or checkmark on right
                    if percentage >= 100:
                        # Draw checkmark on right side
                        self._draw_checkmark(canvas, 40, y_text - 8)
                    elif self.controller.font:
                        pct_text = f"{int(percentage)}%"
                        self._draw_text(canvas, pct_text, 40, y_text, TEXT_COLOR)
                else:
                    # No sprint data - show empty slot
                    label = f"S{i+1}"
                    if self.controller.font:
                        self._draw_text(canvas, label, 2, y_text, TEXT_COLOR)

                    # Draw empty gauge outline
                    self._draw_outline_rectangle(
                        canvas,
                        x_start=14,
                        x_end=38,
                        y_start=gauge_y_start,
                        y_end=gauge_y_end,
                        color_rgb=GAUGE_OUTLINE
                    )

            self.controller._display_canvas(canvas)

    def render_user_story_layout(self, sprint_data: Dict, user_stories: List[Dict],
                                   user_story_start_index: int = 0,
                                   all_user_stories: Optional[List[Dict]] = None) -> None:
        """
        Render User Story Layout: 3 horizontal lines - sprint on top, 2 user stories below.

        Layout (64x64 matrix, 3 lines of 21px each):
        Line 1: "S1" | ████████████████░░░░░ | "75%" (Multi-colored segments for all user stories)
        Line 2: "U1" | ████████░░░░░░░░░░░░░ | "50%" (Blue - User Story 1)
        Line 3: "U2" | ██░░░░░░░░░░░░░░░░░░░ | "25%" (Yellow - User Story 2)

        Args:
            sprint_data: Dict with 'progress' key containing sprint progress, optional 'index' for sprint number
            user_stories: List of user story dicts with 'progress' key (first 2 displayed as individual lines)
            user_story_start_index: Starting index for user story labels (default 0, so U1, U2)
            all_user_stories: Optional full list of user stories for sprint gauge segments (used in cycling mode)
        """
        # Use all_user_stories for sprint gauge if provided, otherwise use user_stories
        sprint_gauge_stories = all_user_stories if all_user_stories is not None else user_stories
        self.controller.stop_current_animation()
        self._stop_scrolling_text()

        if self.mock_mode:
            sprint_index = sprint_data.get('index', 0)
            sprint_pct = sprint_data.get('progress', {}).get('percentage', 0)
            num_stories = len(user_stories[:2])
            print(f"[LED] User Story Layout: S{sprint_index + 1} {sprint_pct}% (displaying {1 + num_stories} lines)")
            # Sprint gauge shows horizontal fill with proportional colored segments
            if sprint_gauge_stories:
                percentages = [s.get('progress', {}).get('percentage', 0) for s in sprint_gauge_stories]
                avg_pct = sum(percentages) / len(percentages) if percentages else 0
                print(f"  Sprint gauge: {avg_pct:.0f}% filled [{', '.join(f'{p:.0f}%' for p in percentages)}]")
            # Only print user stories that exist
            for i, story in enumerate(user_stories[:2]):
                story_pct = story.get('progress', {}).get('percentage', 0)
                print(f"  U{user_story_start_index + i + 1}: {story_pct}%")
            return

        with self.controller._lock:
            canvas = self.controller._create_canvas()

            # Layout constants
            LINE_HEIGHT = 21
            GAUGE_OUTLINE = (100, 100, 100)  # Gray
            TEXT_COLOR = (255, 255, 255)      # White

            # Different colors per line
            LINE_COLORS = [
                (0, 255, 0),      # Line 1 (Sprint): Green
                (0, 100, 255),    # Line 2 (User Story 1): Blue
                (255, 255, 0)     # Line 3 (User Story 2): Yellow
            ]

            # Line labels - dynamic based on sprint and user story indices
            sprint_index = sprint_data.get('index', 0)
            LINE_LABELS = [f"S{sprint_index + 1}"] + [f"U{user_story_start_index + i + 1}" for i in range(2)]

            # Data for each line (sprint + only existing user stories)
            line_data = [sprint_data] + user_stories[:2]

            # Only render lines that have actual data (don't show empty slots)
            num_lines = len(line_data)

            # Always use 3-line layout height for consistent gauge sizing
            # This keeps gauges the same size even when there's only 1 user story
            adjusted_line_height = LINE_HEIGHT  # 21px - same as when 2 user stories are present

            # Render only lines that have data
            for i in range(num_lines):
                y_start = i * adjusted_line_height
                y_end = (i + 1) * adjusted_line_height
                y_center = y_start + (adjusted_line_height // 2)
                y_text = y_center + 3  # Baseline for text (centered vertically)

                # Gauge dimensions (horizontally centered in available space)
                gauge_y_start = y_start + 6  # Vertically center the gauge
                gauge_y_end = y_end - 6

                data = line_data[i]
                if data:
                    percentage = data.get('progress', {}).get('percentage', 0)
                    line_color = LINE_COLORS[i] if i < len(LINE_COLORS) else LINE_COLORS[-1]

                    # 1. Draw label "S1", "U1", "U2" on left
                    label = LINE_LABELS[i] if i < len(LINE_LABELS) else f"U{i}"
                    if self.controller.font:
                        self._draw_text(canvas, label, 2, y_text, TEXT_COLOR)

                    # 2. Draw gauge outline (middle section - 24px wide)
                    self._draw_outline_rectangle(
                        canvas,
                        x_start=14,
                        x_end=38,
                        y_start=gauge_y_start,
                        y_end=gauge_y_end,
                        color_rgb=GAUGE_OUTLINE
                    )

                    # 3. Fill gauge based on percentage
                    if i == 0 and sprint_gauge_stories:
                        # Sprint line: multi-segment bar with user story colors
                        self._fill_multi_segment_bar(
                            canvas,
                            x_start=15,  # Inside outline
                            x_end=37,
                            y_start=gauge_y_start + 1,
                            y_end=gauge_y_end - 1,
                            user_stories=sprint_gauge_stories,
                            colors=self.USER_STORY_COLORS
                        )
                    else:
                        # User story lines: single color horizontal bar
                        self._fill_horizontal_bar(
                            canvas,
                            x_start=15,  # Inside outline
                            x_end=37,
                            y_start=gauge_y_start + 1,
                            y_end=gauge_y_end - 1,
                            percentage=percentage,
                            color_rgb=line_color
                        )

                    # 4. Draw percentage or checkmark on right
                    if percentage >= 100:
                        # Draw checkmark on right side (moved up 5 pixels)
                        self._draw_checkmark(canvas, 40, y_text - 8)
                    elif self.controller.font:
                        pct_text = f"{int(percentage)}%"
                        self._draw_text(canvas, pct_text, 40, y_text, TEXT_COLOR)

            self.controller._display_canvas(canvas)
