"""Gauge layout and LED sync routes."""
from flask import Blueprint, jsonify, request
from datetime import datetime
from app.services import ProjectService
from app.services.multi_led_controller import MultiLEDController

# LED matrix imports - DISABLED to prevent conflicts with LED daemon
# The Flask app should not directly control LED hardware
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared'))
# from led_manager.led_hardware import LEDHardwareController
# from led_manager.led_layout_renderer import LEDLayoutRenderer

bp = Blueprint('gauges', __name__, url_prefix='/api/projects')
project_service = ProjectService()
led_controller = MultiLEDController()

# Initialize LED matrix hardware - DISABLED
# This was causing conflicts with the LED daemon and bootmanager
# led_hardware = LEDHardwareController(mock_mode=False)
# led_renderer = LEDLayoutRenderer(led_hardware)
led_hardware = None
led_renderer = None

# User story colors matching LED panel hardware (same as USER_STORY_COLORS in led_layout_renderer.py)
USER_STORY_COLORS = [
    'rgb(0,100,255)',    # Blue
    'rgb(255,255,0)',    # Yellow
    'rgb(0,255,255)',    # Cyan
    'rgb(255,0,255)',    # Magenta
    'rgb(255,128,0)',    # Orange
    'rgb(128,255,0)',    # Lime
    'rgb(255,0,128)',    # Pink
    'rgb(128,0,255)',    # Purple
]

# Sprint colors for single layout (project gauge filled with sprint colors)
SPRINT_COLORS = [
    'rgb(0,255,0)',      # Green
    'rgb(0,200,255)',    # Light Blue
    'rgb(255,165,0)',    # Orange
    'rgb(255,0,100)',    # Pink
    'rgb(128,0,255)',    # Purple
    'rgb(255,255,0)',    # Yellow
]


def build_gauge_data_single(project_dict: dict) -> list:
    """Build gauge data for single view (project + sprints for frontend preview)."""
    progress = project_dict.get('progress', {})
    sprints = project_dict.get('sprints', [])

    # Build segments for project gauge (sprint colors)
    segments = []
    for i, sprint in enumerate(sprints):
        sprint_progress = sprint.get('progress', {})
        sprint_percentage = sprint_progress.get('percentage', 0)
        if sprint_percentage > 0:
            segments.append({
                'percentage': sprint_percentage,
                'color': SPRINT_COLORS[i % len(SPRINT_COLORS)],
            })

    gauges = [{
        'id': project_dict['id'],
        'label': project_dict['name'],
        'percentage': progress.get('percentage', 0),
        'type': 'project',
        'segments': segments,  # Multi-segment fill with sprint colors
    }]

    # Add sprint gauges so frontend can extract sprint/story counts
    for sprint in sprints:
        sprint_progress = sprint.get('progress', {})
        user_stories = sprint.get('user_stories', [])

        gauges.append({
            'id': sprint['id'],
            'label': sprint['name'],
            'percentage': sprint_progress.get('percentage', 0),
            'type': 'sprint',
            'user_stories': user_stories,
        })

    return gauges


def build_gauge_data_sprint_view(project_dict: dict) -> list:
    """Build gauge data for sprint view (one gauge per sprint with user story color segments)."""
    gauges = []
    sprints = project_dict.get('sprints', [])

    for sprint in sprints:
        progress = sprint.get('progress', {})
        user_stories = sprint.get('user_stories', [])

        # Build segments for each user story (matching LED panel multi-segment bar)
        segments = []
        for i, story in enumerate(user_stories):
            story_progress = story.get('progress', {})
            story_percentage = story_progress.get('percentage', 0)
            if story_percentage > 0:  # Only include non-zero segments
                segments.append({
                    'percentage': story_percentage,
                    'color': USER_STORY_COLORS[i % len(USER_STORY_COLORS)],
                })

        gauges.append({
            'id': sprint['id'],
            'label': sprint['name'],
            'percentage': progress.get('percentage', 0),
            'type': 'sprint',
            'segments': segments,  # User story color segments
        })

    return gauges


