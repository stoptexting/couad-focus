"""Configuration management for Raspberry Pi Boot Manager."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration loader and validator."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to secrets.env file. If None, uses default location.
        """
        if config_path is None:
            # Default: ~/.config/bootmanager/secrets.env or ./config/secrets.env
            home_config = Path.home() / ".config" / "bootmanager" / "secrets.env"
            local_config = Path("config") / "secrets.env"

            if home_config.exists():
                config_path = str(home_config)
            elif local_config.exists():
                config_path = str(local_config)
            else:
                raise FileNotFoundError(
                    f"Configuration file not found. Please create one at:\n"
                    f"  {home_config}\n  or\n  {local_config}"
                )

        # Load environment variables from file
        load_dotenv(config_path)

        # Load and validate required configuration
        self.discord_bot_token = self._get_required("DISCORD_BOT_TOKEN")
        self.discord_channel_id = int(self._get_required("DISCORD_CHANNEL_ID"))
        self.ngrok_auth_token = self._get_required("NGROK_AUTH_TOKEN")
        self.ngrok_http_username = self._get_required("NGROK_HTTP_USERNAME")
        self.ngrok_http_password = self._get_required("NGROK_HTTP_PASSWORD")
        self.wifi_ssid = self._get_required("WIFI_SSID")
        self.wifi_password = self._get_required("WIFI_PASSWORD")

        # Optional configuration with defaults
        self.log_dir = Path(self._get_optional("LOG_DIR", "logs"))
        self.cmdruns_dir = Path(self._get_optional("CMDRUNS_DIR", ".cmdruns"))
        self.wifi_retry_attempts = int(self._get_optional("WIFI_RETRY_ATTEMPTS", "10"))
        self.wifi_retry_delay = int(self._get_optional("WIFI_RETRY_DELAY", "5"))
        self.ngrok_retry_delay = int(self._get_optional("NGROK_RETRY_DELAY", "30"))

        # Service configuration
        self.server_path = Path(self._get_optional("SERVER_PATH", "/home/focus/focus/server"))
        self.frontend_path = Path(self._get_optional("FRONTEND_PATH", "/home/focus/focus/frontend"))
        self.server_port = int(self._get_optional("SERVER_PORT", "5001"))
        self.frontend_port = int(self._get_optional("FRONTEND_PORT", "3000"))
        self.frontend_dev_mode = self._get_optional("FRONTEND_DEV_MODE", "false").lower() == "true"

        # Ensure directories exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cmdruns_dir.mkdir(parents=True, exist_ok=True)

    def _get_required(self, key: str) -> str:
        """
        Get required environment variable.

        Args:
            key: Environment variable name

        Returns:
            Value of the environment variable

        Raises:
            ValueError: If the environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required configuration '{key}' is not set in secrets.env")
        return value

    def _get_optional(self, key: str, default: str) -> str:
        """
        Get optional environment variable with default.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Value of the environment variable or default
        """
        return os.getenv(key, default)

    def __repr__(self) -> str:
        """String representation (with sensitive data masked)."""
        return (
            f"Config(wifi_ssid='{self.wifi_ssid}', "
            f"discord_channel_id={self.discord_channel_id}, "
            f"log_dir='{self.log_dir}', "
            f"cmdruns_dir='{self.cmdruns_dir}')"
        )


# Global config instance (initialized in main.py)
config: Optional[Config] = None


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load and initialize global configuration.

    Args:
        config_path: Optional path to secrets.env file

    Returns:
        Initialized Config instance
    """
    global config
    config = Config(config_path)
    return config


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance

    Raises:
        RuntimeError: If config hasn't been loaded yet
    """
    if config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return config
