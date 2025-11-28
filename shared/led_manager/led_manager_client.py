"""LED Manager Client - Client library for communicating with LED manager daemon."""

import json
import socket
import time
from typing import Optional

from .led_protocol import (
    LEDCommand,
    LEDResponse,
    CommandType,
    Priority,
    create_show_symbol_command,
    create_show_animation_command,
    create_show_progress_command,
    create_show_sprint_progress_command,
    create_show_sprint_horizontal_command,
    create_show_single_layout_command,
    create_show_user_story_layout_command,
    create_show_user_story_layout_cycling_command,
    create_clear_command,
    create_show_connected_test_command,
    create_stop_animation_command,
    create_show_gif_command
)


class LEDManagerClient:
    """
    Client for communicating with LED Manager daemon via Unix socket.

    This class provides the same interface as the original LEDController
    but communicates with the daemon instead of controlling hardware directly.
    """

    def __init__(
        self,
        socket_path: str = "/tmp/led-manager.sock",
        timeout: float = 2.0,
        max_retries: int = 3
    ):
        """
        Initialize LED manager client.

        Args:
            socket_path: Path to Unix domain socket
            timeout: Socket timeout in seconds
            max_retries: Maximum number of connection retries
        """
        self.socket_path = socket_path
        self.timeout = timeout
        self.max_retries = max_retries

    def _send_command(self, command: LEDCommand) -> LEDResponse:
        """
        Send command to LED manager daemon.

        Args:
            command: Command to send

        Returns:
            Response from daemon

        Raises:
            ConnectionError: If unable to connect to daemon
            RuntimeError: If command fails
        """
        retries = 0

        while retries < self.max_retries:
            try:
                # Create socket
                client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_socket.settimeout(self.timeout)

                # Connect to daemon
                client_socket.connect(self.socket_path)

                # Send command
                command_json = command.to_json()
                client_socket.sendall(command_json.encode('utf-8'))

                # Receive response - read in chunks until complete
                data_chunks = []
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    data_chunks.append(chunk)
                    # Check if we have a complete JSON by looking for closing brace
                    try:
                        response_json = b''.join(data_chunks).decode('utf-8')
                        # Try to parse - if successful, we have complete JSON
                        response = LEDResponse.from_json(response_json)
                        break
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Not complete yet, continue reading
                        continue

                if not data_chunks:
                    raise RuntimeError("No response received from LED daemon")

                client_socket.close()

                if not response.success:
                    raise RuntimeError(f"Command failed: {response.error}")

                return response

            except (socket.error, OSError) as e:
                retries += 1
                if retries >= self.max_retries:
                    raise ConnectionError(
                        f"Failed to connect to LED manager daemon at {self.socket_path}: {e}"
                    )
                time.sleep(0.1)  # Brief delay before retry

            except Exception as e:
                raise RuntimeError(f"Command error: {e}")

        raise ConnectionError(f"Failed to connect after {self.max_retries} retries")

    def show_symbol(self, symbol: str, priority: Priority = Priority.MEDIUM) -> None:
        """
        Display a static symbol.

        Args:
            symbol: Symbol name (e.g., 'w', 't', 'd', 'error', 'checkmark')
            priority: Command priority
        """
        command = create_show_symbol_command(symbol, priority)
        self._send_command(command)

    def show_animation(
        self,
        animation: str,
        duration: Optional[float] = None,
        frame_delay: float = 0.2,
        priority: Priority = Priority.MEDIUM
    ) -> None:
        """
        Display an animation (looping or for specified duration).

        Args:
            animation: Animation name (e.g., 'wifi_searching', 'boot', 'idle')
            duration: Duration in seconds (None = loop forever)
            frame_delay: Delay between frames in seconds
            priority: Command priority
        """
        command = create_show_animation_command(animation, duration, frame_delay, priority)
        self._send_command(command)

    def show_progress(self, percentage: int, priority: Priority = Priority.LOW) -> None:
        """
        Display progress bar on 8x8 LED matrix.

        Args:
            percentage: Progress value from 0 to 100
            priority: Command priority
        """
        command = create_show_progress_command(percentage, priority)
        self._send_command(command)

    def show_sprint_progress(self, project_percentage: int, sprints: list, priority: Priority = Priority.LOW) -> None:
        """
        Display sprint progress layout on 64x64 LED matrix.

        Shows horizontal project percentage bar at top with outline, followed by
        3 sprint progress bars below with labels S1, S2, S3.

        Args:
            project_percentage: Overall project completion percentage (0-100)
            sprints: List of sprint dicts with 'name' and 'progress' keys
            priority: Command priority
        """
        command = create_show_sprint_progress_command(project_percentage, sprints, priority)
        self._send_command(command)

    def show_sprint_horizontal(self, sprints: list, priority: Priority = Priority.LOW) -> None:
        """
        Display sprint horizontal layout on 64x64 LED matrix.

        Shows 3 horizontal lines with labels (S1, S2, S3), gauges, and percentages.
        Each line uses a different color: Green, Blue, Yellow.

        Args:
            sprints: List of sprint dicts with 'progress' key (first 3 used)
            priority: Command priority
        """
        command = create_show_sprint_horizontal_command(sprints, priority)
        self._send_command(command)

    def show_user_story_layout(self, sprint_data: dict, user_stories: list, priority: Priority = Priority.LOW) -> None:
        """
        Display user story layout on 64x64 LED matrix.

        Shows 3 horizontal lines: sprint progress on top, 2 user stories below.
        Line 1: "S1" with sprint progress (Green)
        Line 2: "U1" with first user story progress (Blue)
        Line 3: "U2" with second user story progress (Yellow)

        Args:
            sprint_data: Dict with 'progress' key containing sprint progress
            user_stories: List of user story dicts with 'progress' key (first 2 used)
            priority: Command priority
        """
        command = create_show_user_story_layout_command(sprint_data, user_stories, priority)
        self._send_command(command)

    def show_user_story_layout_cycling(
        self,
        sprint_data: dict,
        user_stories: list,
        cycle_interval: float = 10.0,
        priority: Priority = Priority.LOW
    ) -> None:
        """
        Display cycling user story layout on 64x64 LED matrix.

        Shows sprint progress on top, cycles through user stories in pairs below.
        Every cycle_interval seconds, advances to the next pair of user stories.

        Args:
            sprint_data: Dict with 'progress' key containing sprint progress
            user_stories: Full list of user story dicts (cycles through all)
            cycle_interval: Seconds between cycling to next pair (default 10)
            priority: Command priority
        """
        command = create_show_user_story_layout_cycling_command(
            sprint_data, user_stories, cycle_interval, priority
        )
        self._send_command(command)

    def show_single_layout(
        self,
        project_name: str,
        percentage: int,
        current_sprint: int,
        total_sprints: int,
        completed_stories: int = 0,
        total_stories: int = 0,
        sprints: list = None,
        priority: Priority = Priority.LOW
    ) -> None:
        """
        Display single layout with vertical gauge on 64x64 LED matrix.

        Shows project name at top, vertical gauge in middle with gray outline
        and multi-segment fill with sprint colors, and percentage/sprint count/story count at bottom.

        Args:
            project_name: Project name to display
            percentage: Project completion percentage (0-100)
            current_sprint: Number of completed sprints
            total_sprints: Total number of sprints
            completed_stories: Number of completed user stories
            total_stories: Total number of user stories
            sprints: Optional list of sprint dicts with 'progress' for multi-segment display
            priority: Command priority
        """
        command = create_show_single_layout_command(
            project_name, percentage, current_sprint, total_sprints,
            completed_stories, total_stories, sprints, priority
        )
        self._send_command(command)

    def stop_current_animation(self, priority: Priority = Priority.HIGH) -> None:
        """
        Stop any currently running animation.

        Args:
            priority: Command priority
        """
        command = create_stop_animation_command(priority)
        self._send_command(command)

    def clear(self, priority: Priority = Priority.MEDIUM) -> None:
        """
        Clear the LED matrix (all LEDs off).

        Args:
            priority: Command priority
        """
        command = create_clear_command(priority)
        self._send_command(command)

    # Convenience methods matching the original LEDController API

    def show_connected_test(self) -> None:
        """Show 'CONNECTED' text with green checkmark to verify LED communication."""
        command = create_show_connected_test_command(priority=Priority.HIGH)
        self._send_command(command)

    def show_boot(self) -> None:
        """Show boot animation."""
        self.show_animation("boot", duration=2, frame_delay=0.3, priority=Priority.HIGH)

    def show_wifi_searching(self) -> None:
        """Show Wi-Fi searching animation (loops until stopped)."""
        self.show_animation("wifi_searching", frame_delay=0.2, priority=Priority.MEDIUM)

    def show_wifi_connected(self) -> None:
        """Show Wi-Fi connected (W symbol)."""
        self.show_symbol("w", priority=Priority.MEDIUM)

    def show_wifi_error(self) -> None:
        """Show Wi-Fi error (barred symbol)."""
        self.show_symbol("wifi_error", priority=Priority.HIGH)

    def show_tunnel_active(self) -> None:
        """Show tunnel active (T symbol)."""
        self.show_symbol("t", priority=Priority.MEDIUM)

    def show_discord_active(self) -> None:
        """Show Discord active (D symbol)."""
        self.show_symbol("d", priority=Priority.MEDIUM)

    def show_success(self) -> None:
        """Show success checkmark."""
        self.show_symbol("checkmark", priority=Priority.HIGH)

    def show_error(self) -> None:
        """Show error symbol."""
        self.show_symbol("error", priority=Priority.HIGH)

    def show_activity(self, duration: float = 1.0) -> None:
        """
        Show brief activity indicator.

        Args:
            duration: Duration in seconds
        """
        self.show_animation("activity", duration=duration, frame_delay=0.1, priority=Priority.LOW)

    def show_idle(self) -> None:
        """Show idle animation (rotating dot)."""
        self.show_animation("idle", frame_delay=0.3, priority=Priority.LOW)

    def show_gif(self, gif_name: str, loop: bool = True, priority: Priority = Priority.MEDIUM) -> None:
        """
        Display a GIF animation on the LED matrix.

        Args:
            gif_name: Name of the GIF (without .gif extension), e.g., 'subway', 'brainrot'
            loop: Whether to loop the animation (default True = loop forever)
            priority: Command priority
        """
        command = create_show_gif_command(gif_name, loop, priority)
        self._send_command(command)

    def test(self) -> None:
        """Run a test sequence to verify LED functionality."""
        command = LEDCommand(CommandType.TEST, Priority.HIGH)
        self._send_command(command)

    def cleanup(self) -> None:
        """Clean up resources (compatibility method)."""
        self.clear()

    # Context manager support
    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
