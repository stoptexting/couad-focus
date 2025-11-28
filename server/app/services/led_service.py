"""LED service for controlling LED progress display."""
import logging

# Imports from led_manager (shared/ added to path in run.py)
from led_manager.led_manager_client import LEDManagerClient
from led_manager.led_protocol import Priority

logger = logging.getLogger(__name__)


class LEDService:
    """Service for controlling LED display via LED manager daemon."""

    def __init__(self, enabled: bool = True):
        """
        Initialize LED service.

        Args:
            enabled: Whether LED updates are enabled
        """
        self.enabled = enabled
        self.client = LEDManagerClient() if enabled else None

    def update_progress(self, percentage: int) -> None:
        """
        Update LED progress bar (0-100%).

        Args:
            percentage: Progress percentage (0-100)
        """
        if not self.enabled:
            logger.info(f"LED update skipped (disabled): {percentage}%")
            return

        try:
            self.client.show_progress(percentage, priority=Priority.LOW)
            logger.info(f"LED updated to {percentage}%")
        except ConnectionError as e:
            # LED daemon not running - log but don't crash API
            logger.warning(f"LED daemon not available: {e}")
        except Exception as e:
            logger.error(f"LED update error: {e}")
