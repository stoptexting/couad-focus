"""Configuration classes for Flask application."""
import os
import json
import logging

logger = logging.getLogger(__name__)

# Get the base directory (server/)
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def load_led_config():
    """Load LED configuration from config.json."""
    config_path = os.path.join(basedir, 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"config.json not found at {config_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config.json: {e}")
        return None


class Config:
    """Base configuration."""
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "instance", "database.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LED_SOCKET_PATH = '/tmp/led-manager.sock'
    LED_ENABLED = True  # Physical LED setup available
    LED_ZONES_CONFIG = load_led_config()  # LED multi-zone configuration


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LED_ENABLED = False  # Disable LED hardware for testing (set to True when daemon is running)


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LED_ENABLED = True  # Use real LED hardware in prod
