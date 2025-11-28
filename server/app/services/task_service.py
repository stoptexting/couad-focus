"""Task service for business logic."""
from typing import List, Optional, Dict
from datetime import datetime
import sys
from pathlib import Path

from app.extensions import db
from app.models import Task
from flask import current_app

# Import LED manager components
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared'))
from led_manager.led_manager_client import LEDManagerClient
from led_manager.led_protocol import Priority


class TaskService:
    """Service for task CRUD operations and progress tracking."""

    def __init__(self):
        """Initialize task service."""
        pass

    def _update_leds_after_change(self, task: Task) -> None:
        """
        Update LEDs after task modification using project's preferred layout.

        Args:
            task: The task that was modified
        """
        try:
            # Navigate from task to project: task → user_story → sprint → project
            user_story = task.user_story
            if not user_story:
                return

            sprint = user_story.sprint
            if not sprint:
                return

            project = sprint.project
            if not project:
                return

            # Get project's preferred layout (default to 'single')
            preferred_layout = project.preferred_layout or 'single'

            # Import project service to get full tree with progress
            from app.services.project_service import ProjectService
            project_service = ProjectService()
            project_data = project_service.get_project_with_full_tree(project.id)

            if not project_data:
                return

            # Get progress percentage
            progress = project_data.get('progress', {})
            percentage = int(progress.get('percentage', 0))

            # Connect to LED daemon
            client = LEDManagerClient()

            # Sync based on preferred layout
            if preferred_layout == 'sprint_view':
                # Send minimal sprint data (only name and progress) to avoid huge JSON payloads
                sprints = project_data.get('sprints', [])
                minimal_sprints = [
                    {
                        'name': sprint.get('name', ''),
                        'progress': sprint.get('progress', {})
                    }
                    for sprint in sprints
                ]
                client.show_sprint_horizontal(minimal_sprints, priority=Priority.MEDIUM)

            elif preferred_layout == 'single':
                project_name = project_data.get('name', 'Project')
                sprints = project_data.get('sprints', [])
                total_sprints = len(sprints)
                completed_sprints = sum(1 for s in sprints if s.get('progress', {}).get('percentage', 0) >= 100)

                # Calculate user story counts
                total_user_stories = sum(len(s.get('user_stories', [])) for s in sprints)
                completed_user_stories = sum(
                    len([us for us in s.get('user_stories', [])
                         if us.get('progress', {}).get('percentage', 0) == 100])
                    for s in sprints
                )

                client.show_single_layout(
                    project_name=project_name,
                    percentage=percentage,
                    current_sprint=completed_sprints,
                    total_sprints=total_sprints,
                    completed_stories=completed_user_stories,
                    total_stories=total_user_stories,
                    priority=Priority.MEDIUM
                )

            else:
                # Fallback: use simple progress bar
                client.show_progress(percentage, priority=Priority.MEDIUM)

        except Exception as e:
            # Log but don't fail the task update if LED sync fails
            print(f"LED sync failed: {str(e)}")

    def create_task(
        self,
        title: str,
        user_story_id: str,
        description: Optional[str] = None
    ) -> Task:
        """
        Create a new task.

        Args:
            title: Task title
            user_story_id: Parent user story ID
            description: Task description (optional)

        Returns:
            Created task object
        """
        task = Task(
            title=title,
            user_story_id=user_story_id,
            description=description,
            status='new'
        )
        db.session.add(task)
        db.session.commit()

        # Update LEDs after creation
        self._update_leds_after_change(task)

        return task

    def get_all_tasks(self) -> List[Task]:
        """
        Get all tasks.

        Returns:
            List of all tasks
        """
        return Task.query.all()

    def get_tasks_by_user_story(self, user_story_id: str) -> List[Task]:
        """
        Get all tasks for a user story.

        Args:
            user_story_id: User story ID

        Returns:
            List of tasks
        """
        return Task.query.filter_by(user_story_id=user_story_id).all()

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task object or None if not found
        """
        return Task.query.get(task_id)

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Task]:
        """
        Update a task.

        Args:
            task_id: Task ID
            title: New title (optional)
            description: New description (optional)
            status: New status (optional)

        Returns:
            Updated task object or None if not found
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return None

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status

        task.updated_at = datetime.utcnow()
        db.session.commit()

        # Update LEDs after modification
        self._update_leds_after_change(task)

        return task

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return False

        # Update LEDs before deletion (need task for project lookup)
        self._update_leds_after_change(task)

        db.session.delete(task)
        db.session.commit()

        return True

    def get_progress_stats(self) -> Dict[str, int]:
        """
        Calculate progress statistics.

        Returns:
            Dictionary with percentage, total_tasks, and completed_tasks
        """
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(status='completed').count()

        if total_tasks == 0:
            percentage = 0
        else:
            percentage = round((completed_tasks / total_tasks) * 100)

        return {
            'percentage': percentage,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        }
