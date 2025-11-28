"""UserStory routes."""
from flask import Blueprint, request, jsonify
from app.services import UserStoryService
from app.models import UserStory

bp = Blueprint('user_stories', __name__, url_prefix='/api')
user_story_service = UserStoryService()


@bp.route('/sprints/<sprint_id>/user-stories', methods=['GET'])
def get_user_stories_by_sprint(sprint_id: str):
    """Get all user stories for a sprint."""
    user_stories = user_story_service.get_user_stories_by_sprint(sprint_id)
    return jsonify([us.to_dict(include_tasks=True) for us in user_stories]), 200


@bp.route('/user-stories/<user_story_id>', methods=['GET'])
def get_user_story(user_story_id: str):
    """Get single user story by ID with nested tasks."""
    user_story = user_story_service.get_user_story_with_tasks(user_story_id)

    if not user_story:
        return jsonify({'error': 'User story not found'}), 404

    return jsonify(user_story), 200


@bp.route('/sprints/<sprint_id>/user-stories', methods=['POST'])
def create_user_story(sprint_id: str):
    """Create a new user story."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate required fields
    if 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400

    # Validate title length
    if len(data['title']) > 200:
        return jsonify({'error': 'Title must be 200 characters or less'}), 400

    # Validate priority if provided
    priority = data.get('priority', 'P2')
    if not UserStory.validate_priority(priority):
        return jsonify({'error': 'Invalid priority. Must be: P0, P1, or P2'}), 400

    # Validate status if provided
    status = data.get('status', 'new')
    if not UserStory.validate_status(status):
        return jsonify({'error': 'Invalid status. Must be: new, in_progress, or completed'}), 400

    try:
        user_story = user_story_service.create_user_story(
            title=data['title'],
            sprint_id=sprint_id,
            description=data.get('description'),
            priority=priority,
            status=status
        )
        return jsonify(user_story.to_dict()), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create user story: {str(e)}'}), 500


@bp.route('/user-stories/<user_story_id>', methods=['PUT'])
def update_user_story(user_story_id: str):
    """Update an existing user story."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate title length if provided
    if 'title' in data and len(data['title']) > 200:
        return jsonify({'error': 'Title must be 200 characters or less'}), 400

    # Validate priority if provided
    if 'priority' in data and not UserStory.validate_priority(data['priority']):
        return jsonify({'error': 'Invalid priority. Must be: P0, P1, or P2'}), 400

    # Validate status if provided
    if 'status' in data and not UserStory.validate_status(data['status']):
        return jsonify({'error': 'Invalid status. Must be: new, in_progress, or completed'}), 400

    try:
        user_story = user_story_service.update_user_story(
            user_story_id=user_story_id,
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority'),
            status=data.get('status')
        )

        if not user_story:
            return jsonify({'error': 'User story not found'}), 404

        return jsonify(user_story.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update user story: {str(e)}'}), 500


@bp.route('/user-stories/<user_story_id>', methods=['DELETE'])
def delete_user_story(user_story_id: str):
    """Delete a user story (cascade deletes all tasks)."""
    try:
        success = user_story_service.delete_user_story(user_story_id)

        if not success:
            return jsonify({'error': 'User story not found'}), 404

        return jsonify({
            'success': True,
            'message': 'User story and all tasks deleted'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete user story: {str(e)}'}), 500


@bp.route('/user-stories/<user_story_id>/progress', methods=['GET'])
def get_user_story_progress(user_story_id: str):
    """Get progress statistics for a user story."""
    progress = user_story_service.get_user_story_progress(user_story_id)

    if progress is None:
        return jsonify({'error': 'User story not found'}), 404

    return jsonify(progress), 200
