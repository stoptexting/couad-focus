"""Task routes."""
from flask import Blueprint, request, jsonify
from app.services import TaskService
from app.utils import validate_task_input

bp = Blueprint('tasks', __name__, url_prefix='/api')
task_service = TaskService()


@bp.route('/user-stories/<user_story_id>/tasks', methods=['GET'])
def get_tasks_by_user_story(user_story_id: str):
    """Get all tasks for a user story."""
    tasks = task_service.get_tasks_by_user_story(user_story_id)
    return jsonify([task.to_dict() for task in tasks]), 200


@bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """Get single task by ID."""
    task = task_service.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(task.to_dict()), 200


@bp.route('/user-stories/<user_story_id>/tasks', methods=['POST'])
def create_task(user_story_id: str):
    """Create a new task."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate required fields
    if 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400

    # Validate input
    errors = validate_task_input(data)
    if errors:
        return jsonify({'error': ', '.join(errors)}), 400

    try:
        task = task_service.create_task(
            title=data['title'],
            user_story_id=user_story_id,
            description=data.get('description')
        )
        return jsonify(task.to_dict()), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create task: {str(e)}'}), 500


@bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id: str):
    """Update an existing task."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate input
    errors = validate_task_input(data)
    if errors:
        return jsonify({'error': ', '.join(errors)}), 400

    try:
        task = task_service.update_task(
            task_id=task_id,
            title=data.get('title'),
            description=data.get('description'),
            status=data.get('status')
        )

        if not task:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(task.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update task: {str(e)}'}), 500


@bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id: str):
    """Delete a task."""
    try:
        success = task_service.delete_task(task_id)

        if not success:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Task deleted'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete task: {str(e)}'}), 500