def build_gauge_data_user_story_layout(project_dict: dict, sprint_index: int = 0) -> list:
    """Build gauge data for user story layout (sprint + all user stories)."""
    gauges = []
    sprints = project_dict.get('sprints', [])

    if not sprints:
        return gauges

    # Get selected sprint (default to first)
    if sprint_index >= len(sprints):
        sprint_index = 0

    sprint = sprints[sprint_index]
    sprint_progress = sprint.get('progress', {})
    user_stories = sprint.get('user_stories', [])

    # Build segments for sprint gauge (user story colors)
    segments = []
    for i, story in enumerate(user_stories):
        story_progress = story.get('progress', {})
        story_percentage = story_progress.get('percentage', 0)
        if story_percentage > 0:
            segments.append({
                'percentage': story_percentage,
                'color': USER_STORY_COLORS[i % len(USER_STORY_COLORS)],
            })

    # Add sprint gauge with multi-segment fill
    gauges.append({
        'id': sprint['id'],
        'label': f"S{sprint_index + 1}: {sprint['name']}",
        'percentage': sprint_progress.get('percentage', 0),
        'type': 'sprint',
        'segments': segments,  # Multi-segment fill with user story colors
    })

    # Add all user stories with colors matching LED panel
    for i, story in enumerate(user_stories):
        story_progress = story.get('progress', {})
        gauges.append({
            'id': story['id'],
            'label': f"U{i+1}: {story['title']}",
            'percentage': story_progress.get('percentage', 0),
            'type': 'user_story',
            'color': USER_STORY_COLORS[i % len(USER_STORY_COLORS)],
        })

    return gauges


