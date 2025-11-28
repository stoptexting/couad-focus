"""LED Manager configuration."""

import os
from pathlib import Path


class LEDManagerConfig:
    """Configuration for LED Manager daemon."""

    # Socket path for IPC
    SOCKET_PATH = os.getenv("LED_SOCKET_PATH", "/tmp/led-manager.sock")

    # Mock mode (for testing without hardware)
    MOCK_MODE = os.getenv("LED_MOCK_MODE", "false").lower() == "true"

    # RGB LED Matrix hardware settings (64x64 HUB75E panel)
    # Based on LED-MATRIX01 datasheet specifications
    MATRIX_ROWS = 64
    MATRIX_COLS = 64
    MATRIX_CHAIN_LENGTH = 1
    MATRIX_PARALLEL = 1
    MATRIX_BRIGHTNESS = 100  # 0-100
    MATRIX_PWM_BITS = 11
    MATRIX_GPIO_SLOWDOWN = 4  # Adjust for stability (1-4)

    # HUB75E Pin mapping (handled automatically by rpi-rgb-led-matrix library)
    # Physical connections as per datasheet:
    # Left side: R1, B1, R2, B2, A, C, CLK, OE
    # Right side: G1, GND, G2, E, B, D, LAT, GND
    # Driving mode: 1/32 Scan
    # Supply voltage: 5V
    # Maximum power: 40W

    # Command queue settings
    COMMAND_QUEUE_SIZE = 100
    WORKER_TIMEOUT = 0.5  # seconds

    # Client settings
    CLIENT_TIMEOUT = 2.0  # seconds
    CLIENT_MAX_RETRIES = 3

    @classmethod
    def from_env(cls) -> 'LEDManagerConfig':
        """
        Load configuration from environment variables.

        Returns:
            Configuration instance
        """
        config = cls()
        return config


# Global config instance
config = LEDManagerConfig.from_env()
