#!/usr/bin/env python3
"""LED Manager Daemon - Socket-based LED controller service."""

import os
import sys
import socket
import signal
import logging
import threading
import queue
from pathlib import Path
from typing import Optional

# Fix imports to work both as module and as script
if __name__ == "__main__" and __package__ is None:
    # Add parent directory to path when run as script
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from led_manager.led_hardware import LEDHardwareController
    from led_manager.led_layout_renderer import LEDLayoutRenderer
    from led_manager.led_protocol import (
        LEDCommand,
        LEDResponse,
        CommandType,
        Priority
    )
else:
    from .led_hardware import LEDHardwareController
    from .led_layout_renderer import LEDLayoutRenderer
    from .led_protocol import (
        LEDCommand,
        LEDResponse,
        CommandType,
        Priority
    )


class LEDManagerDaemon:
    """LED Manager daemon that listens for commands via Unix socket."""

    def __init__(
        self,
        socket_path: str = "/tmp/led-manager.sock",
        mock_mode: bool = False
    ):
        """
        Initialize LED manager daemon.

        Args:
            socket_path: Path to Unix domain socket
            mock_mode: Run in mock mode without hardware
        """
        self.socket_path = socket_path
        self.mock_mode = mock_mode
        self.server_socket: Optional[socket.socket] = None
        self.running = False

        # Command queue with priority
        self.command_queue: queue.PriorityQueue = queue.PriorityQueue()

        # LED hardware controller
        self.led_controller = LEDHardwareController(mock_mode=mock_mode)

        # Worker thread for processing commands
        self.worker_thread: Optional[threading.Thread] = None

        # Cycling state for user story layout
        self.cycling_thread: Optional[threading.Thread] = None
        self.stop_cycling = threading.Event()

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('led-manager')

    def _cleanup_socket(self) -> None:
        """Remove existing socket file if it exists."""
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
                self.logger.info(f"Removed existing socket: {self.socket_path}")
            except OSError as e:
                self.logger.error(f"Failed to remove socket: {e}")

    def start(self) -> None:
        """Start the LED manager daemon."""
        self.logger.info("Starting LED Manager Daemon...")
        self.logger.info(f"Socket path: {self.socket_path}")
        self.logger.info(f"Mock mode: {self.mock_mode}")

        # Ensure socket directory exists
        socket_dir = os.path.dirname(self.socket_path)
        if not os.path.exists(socket_dir):
            self.logger.info(f"Creating socket directory: {socket_dir}")
            os.makedirs(socket_dir, mode=0o755, exist_ok=True)

        # Clean up any existing socket
        self._cleanup_socket()

        # Create Unix domain socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            self.logger.info(f"Attempting to bind to {self.socket_path}")
            self.server_socket.bind(self.socket_path)
            self.logger.info("Bind successful")

            self.server_socket.listen(5)
            self.logger.info("Listen successful")

            # Set socket permissions (readable/writable by all for simplicity)
            # In production, use proper permissions
            self.logger.info("Setting socket permissions")
            os.chmod(self.socket_path, 0o666)
            self.logger.info("Permissions set")

            self.logger.info(f"Listening on {self.socket_path}")

            # Start worker thread
            self.running = True
            self.worker_thread = threading.Thread(target=self._command_worker, daemon=True)
            self.worker_thread.start()

            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Accept connections
            while self.running:
                try:
                    client_socket, _ = self.server_socket.accept()
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    client_thread.start()
                except OSError:
                    if not self.running:
                        break
                    raise

        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self.shutdown()

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _command_worker(self) -> None:
        """Worker thread that processes commands from the queue."""
        self.logger.info("Command worker started")

        while self.running:
            try:
                # Get command from queue (blocks with timeout)
                # Priority queue: lower number = higher priority
                # We negate priority value so HIGH (2) becomes -2 (processed first)
                priority, command = self.command_queue.get(timeout=0.5)

                self.logger.info(f"Processing command: {command.command.value} (priority: {-priority})")

                # Execute command
                self._execute_command(command)

                self.command_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")

        self.logger.info("Command worker stopped")

    def _execute_command(self, command: LEDCommand) -> None:
        """
        Execute a LED command.

        Args:
            command: Command to execute
        """
        try:
            self.logger.info(f"Executing command: {command.command.value}")

            # Stop any running animations before any display command
            # This prevents cycling/scrolling/GIF animations from "popping" over other displays
            # Note: SHOW_USER_STORY_LAYOUT_CYCLING handles its own stop, and
            # STOP_ANIMATION/SHUTDOWN don't need this
            if command.command not in [
                CommandType.SHOW_USER_STORY_LAYOUT_CYCLING,
                CommandType.STOP_ANIMATION,
                CommandType.SHUTDOWN
            ]:
                self._stop_user_story_cycling()
                self.led_controller.stop_all_animations()

            if command.command == CommandType.SHOW_SYMBOL:
                symbol = command.params.get("symbol")
                self.logger.info(f"Showing symbol: {symbol}")
                self.led_controller.show_symbol(symbol)
                self.logger.info(f"Symbol display complete")

            elif command.command == CommandType.SHOW_ANIMATION:
                animation = command.params.get("animation")
                duration = command.params.get("duration")
                frame_delay = command.params.get("frame_delay", 0.2)
                self.logger.info(f"Showing animation: {animation}, duration: {duration}")
                self.led_controller.show_animation(animation, duration, frame_delay)
                self.logger.info(f"Animation started")

            elif command.command == CommandType.SHOW_PROGRESS:
                percentage = command.params.get("percentage", 0)
                self.logger.info(f"Showing progress: {percentage}%")
                self.led_controller.show_progress(percentage)
                self.logger.info(f"Progress display complete")

            elif command.command == CommandType.SHOW_SPRINT_PROGRESS:
                project_percentage = command.params.get("project_percentage", 0)
                sprints = command.params.get("sprints", [])
                self.logger.info(f"Showing sprint progress: {project_percentage}% with {len(sprints)} sprints")

                # Create layout renderer and render sprint view
                try:
                    renderer = LEDLayoutRenderer(self.led_controller)
                    project_data = {"progress": {"percentage": project_percentage}}
                    renderer.render_sprint_view(project_data, sprints)
                    self.logger.info(f"Sprint view rendered successfully")
                except Exception as e:
                    self.logger.error(f"Error rendering sprint view: {e}")

            elif command.command == CommandType.SHOW_SPRINT_HORIZONTAL:
                sprints = command.params.get("sprints", [])
                self.logger.info(f"Showing sprint horizontal layout: {len(sprints)} sprints")

                # Create layout renderer and render sprint horizontal layout
                try:
                    renderer = LEDLayoutRenderer(self.led_controller)
                    renderer.render_sprint_horizontal_layout(sprints)
                    self.logger.info(f"Sprint horizontal layout rendered successfully")
                except Exception as e:
                    self.logger.error(f"Error rendering sprint horizontal layout: {e}")

            elif command.command == CommandType.SHOW_USER_STORY_LAYOUT:
                sprint_data = command.params.get("sprint_data", {})
                user_stories = command.params.get("user_stories", [])
                self.logger.info(f"Showing user story layout: sprint + {len(user_stories)} user stories")

                # Stop any cycling before showing static layout
                self._stop_user_story_cycling()

                # Create layout renderer and render user story layout
                try:
                    renderer = LEDLayoutRenderer(self.led_controller)
                    renderer.render_user_story_layout(sprint_data, user_stories)
                    self.logger.info(f"User story layout rendered successfully")
                except Exception as e:
                    self.logger.error(f"Error rendering user story layout: {e}")

            elif command.command == CommandType.SHOW_USER_STORY_LAYOUT_CYCLING:
                sprint_data = command.params.get("sprint_data", {})
                user_stories = command.params.get("user_stories", [])
                cycle_interval = command.params.get("cycle_interval", 10.0)
                self.logger.info(f"Showing cycling user story layout: sprint + {len(user_stories)} user stories, interval={cycle_interval}s")

                try:
                    self._start_user_story_cycling(sprint_data, user_stories, cycle_interval)
                except Exception as e:
                    self.logger.error(f"Error starting cycling user story layout: {e}")

            elif command.command == CommandType.SHOW_SINGLE_LAYOUT:
                project_name = command.params.get("project_name", "")
                percentage = command.params.get("percentage", 0)
                current_sprint = command.params.get("current_sprint", 0)
                total_sprints = command.params.get("total_sprints", 0)
                completed_stories = command.params.get("completed_stories", 0)
                total_stories = command.params.get("total_stories", 0)
                sprints = command.params.get("sprints", [])
                self.logger.info(f"Showing single layout: {project_name} at {percentage}% ({current_sprint}/{total_sprints} sprints, {completed_stories}/{total_stories} stories)")

                # Create layout renderer and render single view
                try:
                    renderer = LEDLayoutRenderer(self.led_controller)
                    project_data = {
                        "name": project_name,
                        "progress": {"percentage": percentage},
                        "sprint_stats": {
                            "current": current_sprint,
                            "total": total_sprints
                        },
                        "story_stats": {
                            "completed": completed_stories,
                            "total": total_stories
                        },
                        "sprints": sprints  # For multi-segment vertical bar
                    }
                    renderer.render_single_view(project_data)
                    self.logger.info(f"Single layout rendered successfully")
                except Exception as e:
                    self.logger.error(f"Error rendering single layout: {e}")

            elif command.command == CommandType.SHOW_GIF:
                gif_name = command.params.get("gif_name")
                loop = command.params.get("loop", True)
                self.logger.info(f"Showing GIF: {gif_name}, loop={loop}")
                self.led_controller.show_gif(gif_name, loop=loop)
                self.logger.info(f"GIF animation started: {gif_name}")

            elif command.command == CommandType.STOP_ANIMATION:
                self.logger.info("Stopping animation")
                self.led_controller.stop_current_animation()

            elif command.command == CommandType.CLEAR:
                self.logger.info("Clearing display")
                self.led_controller.clear()

            elif command.command == CommandType.SHOW_CONNECTED_TEST:
                self.logger.info("Showing connected test")
                self.led_controller.show_connected_test()
                self.logger.info("Connected test complete")

            elif command.command == CommandType.TEST:
                self.logger.info("Running test sequence")
                self.led_controller.test()

            elif command.command == CommandType.SHUTDOWN:
                self.logger.info("Shutdown command received")
                self.running = False

        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _start_user_story_cycling(
        self,
        sprint_data: dict,
        user_stories: list,
        cycle_interval: float
    ) -> None:
        """
        Start cycling through user stories in pairs.

        Shows stories 0-1, then 2-3, then 4-5, etc., wrapping around.

        Args:
            sprint_data: Sprint progress data
            user_stories: Full list of user stories
            cycle_interval: Seconds between cycles
        """
        # Stop any existing cycling
        self._stop_user_story_cycling()

        if len(user_stories) <= 2:
            # No cycling needed - just render once
            renderer = LEDLayoutRenderer(self.led_controller)
            renderer.render_user_story_layout(sprint_data, user_stories)
            return

        def cycle():
            current_index = 0
            total_stories = len(user_stories)

            while not self.stop_cycling.is_set():
                # Get current pair of stories
                end_index = min(current_index + 2, total_stories)
                current_pair = user_stories[current_index:end_index]

                # Render current pair (with all stories for sprint gauge)
                try:
                    renderer = LEDLayoutRenderer(self.led_controller)
                    renderer.render_user_story_layout(sprint_data, current_pair, current_index,
                                                       all_user_stories=user_stories)
                    self.logger.info(f"Cycling: showing stories {current_index + 1}-{end_index} of {total_stories}")
                except Exception as e:
                    self.logger.error(f"Error rendering cycling user story layout: {e}")

                # Wait for interval (or stop signal)
                if self.stop_cycling.wait(cycle_interval):
                    break

                # Move to next pair
                current_index += 2
                if current_index >= total_stories:
                    current_index = 0  # Wrap around

        self.cycling_thread = threading.Thread(target=cycle, daemon=True)
        self.cycling_thread.start()
        self.logger.info(f"User story cycling started: {len(user_stories)} stories, {cycle_interval}s interval")

    def _stop_user_story_cycling(self) -> None:
        """Stop user story cycling if running."""
        if self.cycling_thread and self.cycling_thread.is_alive():
            self.stop_cycling.set()
            self.cycling_thread.join(timeout=1.0)
            self.stop_cycling.clear()
            self.cycling_thread = None
            self.logger.info("User story cycling stopped")

    def _handle_client(self, client_socket: socket.socket) -> None:
        """
        Handle a client connection.

        Args:
            client_socket: Client socket
        """
        try:
            # Receive command (max 4KB)
            data = client_socket.recv(4096)

            if not data:
                self.logger.warning("Received empty data from client")
                return

            # Parse command
            command_json = data.decode('utf-8')
            self.logger.info(f"Received command JSON: {command_json}")
            command = LEDCommand.from_json(command_json)
            self.logger.info(f"Parsed command: {command.command.value}, params: {command.params}")

            # Add to queue (negate priority for correct ordering)
            priority_value = -command.priority.value
            self.command_queue.put((priority_value, command))
            self.logger.info(f"Command added to queue (priority: {priority_value})")

            # Send response
            response = LEDResponse(success=True, message="Command queued")
            client_socket.sendall(response.to_json().encode('utf-8'))

        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            response = LEDResponse(success=False, error=str(e))
            try:
                client_socket.sendall(response.to_json().encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()

    def shutdown(self) -> None:
        """Shutdown the daemon."""
        self.logger.info("Shutting down LED Manager Daemon...")

        self.running = False

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        # Wait for worker thread
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)

        # Stop any cycling
        self._stop_user_story_cycling()

        # Cleanup LED controller
        self.led_controller.cleanup()

        # Remove socket file
        self._cleanup_socket()

        self.logger.info("Shutdown complete")


def main():
    """Main entry point."""
    # Use /tmp for socket (more reliable permissions than /var/run)
    socket_path = os.getenv("LED_SOCKET_PATH", "/tmp/led-manager.sock")
    mock_mode = os.getenv("LED_MOCK_MODE", "false").lower() == "true"

    daemon = LEDManagerDaemon(socket_path=socket_path, mock_mode=mock_mode)

    try:
        daemon.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
