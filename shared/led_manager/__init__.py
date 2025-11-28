"""Shared LED Manager - Socket-based LED controller for concurrent access."""

from .led_manager_client import LEDManagerClient

__all__ = ['LEDManagerClient']
