"""Project service for business logic."""
from typing import List, Optional, Dict
import sys
from pathlib import Path
from app.extensions import db
from app.models import Project
from app.services.progress_calculator import ProgressCalculator

# Import LED manager components
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared'))
from led_manager.led_manager_client import LEDManagerClient
from led_manager.led_protocol import Priority


class ProjectService:
    """Service for project CRUD operations."""

    def _update_leds_after_change(self, project: Project) -> None:
        """
        Update LEDs after project modification using project's preferred layout.

        Args:
            project: The project that was modified
        """
        try:
            # Get project's preferred layout (default to 'single')
            preferred_layout = project.preferred_layout or 'single'

            # Get full project tree with progress
            project_data = self.get_project_with_full_tree(project.id)

            if not project_data:
                return

            # Get progress percentage
            progress = project_data.get('progress', {})
            percentage = int(progress.get('percentage', 0))

            # Connect to LED daemon
            client = LEDManagerClient()

            # Sync based on preferred layout
            if preferred_layout == 'sprint_view':
                # Send sprint data including user stories for multi-segment display
                sprints = project_data.get('sprints', [])
                minimal_sprints = [
                    {
                        'name': sprint.get('name', ''),
                        'progress': sprint.get('progress', {}),
                        'user_stories': [
                            {'progress': us.get('progress', {})}
                            for us in sprint.get('user_stories', [])
                        ]
                    }
                    for sprint in sprints
                ]
                client.show_sprint_horizontal(minimal_sprints, priority=Priority.MEDIUM)

            elif preferred_layout == 'single':
                project_name = project_data.get('name', 'Project')
                sprints = project_data.get('sprints', [])
                total_sprints = len(sprints)

                # Find the current (latest incomplete) sprint
                current_sprint_index = len(sprints) - 1  # Default to last sprint
                for i, s in enumerate(sprints):
                    if s.get('progress', {}).get('percentage', 0) < 100:
                        current_sprint_index = i
                        # Continue to find the LAST incomplete sprint

                # Sprint number is 1-indexed for display
                current_sprint_number = current_sprint_index + 1 if sprints else 0

                # Calculate user story counts for the CURRENT sprint only
                if sprints and current_sprint_index < len(sprints):
                    current_sprint_data = sprints[current_sprint_index]
                    current_sprint_stories = current_sprint_data.get('user_stories', [])
                    total_user_stories = len(current_sprint_stories)
                    completed_user_stories = len([
                        us for us in current_sprint_stories
                        if us.get('progress', {}).get('percentage', 0) == 100
                    ])
                else:
                    total_user_stories = 0
                    completed_user_stories = 0

                # Create minimal sprints for multi-segment display
                minimal_sprints = [
                    {
                        'name': sprint.get('name', ''),
                        'progress': sprint.get('progress', {})
                    }
                    for sprint in sprints
                ]

                client.show_single_layout(
                    project_name=project_name,
                    percentage=percentage,
                    current_sprint=current_sprint_number,
                    total_sprints=total_sprints,
                    completed_stories=completed_user_stories,
                    total_stories=total_user_stories,
                    sprints=minimal_sprints,
                    priority=Priority.MEDIUM
                )

            elif preferred_layout == 'user_story_layout':
                sprints = project_data.get('sprints', [])
                if sprints:
                    # Use preferred sprint index from project settings
                    sprint_index = project.preferred_sprint_index or 0
                    if sprint_index >= len(sprints):
                        sprint_index = 0
                    selected_sprint = sprints[sprint_index]
                    sprint_data = {
                        'name': selected_sprint.get('name', ''),
                        'progress': selected_sprint.get('progress', {}),
                        'index': sprint_index
                    }
                    user_stories = selected_sprint.get('user_stories', [])
                    minimal_user_stories = [
                        {
                            'title': story.get('title', ''),
                            'progress': story.get('progress', {})
                        }
                        for story in user_stories
                    ]
                    # Use cycling if more than 2 user stories, otherwise static display
                    if len(minimal_user_stories) > 2:
                        client.show_user_story_layout_cycling(
                            sprint_data, minimal_user_stories, cycle_interval=5.0, priority=Priority.MEDIUM
                        )
                    else:
                        client.show_user_story_layout(sprint_data, minimal_user_stories, priority=Priority.MEDIUM)
                else:
                    # No sprints - fall back to progress bar
                    client.show_progress(percentage, priority=Priority.MEDIUM)

            else:
                # Fallback: use simple progress bar
                client.show_progress(percentage, priority=Priority.MEDIUM)

        except Exception as e:
            # Log but don't fail the project update if LED sync fails
            print(f"LED sync failed: {str(e)}")

    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description (optional)

        Returns:
            Created project object
        """
        project = Project(
            name=name,
            description=description
        )
        db.session.add(project)
        db.session.commit()

        # Update LEDs after creation
        self._update_leds_after_change(project)

        return project

    def get_all_projects(self) -> List[Project]:
        """
        Get all projects.

        Returns:
            List of all projects
        """
        return Project.query.all()

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """
        Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project object or None if not found
        """
        return Project.query.get(project_id)

    def get_project_with_full_tree(self, project_id: str) -> Optional[Dict]:
        """
        Get project with complete nested hierarchy.

        Args:
            project_id: Project ID

        Returns:
            Dict with full project tree or None if not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        return project.to_dict(include_sprints=True)

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Project]:
        """
        Update a project.

        Args:
            project_id: Project ID
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated project object or None if not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        db.session.commit()

        # Update LEDs after modification
        self._update_leds_after_change(project)

        return project

    def update_preferred_layout(self, project_id: str, layout: str) -> Optional[Project]:
        """
        Update a project's preferred LED layout.

        Args:
            project_id: Project ID
            layout: Layout type ('single', 'sprint_view', 'user_story_layout')

        Returns:
            Updated project object or None if not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        project.preferred_layout = layout
        db.session.commit()

        # Update LEDs immediately with new layout
        self._update_leds_after_change(project)

        return project

    def update_preferred_sprint_index(self, project_id: str, sprint_index: int) -> Optional[Project]:
        """
        Update a project's preferred sprint index for user_story_layout.

        Args:
            project_id: Project ID
            sprint_index: Sprint index (0-based)

        Returns:
            Updated project object or None if not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        project.preferred_sprint_index = sprint_index
        db.session.commit()

        # Note: LED sync is handled by frontend when sprintIndex changes
        # to avoid duplicate syncs and race conditions

        return project

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project (cascade deletes sprints, user stories, tasks).

        Args:
            project_id: Project ID

        Returns:
            True if deleted, False if not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return False

        db.session.delete(project)
        db.session.commit()

        # Clear LED display after project deletion
        try:
            client = LEDManagerClient()
            client.clear(priority=Priority.MEDIUM)
        except Exception as e:
            # Log but don't fail the delete operation if LED clear fails
            print(f"LED clear failed: {str(e)}")

        return True

    def get_project_progress(self, project_id: str) -> Optional[Dict]:
        """
        Calculate progress for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with progress stats or None if not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        return ProgressCalculator.calculate_project_progress(project)

    def get_project_stats(self, project_id: str) -> Optional[Dict]:
        """
        Get comprehensive statistics for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with full stats or None if not found
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        return ProgressCalculator.calculate_full_project_stats(project)