@bp.route('/<project_id>/gauges/<layout_type>', methods=['GET'])
def get_gauge_layout_data(project_id: str, layout_type: str):
    """
    Get gauge data for a specific layout type.

    Args:
        project_id: Project UUID
        layout_type: 'single' | 'sprint_view' | 'user_story_layout'

    Returns:
        JSON with gauge data for the specified layout
    """
    # Validate layout type
    valid_layouts = ['single', 'sprint_view', 'user_story_layout']
    if layout_type not in valid_layouts:
        return jsonify({
            'error': f'Invalid layout type. Must be one of: {", ".join(valid_layouts)}'
        }), 400

    # Get project with full tree and progress
    project = project_service.get_project_with_full_tree(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Build gauge data based on layout type
    if layout_type == 'single':
        gauges = build_gauge_data_single(project)
    elif layout_type == 'sprint_view':
        gauges = build_gauge_data_sprint_view(project)
    elif layout_type == 'user_story_layout':
        # Get sprint index from query params
        sprint_index = request.args.get('sprint_index', 0, type=int)
        gauges = build_gauge_data_user_story_layout(project, sprint_index)
    else:
        gauges = []

    return jsonify({
        'layout_type': layout_type,
        'gauges': gauges,
        'project_id': project_id,
        'project_name': project['name'],
        'timestamp': datetime.utcnow().isoformat(),
    }), 200


@bp.route('/<project_id>/sync-leds', methods=['POST'])
def sync_leds_with_progress(project_id: str):
    """
    Synchronize LED zones with project progress.

    Maps sprints to LED zones and updates them based on sprint progress.

    Args:
        project_id: Project UUID

    Returns:
        JSON with sync status
    """
    # Get project with full tree
    project = project_service.get_project_with_full_tree(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Get LED zones
    zones = led_controller.get_zones()
    sprints = project.get('sprints', [])

    # Map sprints to zones (1:1 mapping by index)
    zone_updates = []
    for i, sprint in enumerate(sprints):
        if i < len(zones):
            zone = zones[i]
            progress = sprint.get('progress', {})
            percentage = progress.get('percentage', 0)

            zone_updates.append({
                'zone_id': zone['id'],
                'percentage': percentage,
            })

    # Send updates to LED controller
    result = led_controller.send_multi_zone_update(zone_updates)

    return jsonify({
        'synced': result.get('status') == 'success',
        'zones_updated': result.get('zones_updated', 0),
        'last_sync': datetime.utcnow().isoformat(),
        'errors': [result.get('error')] if 'error' in result else [],
    }), 200


@bp.route('/<project_id>/sync-led-matrix/<layout_type>', methods=['POST'])
def sync_led_matrix(project_id: str, layout_type: str):
    """
    Synchronize LED matrix with project progress via daemon.

    Args:
        project_id: Project UUID
        layout_type: 'single' | 'sprint_view' | 'user_story_layout'

    Returns:
        JSON with sync status
    """
    # Validate layout type
    valid_layouts = ['single', 'sprint_view', 'user_story_layout']
    if layout_type not in valid_layouts:
        return jsonify({
            'error': f'Invalid layout type. Must be one of: {", ".join(valid_layouts)}'
        }), 400

    # Get project with full tree and progress
    project = project_service.get_project_with_full_tree(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        # Import LED manager client
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared'))
        from led_manager.led_manager_client import LEDManagerClient
        from led_manager.led_protocol import Priority

        # Get project progress percentage
        progress = project.get('progress', {})
        percentage = int(progress.get('percentage', 0))

        # Send to LED daemon based on layout type
        client = LEDManagerClient()

        if layout_type == 'sprint_view':
            # Send sprint horizontal layout with sprint data including user stories for multi-segment display
            sprints = project.get('sprints', [])
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
            return jsonify({
                'synced': True,
                'layout_type': layout_type,
                'sprints_count': len(sprints),
                'last_sync': datetime.utcnow().isoformat(),
            }), 200
        elif layout_type == 'user_story_layout':
            # Get sprint selection parameter (default to 0 - first sprint)
            sprint_index = request.json.get('sprint_index', 0) if request.json else 0
            cycle_interval = request.json.get('cycle_interval', 10.0) if request.json else 10.0

            sprints = project.get('sprints', [])

            # Validate sprint index
            if not sprints:
                return jsonify({
                    'synced': False,
                    'error': 'No sprints found in project'
                }), 400

            if sprint_index >= len(sprints):
                sprint_index = 0  # Default to first sprint if index out of range

            # Get selected sprint
            selected_sprint = sprints[sprint_index]
            sprint_data = {
                'name': selected_sprint.get('name', ''),
                'progress': selected_sprint.get('progress', {}),
                'index': sprint_index
            }

            # Get ALL user stories from selected sprint (no limit)
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
                    sprint_data, minimal_user_stories, cycle_interval, priority=Priority.MEDIUM
                )
                cycling_enabled = True
            else:
                client.show_user_story_layout(sprint_data, minimal_user_stories, priority=Priority.MEDIUM)
                cycling_enabled = False

            return jsonify({
                'synced': True,
                'layout_type': layout_type,
                'sprint_index': sprint_index,
                'sprint_name': sprint_data['name'],
                'user_stories_count': len(user_stories),
                'cycling_enabled': cycling_enabled,
                'cycle_interval': cycle_interval if cycling_enabled else None,
                'last_sync': datetime.utcnow().isoformat(),
            }), 200
        elif layout_type == 'single':
            # Send single layout with project name, current sprint number, and current sprint US counts
            project_name = project.get('name', 'Project')
            sprints = project.get('sprints', [])
            total_sprints = len(sprints)

            # Find the current (latest) sprint number
            # Current sprint is the last non-100% sprint, or the last sprint if all complete
            current_sprint_index = len(sprints) - 1  # Default to last sprint
            for i, s in enumerate(sprints):
                if s.get('progress', {}).get('percentage', 0) < 100:
                    current_sprint_index = i
                    # Continue to find the LAST incomplete sprint, not the first

            # Sprint number is 1-indexed for display
            current_sprint_number = current_sprint_index + 1 if sprints else 0

            # Get user story counts for the CURRENT sprint only
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

            # Minimal sprint data for multi-segment display (only name and progress)
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
            return jsonify({
                'synced': True,
                'layout_type': layout_type,
                'project_name': project_name,
                'percentage': percentage,
                'current_sprint_number': current_sprint_number,
                'total_sprints': total_sprints,
                'sprint_us_completed': completed_user_stories,
                'sprint_us_total': total_user_stories,
                'last_sync': datetime.utcnow().isoformat(),
            }), 200
        else:
            # For other layouts, use simple progress bar
            client.show_progress(percentage, priority=Priority.MEDIUM)
            return jsonify({
                'synced': True,
                'layout_type': layout_type,
                'percentage': percentage,
                'last_sync': datetime.utcnow().isoformat(),
            }), 200

    except ConnectionError as e:
        return jsonify({
            'synced': False,
            'error': 'LED daemon not running',
            'details': str(e)
        }), 503

    except Exception as e:
        return jsonify({
            'synced': False,
            'error': str(e),
        }), 500
