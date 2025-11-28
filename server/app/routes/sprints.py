"""Sprint routes."""
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services import SprintService
from app.models import Sprint

bp = Blueprint('sprints', __name__, url_prefix='/api')
sprint_service = SprintService()


@bp.route('/projects/<project_id>/sprints', methods=['GET'])
def get_sprints_by_project(project_id: str):
    """Get all sprints for a project."""
    sprints = sprint_service.get_sprints_by_project(project_id)
    return jsonify([sprint.to_dict() for sprint in sprints]), 200


@bp.route('/sprints/<sprint_id>', methods=['GET'])
def get_sprint(sprint_id: str):
    """Get single sprint by ID with nested user stories."""
    sprint = sprint_service.get_sprint_with_user_stories(sprint_id)

    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404

    return jsonify(sprint), 200


@bp.route('/projects/<project_id>/sprints', methods=['POST'])
def create_sprint(project_id: str):
    """Create a new sprint."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate required fields
    if 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400

    # Validate name length
    if len(data['name']) > 100:
        return jsonify({'error': 'Name must be 100 characters or less'}), 400

    # Validate status if provided
    status = data.get('status', 'planned')
    if not Sprint.validate_status(status):
        return jsonify({'error': 'Invalid status. Must be: planned, active, or completed'}), 400

    # Parse dates if provided
    start_date = None
    end_date = None

    try:
        if 'start_date' in data and data['start_date']:
            start_date = datetime.fromisoformat(data['start_date']).date()
        if 'end_date' in data and data['end_date']:
            end_date = datetime.fromisoformat(data['end_date']).date()

        # Validate date range
        if start_date and end_date and end_date < start_date:
            return jsonify({'error': 'End date must be after start date'}), 400

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400

    try:
        sprint = sprint_service.create_sprint(
            name=data['name'],
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        return jsonify(sprint.to_dict()), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create sprint: {str(e)}'}), 500


@bp.route('/sprints/<sprint_id>', methods=['PUT'])
def update_sprint(sprint_id: str):
    """Update an existing sprint."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate name length if provided
    if 'name' in data and len(data['name']) > 100:
        return jsonify({'error': 'Name must be 100 characters or less'}), 400

    # Validate status if provided
    if 'status' in data and not Sprint.validate_status(data['status']):
        return jsonify({'error': 'Invalid status. Must be: planned, active, or completed'}), 400

    # Parse dates if provided
    start_date = None
    end_date = None

    try:
        if 'start_date' in data:
            if data['start_date']:
                start_date = datetime.fromisoformat(data['start_date']).date()

        if 'end_date' in data:
            if data['end_date']:
                end_date = datetime.fromisoformat(data['end_date']).date()

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400

    try:
        sprint = sprint_service.update_sprint(
            sprint_id=sprint_id,
            name=data.get('name'),
            start_date=start_date,
            end_date=end_date,
            status=data.get('status')
        )

        if not sprint:
            return jsonify({'error': 'Sprint not found'}), 404

        return jsonify(sprint.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update sprint: {str(e)}'}), 500


@bp.route('/sprints/<sprint_id>', methods=['DELETE'])
def delete_sprint(sprint_id: str):
    """Delete a sprint (cascade deletes all user stories and tasks)."""
    try:
        success = sprint_service.delete_sprint(sprint_id)

        if not success:
            return jsonify({'error': 'Sprint not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Sprint and all nested data deleted'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete sprint: {str(e)}'}), 500


@bp.route('/sprints/<sprint_id>/progress', methods=['GET'])
def get_sprint_progress(sprint_id: str):
    """Get progress statistics for a sprint."""
    progress = sprint_service.get_sprint_progress(sprint_id)

    if progress is None:
        return jsonify({'error': 'Sprint not found'}), 404

    return jsonify(progress), 200
