#!/usr/bin/env python3
"""Example: How server will use LED Manager for task progress."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.led_manager.led_manager_client import LEDManagerClient
from shared.led_manager.led_protocol import Priority


class TaskProgressLED:
    """LED progress display for task management server."""

    def __init__(self):
        """Initialize LED client."""
        self.led = LEDManagerClient()

    def update_task_progress(self, completed: int, total: int) -> None:
        """
        Update LED display with task completion progress.

        Args:
            completed: Number of completed tasks
            total: Total number of tasks
        """
        if total == 0:
            percentage = 0
        else:
            percentage = int((completed / total) * 100)

        print(f"Updating LED: {completed}/{total} tasks ({percentage}%)")

        # Update LED with LOW priority (can be interrupted by bootmanager)
        self.led.show_progress(percentage, priority=Priority.LOW)


def example_task_workflow():
    """Simulate task management workflow with LED updates."""
    progress = TaskProgressLED()

    print("Task Management LED Example")
    print("=" * 50)

    # Simulate creating tasks
    tasks = ["Task 1", "Task 2", "Task 3", "Task 4"]
    completed_tasks = []

    print(f"\n{len(tasks)} tasks created")
    progress.update_task_progress(0, len(tasks))
    input("Press Enter to complete Task 1...")

    # Complete tasks one by one
    for i, task in enumerate(tasks):
        completed_tasks.append(task)
        print(f"\n✓ Completed: {task}")
        progress.update_task_progress(len(completed_tasks), len(tasks))

        if i < len(tasks) - 1:
            input(f"Press Enter to complete {tasks[i+1]}...")

    print("\n✓ All tasks completed!")
    print("LED shows 100% progress (all 8 rows lit)")


if __name__ == "__main__":
    try:
        example_task_workflow()
    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure LED manager daemon is running:")
        print("  sudo systemctl status led-manager.service")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
