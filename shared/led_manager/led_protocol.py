"""LED Manager IPC Protocol definitions."""

import json
from typing import Dict, Any, Optional
from enum import Enum


class CommandType(Enum):
    """Available LED command types."""
    SHOW_SYMBOL = "show_symbol"
    SHOW_ANIMATION = "show_animation"
    SHOW_PROGRESS = "show_progress"
    SHOW_SPRINT_PROGRESS = "show_sprint_progress"
    SHOW_SPRINT_HORIZONTAL = "show_sprint_horizontal"
    SHOW_SINGLE_LAYOUT = "show_single_layout"
    SHOW_USER_STORY_LAYOUT = "show_user_story_layout"
    SHOW_USER_STORY_LAYOUT_CYCLING = "show_user_story_layout_cycling"
    STOP_ANIMATION = "stop_animation"
    SHOW_GIF = "show_gif"
    CLEAR = "clear"
    TEST = "test"
    SHOW_CONNECTED_TEST = "show_connected_test"
    SHUTDOWN = "shutdown"


class Priority(Enum):
    """Command priority levels."""
    LOW = 0      # Idle animations, progress updates
    MEDIUM = 1   # Boot sequence, status symbols
    HIGH = 2     # Errors, critical status


class LEDCommand:
    """Represents a command to send to the LED manager."""

    def __init__(
        self,
        command: CommandType,
        priority: Priority = Priority.MEDIUM,
        **kwargs
    ):
        """
        Initialize LED command.

        Args:
            command: Command type
            priority: Command priority
            **kwargs: Additional command parameters
        """
        self.command = command
        self.priority = priority
        self.params = kwargs

    def to_json(self) -> str:
        """
        Serialize command to JSON.

        Returns:
            JSON string representation
        """
        data = {
            "command": self.command.value,
            "priority": self.priority.value,
            "params": self.params
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'LEDCommand':
        """
        Deserialize command from JSON.

        Args:
            json_str: JSON string

        Returns:
            LEDCommand instance
        """
        data = json.loads(json_str)
        command = CommandType(data["command"])
        priority = Priority(data["priority"])
        params = data.get("params", {})
        return cls(command, priority, **params)


class LEDResponse:
    """Response from LED manager."""

    def __init__(self, success: bool, message: str = "", error: Optional[str] = None):
        """
        Initialize response.

        Args:
            success: Whether command succeeded
            message: Response message
            error: Error message if failed
        """
        self.success = success
        self.message = message
        self.error = error

    def to_json(self) -> str:
        """
        Serialize response to JSON.

        Returns:
            JSON string representation
        """
        data = {
            "success": self.success,
            "message": self.message,
            "error": self.error
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'LEDResponse':
        """
        Deserialize response from JSON.

        Args:
            json_str: JSON string

        Returns:
            LEDResponse instance
        """
        data = json.loads(json_str)
        return cls(
            success=data["success"],
            message=data.get("message", ""),
            error=data.get("error")
        )


# Helper functions for creating common commands
def create_show_symbol_command(symbol: str, priority: Priority = Priority.MEDIUM) -> LEDCommand:
    """Create command to show a symbol."""
    return LEDCommand(CommandType.SHOW_SYMBOL, priority, symbol=symbol)


def create_show_animation_command(
    animation: str,
    duration: Optional[float] = None,
    frame_delay: float = 0.2,
    priority: Priority = Priority.MEDIUM
) -> LEDCommand:
    """Create command to show an animation."""
    return LEDCommand(
        CommandType.SHOW_ANIMATION,
        priority,
        animation=animation,
        duration=duration,
        frame_delay=frame_delay
    )


def create_show_progress_command(percentage: int, priority: Priority = Priority.LOW) -> LEDCommand:
    """Create command to show progress bar."""
    return LEDCommand(CommandType.SHOW_PROGRESS, priority, percentage=percentage)


def create_clear_command(priority: Priority = Priority.MEDIUM) -> LEDCommand:
    """Create command to clear display."""
    return LEDCommand(CommandType.CLEAR, priority)


def create_show_connected_test_command(priority: Priority = Priority.HIGH) -> LEDCommand:
    """Create command to show connected test."""
    return LEDCommand(CommandType.SHOW_CONNECTED_TEST, priority)


def create_stop_animation_command(priority: Priority = Priority.HIGH) -> LEDCommand:
    """Create command to stop current animation."""
    return LEDCommand(CommandType.STOP_ANIMATION, priority)


def create_show_sprint_progress_command(
    project_percentage: int,
    sprints: list,
    priority: Priority = Priority.LOW
) -> LEDCommand:
    """
    Create command to show sprint progress with project percentage at top.

    Args:
        project_percentage: Overall project completion percentage (0-100)
        sprints: List of sprint dicts with 'name' and 'progress' keys
        priority: Command priority

    Returns:
        LEDCommand for sprint progress display
    """
    return LEDCommand(
        CommandType.SHOW_SPRINT_PROGRESS,
        priority,
        project_percentage=project_percentage,
        sprints=sprints
    )


def create_show_single_layout_command(
    project_name: str,
    percentage: int,
    current_sprint: int,
    total_sprints: int,
    completed_stories: int = 0,
    total_stories: int = 0,
    sprints: list = None,
    priority: Priority = Priority.LOW
) -> LEDCommand:
    """
    Create command to show single layout with vertical gauge.

    Args:
        project_name: Project name to display
        percentage: Project completion percentage (0-100)
        current_sprint: Number of completed sprints
        total_sprints: Total number of sprints
        completed_stories: Number of completed user stories
        total_stories: Total number of user stories
        sprints: Optional list of sprint dicts with 'progress' for multi-segment display
        priority: Command priority

    Returns:
        LEDCommand for single layout display
    """
    return LEDCommand(
        CommandType.SHOW_SINGLE_LAYOUT,
        priority,
        project_name=project_name,
        percentage=percentage,
        current_sprint=current_sprint,
        total_sprints=total_sprints,
        completed_stories=completed_stories,
        total_stories=total_stories,
        sprints=sprints or []
    )


def create_show_sprint_horizontal_command(
    sprints: list,
    priority: Priority = Priority.LOW
) -> LEDCommand:
    """
    Create command to show sprint horizontal layout.

    Args:
        sprints: List of sprint dicts with 'progress' key (first 3 used)
        priority: Command priority

    Returns:
        LEDCommand for sprint horizontal layout display
    """
    return LEDCommand(
        CommandType.SHOW_SPRINT_HORIZONTAL,
        priority,
        sprints=sprints
    )


def create_show_user_story_layout_command(
    sprint_data: dict,
    user_stories: list,
    priority: Priority = Priority.LOW
) -> LEDCommand:
    """
    Create command to show user story layout.

    Args:
        sprint_data: Dict with 'progress' key containing sprint progress
        user_stories: List of user story dicts with 'progress' key (first 2 used)
        priority: Command priority

    Returns:
        LEDCommand for user story layout display
    """
    return LEDCommand(
        CommandType.SHOW_USER_STORY_LAYOUT,
        priority,
        sprint_data=sprint_data,
        user_stories=user_stories
    )


def create_show_gif_command(
    gif_name: str,
    loop: bool = True,
    priority: Priority = Priority.MEDIUM
) -> LEDCommand:
    """
    Create command to show a GIF animation on the LED matrix.

    Args:
        gif_name: Name of the GIF (without extension) from gifs/ directory
        loop: Whether to loop the GIF (default True)
        priority: Command priority

    Returns:
        LEDCommand for GIF display
    """
    return LEDCommand(
        CommandType.SHOW_GIF,
        priority,
        gif_name=gif_name,
        loop=loop
    )


def create_show_user_story_layout_cycling_command(
    sprint_data: dict,
    user_stories: list,
    cycle_interval: float = 10.0,
    priority: Priority = Priority.LOW
) -> LEDCommand:
    """
    Create command to show cycling user story layout.

    Cycles through all user stories in pairs (2 at a time) on the LED display.
    Each cycle shows sprint progress + 2 user stories, then advances to the next pair.

    Args:
        sprint_data: Dict with 'progress' key containing sprint progress
        user_stories: Full list of user story dicts (cycles through all)
        cycle_interval: Seconds between cycling to next pair (default 10.0)
        priority: Command priority

    Returns:
        LEDCommand for cycling user story layout display
    """
    return LEDCommand(
        CommandType.SHOW_USER_STORY_LAYOUT_CYCLING,
        priority,
        sprint_data=sprint_data,
        user_stories=user_stories,
        cycle_interval=cycle_interval
    )
