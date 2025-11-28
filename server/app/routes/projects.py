"""Project routes."""
from flask import Blueprint, request, jsonify
from app.services import ProjectService

bp = Blueprint('projects', __name__, url_prefix='/api/projects')
project_service = ProjectService()


@bp.route('', methods=['GET'])
def get_projects():
    """Get all projects."""
    projects = project_service.get_all_projects()
    return jsonify([project.to_dict(include_sprints=True) for project in projects]), 200


@bp.route('/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """Get single project by ID with full tree (sprints, user stories, tasks)."""
    project = project_service.get_project_with_full_tree(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify(project), 200


@bp.route('', methods=['POST'])
def create_project():
    """Create a new project."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate required fields
    if 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400

    # Validate name length
    if len(data['name']) > 100:
        return jsonify({'error': 'Name must be 100 characters or less'}), 400

    try:
        project = project_service.create_project(
            name=data['name'],
            description=data.get('description')
        )
        return jsonify(project.to_dict()), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create project: {str(e)}'}), 500


@bp.route('/<project_id>', methods=['PUT'])
def update_project(project_id: str):
    """Update an existing project."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate name length if provided
    if 'name' in data and len(data['name']) > 100:
        return jsonify({'error': 'Name must be 100 characters or less'}), 400

    try:
        project = project_service.update_project(
            project_id=project_id,
            name=data.get('name'),
            description=data.get('description')
        )

        if not project:
            return jsonify({'error': 'Project not found'}), 404

        return jsonify(project.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update project: {str(e)}'}), 500


@bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """Delete a project (cascade deletes all sprints, user stories, tasks)."""
    try:
        success = project_service.delete_project(project_id)

        if not success:
            return jsonify({'error': 'Project not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Project and all nested data deleted'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete project: {str(e)}'}), 500


@bp.route('/<project_id>/progress', methods=['GET'])
def get_project_progress(project_id: str):
    """Get progress statistics for a project."""
    progress = project_service.get_project_progress(project_id)

    if progress is None:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify(progress), 200


@bp.route('/<project_id>/preferred-layout', methods=['PUT'])
def update_preferred_layout(project_id: str):
    """Update a project's preferred LED layout."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'preferred_layout' not in data:
        return jsonify({'error': 'preferred_layout is required'}), 400

    layout = data['preferred_layout']

    # Validate layout type
    valid_layouts = ['single', 'sprint_view', 'user_story_layout']
    if layout not in valid_layouts:
        return jsonify({'error': f'Invalid layout type. Must be one of: {", ".join(valid_layouts)}'}), 400

    try:
        project = project_service.update_preferred_layout(project_id, layout)

        if not project:
            return jsonify({'error': 'Project not found'}), 404

        return jsonify(project.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update preferred layout: {str(e)}'}), 500


@bp.route('/<project_id>/preferred-sprint-index', methods=['PUT'])
def update_preferred_sprint_index(project_id: str):
    """Update a project's preferred sprint index for user_story_layout."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'preferred_sprint_index' not in data:
        return jsonify({'error': 'preferred_sprint_index is required'}), 400

    sprint_index = data['preferred_sprint_index']

    # Validate sprint index is a non-negative integer
    if not isinstance(sprint_index, int) or sprint_index < 0:
        return jsonify({'error': 'preferred_sprint_index must be a non-negative integer'}), 400

    try:
        project = project_service.update_preferred_sprint_index(project_id, sprint_index)

        if not project:
            return jsonify({'error': 'Project not found'}), 404

        return jsonify(project.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update preferred sprint index: {str(e)}'}), 500
