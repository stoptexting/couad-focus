"""UserStory service for business logic."""
from typing import List, Optional, Dict
import sys
from pathlib import Path
from app.extensions import db
from app.models import UserStory
from app.services.progress_calculator import ProgressCalculator

# Import LED manager components
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared'))
from led_manager.led_manager_client import LEDManagerClient
from led_manager.led_protocol import Priority


class UserStoryService:
    """Service for user story CRUD operations."""

    def _update_leds_after_change(self, user_story: UserStory) -> None:
        """
        Update LEDs after user story modification using project's preferred layout.

        Args:
            user_story: The user story that was modified
        """
        try:
            # Navigate from user story to project: user_story → sprint → project
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
            # Log but don't fail the user story update if LED sync fails
            print(f"LED sync failed: {str(e)}")

    def create_user_story(
        self,
        title: str,
        sprint_id: str,
        description: Optional[str] = None,
        priority: str = 'P2',
        status: str = 'new'
    ) -> UserStory:
        """
        Create a new user story.

        Args:
            title: User story title
            sprint_id: Parent sprint ID
            description: User story description (optional)
            priority: Priority (P0, P1, P2, default: P2)
            status: Status (default: 'new')

        Returns:
            Created user story object
        """
        user_story = UserStory(
            title=title,
            sprint_id=sprint_id,
            description=description,
            priority=priority,
            status=status
        )
        db.session.add(user_story)
        db.session.commit()

        # Update LEDs after creation
        self._update_leds_after_change(user_story)

        return user_story

    def get_user_stories_by_sprint(self, sprint_id: str) -> List[UserStory]:
        """
        Get all user stories for a sprint.

        Args:
            sprint_id: Sprint ID

        Returns:
            List of user stories
        """
        return UserStory.query.filter_by(sprint_id=sprint_id).all()

    def get_user_story_by_id(self, user_story_id: str) -> Optional[UserStory]:
        """
        Get user story by ID.

        Args:
            user_story_id: User story ID

        Returns:
            UserStory object or None if not found
        """
        return UserStory.query.get(user_story_id)

    def get_user_story_with_tasks(self, user_story_id: str) -> Optional[Dict]:
        """
        Get user story with nested tasks.

        Args:
            user_story_id: User story ID

        Returns:
            Dict with user story data including tasks or None if not found
        """
        user_story = self.get_user_story_by_id(user_story_id)
        if not user_story:
            return None

        return user_story.to_dict(include_tasks=True)

    def update_user_story(
        self,
        user_story_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[UserStory]:
        """
        Update a user story.

        Args:
            user_story_id: User story ID
            title: New title (optional)
            description: New description (optional)
            priority: New priority (optional)
            status: New status (optional)

        Returns:
            Updated user story object or None if not found
        """
        user_story = self.get_user_story_by_id(user_story_id)
        if not user_story:
            return None

        if title is not None:
            user_story.title = title
        if description is not None:
            user_story.description = description
        if priority is not None:
            user_story.priority = priority
        if status is not None:
            user_story.status = status

        db.session.commit()

        # Update LEDs after modification (including status changes)
        self._update_leds_after_change(user_story)

        return user_story

    def delete_user_story(self, user_story_id: str) -> bool:
        """
        Delete a user story (cascade deletes tasks).

        Args:
            user_story_id: User story ID

        Returns:
            True if deleted, False if not found
        """
        user_story = self.get_user_story_by_id(user_story_id)
        if not user_story:
            return False

        # Update LEDs before deletion (need user story for project lookup)
        self._update_leds_after_change(user_story)

        db.session.delete(user_story)
        db.session.commit()
        return True

    def get_user_story_progress(self, user_story_id: str) -> Optional[Dict]:
        """
        Calculate progress for a user story.

        Args:
            user_story_id: User story ID

        Returns:
            Dict with progress stats or None if not found
        """
        user_story = self.get_user_story_by_id(user_story_id)
        if not user_story:
            return None

        return ProgressCalculator.calculate_user_story_progress(user_story)
