"""Progress routes."""
from flask import Blueprint, jsonify
from app.services import TaskService

bp = Blueprint('progress', __name__, url_prefix='/api/progress')
task_service = TaskService()


@bp.route('', methods=['GET'])
def get_progress():
    """
    Get progress statistics.

    Returns:
        JSON with percentage, total_tasks, and completed_tasks
    """
    try:
        stats = task_service.get_progress_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500
