"""Logging utility for Raspberry Pi Boot Manager."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class Logger:
    """Centralized logging system with file and console output."""

    def __init__(
        self,
        name: str,
        log_dir: Path,
        level: int = logging.INFO,
        console_output: bool = True
    ):
        """
        Initialize logger.

        Args:
            name: Logger name (usually module name)
            log_dir: Directory for log files
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Whether to output to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_formatter = logging.Formatter(
            fmt="[%(levelname)s] %(message)s"
        )

        # File handler - main log
        log_dir.mkdir(parents=True, exist_ok=True)
        main_log_file = log_dir / "bootmanager.log"
        file_handler = logging.FileHandler(main_log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)

        # File handler - error log
        error_log_file = log_dir / "bootmanager.error.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """
        Log error message.

        Args:
            message: Error message
            exc_info: Whether to include exception traceback
        """
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        """
        Log critical message.

        Args:
            message: Critical message
            exc_info: Whether to include exception traceback
        """
        self.logger.critical(message, exc_info=exc_info)

    def exception(self, message: str) -> None:
        """Log exception with full traceback."""
        self.logger.exception(message)


# Global logger instance
_logger: Optional[Logger] = None


def setup_logger(
    name: str = "bootmanager",
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> Logger:
    """
    Set up and return global logger instance.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level
        console_output: Whether to output to console

    Returns:
        Initialized Logger instance
    """
    global _logger

    if log_dir is None:
        log_dir = Path("logs")

    _logger = Logger(name, log_dir, level, console_output)
    return _logger


def get_logger() -> Logger:
    """
    Get the global logger instance.

    Returns:
        Logger instance

    Raises:
        RuntimeError: If logger hasn't been set up yet
    """
    if _logger is None:
        raise RuntimeError("Logger not set up. Call setup_logger() first.")
    return _logger
