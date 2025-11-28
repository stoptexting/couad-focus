"""
Admin routes for database management and system operations
"""
from flask import Blueprint, jsonify

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/reset-database', methods=['POST'])
def reset_database():
    """
    Reset the database by clearing all project data.

    Deletes all projects, sprints, user stories, and tasks.
    Keeps Taiga auth token so user stays logged in.

    Returns:
        JSON response with counts of deleted items
    """
    from app.extensions import db
    from app.models.project import Project
    from app.models.sprint import Sprint
    from app.models.user_story import UserStory
    from app.models.task import Task
    from app.models.taiga_config import TaigaConfig

    try:
        # Count before deletion
        project_count = Project.query.count()
        sprint_count = Sprint.query.count()
        story_count = UserStory.query.count()
        task_count = Task.query.count()

        # Delete all projects (cascades to sprints, user_stories, tasks)
        Project.query.delete()

        # Reset TaigaConfig project fields but keep auth (user stays logged in)
        config = TaigaConfig.query.first()
        if config:
            config.project_url = None
            config.project_slug = None
            config.taiga_project_id = None
            config.local_project_id = None
            config.sync_status = 'authenticated' if config.auth_token else 'not_configured'
            config.last_sync_at = None
            config.last_error = None
            config.data_version += 1  # Trigger frontend cache invalidation

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Database cleared successfully',
            'data': {
                'projects': project_count,
                'sprints': sprint_count,
                'user_stories': story_count,
                'tasks': task_count
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to reset database: {str(e)}'
        }), 500
