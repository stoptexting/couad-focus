"""Multi-LED zone controller for managing multiple LED zones."""
import logging
import json
import os
from typing import List, Dict, Optional
from flask import current_app
from led_manager.led_manager_client import LEDManagerClient
from led_manager.led_protocol import Priority

logger = logging.getLogger(__name__)


class MultiLEDController:
    """
    Controller for managing multiple LED zones.

    Supports multiple configurations:
    - Single zone: Display one gauge across all LEDs
    - Multi-zone: Display multiple gauges in different LED zones
    """

    def __init__(self, enabled: bool = True):
        """Initialize multi-LED controller."""
        self.config = None
        self.zones = []
        self.total_leds = 0
        self.enabled = enabled
        self.client = LEDManagerClient() if enabled else None
        self._load_config()

    def _load_config(self) -> None:
        """Load LED zone configuration from config.json."""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config.json'
            )

            if not os.path.exists(config_path):
                logger.warning(f"config.json not found at {config_path}, using single zone default")
                self._use_default_config()
                return

            with open(config_path, 'r') as f:
                self.config = json.load(f)

            hardware = self.config.get('hardware', {})
            self.zones = hardware.get('led_zones', [])
            self.total_leds = hardware.get('total_leds', 64)

            logger.info(f"Loaded LED configuration: {len(self.zones)} zones, {self.total_leds} total LEDs")

        except Exception as e:
            logger.error(f"Failed to load config.json: {e}")
            self._use_default_config()

    def _use_default_config(self) -> None:
        """Use default single-zone configuration."""
        self.zones = [{
            "id": "zone-1",
            "name": "Default Zone",
            "start_led": 0,
            "end_led": 63,
            "default_color": [0, 255, 0]
        }]
        self.total_leds = 64
        logger.info("Using default single-zone LED configuration")

    def get_zones(self) -> List[Dict]:
        """
        Get all configured LED zones.

        Returns:
            List of zone configurations
        """
        return self.zones

    def get_zone_by_id(self, zone_id: str) -> Optional[Dict]:
        """
        Get zone configuration by ID.

        Args:
            zone_id: Zone identifier

        Returns:
            Zone configuration dict or None if not found
        """
        for zone in self.zones:
            if zone['id'] == zone_id:
                return zone
        return None

    def calculate_zone_leds(self, zone: Dict, percentage: int) -> Dict:
        """
        Calculate LED indices to light for a zone based on percentage.

        Args:
            zone: Zone configuration dict
            percentage: Progress percentage (0-100)

        Returns:
            Dict with start_led, end_led, leds_to_light, color
        """
        start_led = zone['start_led']
        end_led = zone['end_led']
        total_zone_leds = end_led - start_led + 1

        # Calculate how many LEDs to light
        leds_to_light = round((percentage / 100) * total_zone_leds)
        leds_to_light = max(0, min(leds_to_light, total_zone_leds))

        # Calculate actual LED range to light
        light_end_led = start_led + leds_to_light - 1 if leds_to_light > 0 else start_led - 1

        return {
            'start_led': start_led,
            'end_led': light_end_led,
            'leds_to_light': leds_to_light,
            'total_zone_leds': total_zone_leds,
            'color': zone.get('default_color', [0, 255, 0])
        }

    def prepare_multi_zone_update(self, zone_updates: List[Dict]) -> Dict:
        """
        Prepare multi-zone update command.

        Args:
            zone_updates: List of {zone_id, percentage, color (optional)}

        Returns:
            Dict formatted for LED daemon multi-zone command
        """
        zones_data = []

        for update in zone_updates:
            zone_id = update.get('zone_id')
            percentage = update.get('percentage', 0)
            color = update.get('color')

            zone = self.get_zone_by_id(zone_id)
            if not zone:
                logger.warning(f"Zone {zone_id} not found, skipping")
                continue

            # Calculate LEDs for this zone
            zone_calc = self.calculate_zone_leds(zone, percentage)

            # Use provided color or default
            if color is None:
                color = zone_calc['color']

            zones_data.append({
                'zone_id': zone_id,
                'start_led': zone_calc['start_led'],
                'end_led': zone_calc['end_led'],
                'leds_to_light': zone_calc['leds_to_light'],
                'percentage': percentage,
                'color': color
            })

        return {
            'zones': zones_data,
            'total_zones': len(zones_data)
        }

    def is_single_zone(self) -> bool:
        """
        Check if configuration has only one zone.

        Returns:
            True if single zone, False otherwise
        """
        return len(self.zones) == 1

    def get_primary_zone(self) -> Optional[Dict]:
        """
        Get the primary zone (first zone or configured default).

        Returns:
            Primary zone configuration or None
        """
        if not self.zones:
            return None

        # Check for configured primary zone
        if self.config:
            defaults = self.config.get('defaults', {})
            primary_id = defaults.get('primary_zone')
            if primary_id:
                zone = self.get_zone_by_id(primary_id)
                if zone:
                    return zone

        # Default to first zone
        return self.zones[0]

    def send_multi_zone_update(self, zone_updates: List[Dict]) -> Dict:
        """
        Send multi-zone update to LED daemon.

        Args:
            zone_updates: List of {zone_id, percentage, color (optional)}

        Returns:
            Dict with status and zones updated
        """
        if not self.enabled:
            logger.info("LED update skipped (disabled)")
            return {'status': 'disabled', 'zones_updated': 0}

        try:
            prepared = self.prepare_multi_zone_update(zone_updates)

            # For now, update each zone sequentially
            # TODO: Add native multi-zone support to LED daemon protocol
            for zone_data in prepared['zones']:
                percentage = zone_data['percentage']
                self.client.show_progress(percentage, priority=Priority.LOW)
                logger.info(f"LED zone {zone_data['zone_id']} updated to {percentage}%")

            return {
                'status': 'success',
                'zones_updated': prepared['total_zones'],
                'zones': prepared['zones']
            }

        except ConnectionError as e:
            logger.warning(f"LED daemon not available: {e}")
            return {
                'status': 'daemon_unavailable',
                'zones_updated': 0,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"LED multi-zone update error: {e}")
            return {
                'status': 'error',
                'zones_updated': 0,
                'error': str(e)
            }
