"""
LED matrix animations and symbols for 8x8 MAX7219 display.

DEPRECATED: This module is deprecated and no longer used.
The LED system has been upgraded to use a 64x64 RGB matrix with direct
graphics rendering instead of 8x8 binary patterns.

See led_hardware.py for the new implementation using rgbmatrix graphics library.

This file is kept for reference only and should not be used in new code.
"""

import warnings
from typing import List, Dict

warnings.warn(
    "led_animations.py is deprecated. Use led_hardware.py direct graphics methods instead.",
    DeprecationWarning,
    stacklevel=2
)

# Each symbol is represented as an 8x8 binary pattern
# 1 = LED on, 0 = LED off
# Patterns are defined as lists of 8 integers (rows), each representing 8 bits


class Symbols:
    """Collection of 8x8 LED patterns for status display."""

    # Letter W - Wi-Fi connected
    W: List[int] = [
        0b00000000,
        0b10000001,
        0b10000001,
        0b10010001,
        0b10101001,
        0b11000011,
        0b00000000,
        0b00000000,
    ]

    # Letter T - Tunnel active
    T: List[int] = [
        0b00000000,
        0b11111111,
        0b00011000,
        0b00011000,
        0b00011000,
        0b00011000,
        0b00000000,
        0b00000000,
    ]

    # Letter D - Discord active
    D: List[int] = [
        0b00000000,
        0b11111000,
        0b10000100,
        0b10000010,
        0b10000010,
        0b10000100,
        0b11111000,
        0b00000000,
    ]

    # Checkmark - Success
    CHECKMARK: List[int] = [
        0b00000000,
        0b00000001,
        0b00000011,
        0b10000110,
        0b11001100,
        0b01111000,
        0b00110000,
        0b00000000,
    ]

    # X - Error
    ERROR: List[int] = [
        0b00000000,
        0b10000001,
        0b01000010,
        0b00100100,
        0b00011000,
        0b00100100,
        0b01000010,
        0b10000001,
    ]

    # Wi-Fi symbol - Connected
    WIFI_CONNECTED: List[int] = [
        0b00011000,
        0b00100100,
        0b01011010,
        0b00000000,
        0b00011000,
        0b00100100,
        0b00000000,
        0b00011000,
    ]

    # Wi-Fi barred - Connection error
    WIFI_ERROR: List[int] = [
        0b00011001,
        0b00100110,
        0b01011100,
        0b00001000,
        0b00010000,
        0b00100100,
        0b01000000,
        0b10011000,
    ]

    # Hourglass - Loading/waiting
    HOURGLASS: List[int] = [
        0b11111111,
        0b10000001,
        0b01000010,
        0b00100100,
        0b00100100,
        0b01000010,
        0b10000001,
        0b11111111,
    ]

    # Dot - Small indicator
    DOT: List[int] = [
        0b00000000,
        0b00000000,
        0b00000000,
        0b00011000,
        0b00011000,
        0b00000000,
        0b00000000,
        0b00000000,
    ]

    # All LEDs on - Test pattern
    ALL_ON: List[int] = [
        0b11111111,
        0b11111111,
        0b11111111,
        0b11111111,
        0b11111111,
        0b11111111,
        0b11111111,
        0b11111111,
    ]

    # All LEDs off - Clear
    ALL_OFF: List[int] = [
        0b00000000,
        0b00000000,
        0b00000000,
        0b00000000,
        0b00000000,
        0b00000000,
        0b00000000,
        0b00000000,
    ]


class Animations:
    """Multi-frame animations for LED matrix."""

    # Wi-Fi searching animation - rotating arc
    WIFI_SEARCHING: List[List[int]] = [
        # Frame 1
        [
            0b00011000,
            0b00100100,
            0b01000010,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
        ],
        # Frame 2
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b01011010,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
        ],
        # Frame 3
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00011000,
            0b00100100,
            0b00000000,
            0b00000000,
        ],
        # Frame 4
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00011000,
        ],
    ]

    # Boot animation - expanding square
    BOOT: List[List[int]] = [
        # Frame 1 - center dot
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00011000,
            0b00011000,
            0b00000000,
            0b00000000,
            0b00000000,
        ],
        # Frame 2 - small square
        [
            0b00000000,
            0b00000000,
            0b00111100,
            0b00100100,
            0b00100100,
            0b00111100,
            0b00000000,
            0b00000000,
        ],
        # Frame 3 - medium square
        [
            0b00000000,
            0b01111110,
            0b01000010,
            0b01000010,
            0b01000010,
            0b01000010,
            0b01111110,
            0b00000000,
        ],
        # Frame 4 - full square
        [
            0b11111111,
            0b10000001,
            0b10000001,
            0b10000001,
            0b10000001,
            0b10000001,
            0b10000001,
            0b11111111,
        ],
        # Frame 5 - all on briefly
        Symbols.ALL_ON,
    ]

    # Activity indicator - blinking dot
    ACTIVITY: List[List[int]] = [
        Symbols.DOT,
        Symbols.ALL_OFF,
    ]

    # Idle animation - rotating single LED
    IDLE: List[List[int]] = [
        # Frame 1 - top
        [
            0b00011000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
        ],
        # Frame 2 - top-right
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000110,
        ],
        # Frame 3 - right
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000110,
            0b00000110,
            0b00000000,
            0b00000000,
            0b00000000,
        ],
        # Frame 4 - bottom-right
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b01100000,
        ],
        # Frame 5 - bottom
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00011000,
        ],
        # Frame 6 - bottom-left
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b01100000,
        ],
        # Frame 7 - left
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b01100000,
            0b01100000,
            0b00000000,
            0b00000000,
            0b00000000,
        ],
        # Frame 8 - top-left
        [
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b00000000,
            0b01100000,
        ],
    ]


# Mapping of string names to symbols/animations for easy access
SYMBOL_MAP: Dict[str, List[int]] = {
    "w": Symbols.W,
    "t": Symbols.T,
    "d": Symbols.D,
    "checkmark": Symbols.CHECKMARK,
    "check": Symbols.CHECKMARK,
    "error": Symbols.ERROR,
    "x": Symbols.ERROR,
    "wifi": Symbols.WIFI_CONNECTED,
    "wifi_error": Symbols.WIFI_ERROR,
    "hourglass": Symbols.HOURGLASS,
    "dot": Symbols.DOT,
    "all_on": Symbols.ALL_ON,
    "all_off": Symbols.ALL_OFF,
    "clear": Symbols.ALL_OFF,
}

ANIMATION_MAP: Dict[str, List[List[int]]] = {
    "wifi_searching": Animations.WIFI_SEARCHING,
    "boot": Animations.BOOT,
    "activity": Animations.ACTIVITY,
    "idle": Animations.IDLE,
}
