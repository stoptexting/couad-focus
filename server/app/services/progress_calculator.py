"""Progress calculator utility for hierarchical progress tracking."""
from typing import Dict
from app.models import Project, Sprint, UserStory, Task


class ProgressCalculator:
    """
    Calculate progress across the hierarchy: Project → Sprint → UserStory → Task.

    Progress calculation rules:
    - Task: 0% (new) or 100% (completed)
    - UserStory: (completed_tasks / total_tasks) × 100
    - Sprint: average of user story percentages
    - Project: average of sprint percentages
    """

    @staticmethod
    def calculate_task_progress(task: Task) -> Dict:
        """
        Calculate progress for a single task.

        Args:
            task: Task instance

        Returns:
            Dict with percentage, status
        """
        percentage = 100 if task.status == 'completed' else 0
        return {
            'percentage': percentage,
            'status': task.status,
            'total': 1,
            'completed': 1 if task.status == 'completed' else 0
        }

    @staticmethod
    def calculate_user_story_progress(user_story: UserStory) -> Dict:
        """
        Calculate progress for a user story based on its tasks.

        Args:
            user_story: UserStory instance

        Returns:
            Dict with percentage, total_tasks, completed_tasks
        """
        tasks = list(user_story.tasks)
        total_tasks = len(tasks)

        if total_tasks == 0:
            return {
                'percentage': 0,
                'total_tasks': 0,
                'completed_tasks': 0
            }

        completed_tasks = sum(1 for task in tasks if task.status == 'completed')
        percentage = round((completed_tasks / total_tasks) * 100, 2)

        return {
            'percentage': percentage,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        }

    @staticmethod
    def calculate_sprint_progress(sprint: Sprint) -> Dict:
        """
        Calculate progress for a sprint based on the average completion of its user stories.

        Sprint percentage is the average of all user story percentages (based on their tasks).
        Sprints marked as 'completed' status always show 100%.

        Args:
            sprint: Sprint instance

        Returns:
            Dict with percentage, total_user_stories, completed_user_stories
        """
        # If sprint is marked completed, return 100%
        if sprint.status == 'completed':
            user_stories = list(sprint.user_stories)
            return {
                'percentage': 100,
                'total_user_stories': len(user_stories),
                'completed_user_stories': len(user_stories)
            }

        user_stories = list(sprint.user_stories)
        total_user_stories = len(user_stories)

        if total_user_stories == 0:
            return {
                'percentage': 0,
                'total_user_stories': 0,
                'completed_user_stories': 0
            }

        # Calculate sprint percentage as the average of user story percentages
        total_percentage = 0
        completed_user_stories = 0
        for us in user_stories:
            us_progress = ProgressCalculator.calculate_user_story_progress(us)
            total_percentage += us_progress['percentage']
            if us.status == 'completed':
                completed_user_stories += 1

        percentage = round(total_percentage / total_user_stories, 2)

        return {
            'percentage': percentage,
            'total_user_stories': total_user_stories,
            'completed_user_stories': completed_user_stories
        }

    @staticmethod
    def calculate_project_progress(project: Project) -> Dict:
        """
        Calculate progress for a project based on its sprints.

        Project percentage is the average of all sprint percentages.

        Args:
            project: Project instance

        Returns:
            Dict with percentage, total_sprints, completed_sprints
        """
        # Filter out Backlog sprint (it's hidden from UI but stored in DB)
        sprints = [s for s in project.sprints if s.name != 'Backlog']
        total_sprints = len(sprints)

        if total_sprints == 0:
            return {
                'percentage': 0,
                'total_sprints': 0,
                'completed_sprints': 0
            }

        # Calculate project percentage as the average of sprint percentages
        total_percentage = 0
        completed_sprints = 0
        for sprint in sprints:
            sprint_progress = ProgressCalculator.calculate_sprint_progress(sprint)
            total_percentage += sprint_progress['percentage']
            if sprint_progress['percentage'] == 100:
                completed_sprints += 1

        percentage = round(total_percentage / total_sprints, 2)

        return {
            'percentage': percentage,
            'total_sprints': total_sprints,
            'completed_sprints': completed_sprints
        }

    @staticmethod
    def calculate_full_project_stats(project: Project) -> Dict:
        """
        Calculate comprehensive statistics for a project including all levels.

        Args:
            project: Project instance

        Returns:
            Dict with nested progress at all levels
        """
        project_progress = ProgressCalculator.calculate_project_progress(project)

        sprints_detail = []
        for sprint in project.sprints:
            sprint_progress = ProgressCalculator.calculate_sprint_progress(sprint)
            sprints_detail.append({
                'id': sprint.id,
                'name': sprint.name,
                'status': sprint.status,
                'progress': sprint_progress
            })

        return {
            'project': {
                'id': project.id,
                'name': project.name,
                'progress': project_progress
            },
            'sprints': sprints_detail
        }
