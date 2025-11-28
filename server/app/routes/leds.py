"""LED control routes."""
from flask import Blueprint, request, jsonify, current_app
from app.services import LEDService
from app.services.multi_led_controller import MultiLEDController
from app.utils import validate_percentage

bp = Blueprint('leds', __name__, url_prefix='/api/leds')


@bp.route('/update', methods=['POST'])
def manual_update():
    """
    Manually trigger LED update for testing.

    Body:
        {
            "percentage": int (0-100)
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'percentage' not in data:
        return jsonify({'error': 'Percentage is required'}), 400

    percentage = data['percentage']

    # Validate percentage
    errors = validate_percentage(percentage)
    if errors:
        return jsonify({'error': ', '.join(errors)}), 400

    try:
        # Get LED service and trigger update
        enabled = current_app.config.get('LED_ENABLED', True)
        led_service = LEDService(enabled=enabled)
        led_service.update_progress(percentage)

        return jsonify({
            'success': True,
            'leds_updated': True,
            'percentage': percentage
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update LEDs: {str(e)}'}), 500


@bp.route('/multi-update', methods=['POST'])
def multi_zone_update():
    """
    Update multiple LED zones with different percentages.

    Body:
        [
            {"zone_id": "zone-1", "percentage": 75, "color": [0,255,0]},
            {"zone_id": "zone-2", "percentage": 30, "color": [255,255,0]}
        ]
    """
    data = request.get_json()

    if not data or not isinstance(data, list):
        return jsonify({'error': 'Request body must be an array of zone updates'}), 400

    if len(data) == 0:
        return jsonify({'error': 'At least one zone update is required'}), 400

    # Validate each zone update
    for i, zone_update in enumerate(data):
        if 'zone_id' not in zone_update:
            return jsonify({'error': f'zone_id is required for update {i}'}), 400

        if 'percentage' not in zone_update:
            return jsonify({'error': f'percentage is required for update {i}'}), 400

        # Validate percentage
        errors = validate_percentage(zone_update['percentage'])
        if errors:
            return jsonify({'error': f'Update {i}: {", ".join(errors)}'}), 400

        # Validate color if provided
        if 'color' in zone_update:
            color = zone_update['color']
            if not isinstance(color, list) or len(color) != 3:
                return jsonify({'error': f'Update {i}: color must be [r, g, b] array'}), 400

    try:
        # Get multi-LED controller
        controller = MultiLEDController()

        # Prepare update data
        prepared_data = controller.prepare_multi_zone_update(data)

        # TODO: Send to LED daemon when multi-zone protocol is implemented
        # For now, just return success with the prepared data

        return jsonify({
            'success': True,
            'zones_updated': len(prepared_data['zones']),
            'zones': prepared_data['zones']
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update LED zones: {str(e)}'}), 500


@bp.route('/zones', methods=['GET'])
def get_zones():
    """Get all configured LED zones."""
    try:
        controller = MultiLEDController()
        zones = controller.get_zones()

        return jsonify({
            'zones': zones,
            'total_zones': len(zones),
            'is_single_zone': controller.is_single_zone()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get LED zones: {str(e)}'}), 500


@bp.route('/config', methods=['GET'])
def get_config():
    """Get current LED configuration."""
    try:
        controller = MultiLEDController()

        return jsonify({
            'zones': controller.get_zones(),
            'total_leds': controller.total_leds,
            'is_single_zone': controller.is_single_zone(),
            'primary_zone': controller.get_primary_zone()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get LED config: {str(e)}'}), 500
