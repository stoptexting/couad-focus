"""Sprint service for business logic."""
from typing import List, Optional, Dict
from datetime import date
import sys
from pathlib import Path
from app.extensions import db
from app.models import Sprint
from app.services.progress_calculator import ProgressCalculator

# Import LED manager components
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared'))
from led_manager.led_manager_client import LEDManagerClient
from led_manager.led_protocol import Priority


class SprintService:
    """Service for sprint CRUD operations."""

    def _update_leds_after_change(self, sprint: Sprint) -> None:
        """
        Update LEDs after sprint modification using project's preferred layout.

        Args:
            sprint: The sprint that was modified
        """
        try:
            # Navigate from sprint to project: sprint → project
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
            # Log but don't fail the sprint update if LED sync fails
            print(f"LED sync failed: {str(e)}")

    def create_sprint(
        self,
        name: str,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: str = 'planned'
    ) -> Sprint:
        """
        Create a new sprint.

        Args:
            name: Sprint name
            project_id: Parent project ID
            start_date: Sprint start date (optional)
            end_date: Sprint end date (optional)
            status: Sprint status (default: 'planned')

        Returns:
            Created sprint object
        """
        sprint = Sprint(
            name=name,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        db.session.add(sprint)
        db.session.commit()

        # Update LEDs after creation
        self._update_leds_after_change(sprint)

        return sprint

    def get_sprints_by_project(self, project_id: str) -> List[Sprint]:
        """
        Get all sprints for a project.

        Args:
            project_id: Project ID

        Returns:
            List of sprints
        """
        return Sprint.query.filter_by(project_id=project_id).all()

    def get_sprint_by_id(self, sprint_id: str) -> Optional[Sprint]:
        """
        Get sprint by ID.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint object or None if not found
        """
        return Sprint.query.get(sprint_id)

    def get_sprint_with_user_stories(self, sprint_id: str) -> Optional[Dict]:
        """
        Get sprint with nested user stories.

        Args:
            sprint_id: Sprint ID

        Returns:
            Dict with sprint data including user stories or None if not found
        """
        sprint = self.get_sprint_by_id(sprint_id)
        if not sprint:
            return None

        return sprint.to_dict(include_user_stories=True)

    def update_sprint(
        self,
        sprint_id: str,
        name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> Optional[Sprint]:
        """
        Update a sprint.

        Args:
            sprint_id: Sprint ID
            name: New name (optional)
            start_date: New start date (optional)
            end_date: New end date (optional)
            status: New status (optional)

        Returns:
            Updated sprint object or None if not found
        """
        sprint = self.get_sprint_by_id(sprint_id)
        if not sprint:
            return None

        if name is not None:
            sprint.name = name
        if start_date is not None:
            sprint.start_date = start_date
        if end_date is not None:
            sprint.end_date = end_date
        if status is not None:
            sprint.status = status

        db.session.commit()

        # Update LEDs after modification (including status changes)
        self._update_leds_after_change(sprint)

        return sprint

    def delete_sprint(self, sprint_id: str) -> bool:
        """
        Delete a sprint (cascade deletes user stories and tasks).

        Args:
            sprint_id: Sprint ID

        Returns:
            True if deleted, False if not found
        """
        sprint = self.get_sprint_by_id(sprint_id)
        if not sprint:
            return False

        # Update LEDs before deletion (need sprint for project lookup)
        self._update_leds_after_change(sprint)

        db.session.delete(sprint)
        db.session.commit()
        return True

    def get_sprint_progress(self, sprint_id: str) -> Optional[Dict]:
        """
        Calculate progress for a sprint.

        Args:
            sprint_id: Sprint ID

        Returns:
            Dict with progress stats or None if not found
        """
        sprint = self.get_sprint_by_id(sprint_id)
        if not sprint:
            return None

        return ProgressCalculator.calculate_sprint_progress(sprint)
