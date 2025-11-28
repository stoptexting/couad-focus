"""LED Client wrapper for bootmanager - connects to LED manager daemon."""

import sys
from pathlib import Path

# Add shared directory to path for led_manager package
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from led_manager.led_manager_client import LEDManagerClient


def init_led_client(socket_path: str = "/tmp/led-manager.sock") -> LEDManagerClient:
    """
    Initialize and return LED manager client.

    Args:
        socket_path: Path to LED manager socket

    Returns:
        Initialized LEDManagerClient instance
    """
    return LEDManagerClient(socket_path=socket_path)


def get_led_client() -> LEDManagerClient:
    """
    Get LED manager client (for compatibility with old code).

    Returns:
        LEDManagerClient instance

    Note:
        This is a compatibility function. New code should instantiate
        LEDManagerClient directly or use init_led_client().
    """
    return init_led_client()
