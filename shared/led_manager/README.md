# LED Manager - Shared LED Control Service

Socket-based LED controller daemon that prevents concurrency issues when multiple services need to control the LED matrix.

## Architecture

The LED Manager uses a daemon process with Unix socket IPC to provide exclusive hardware access:

```
┌─────────────────────────────────────┐
│  LED Manager Daemon                 │
│  - Owns LED hardware exclusively    │
│  - Unix socket server               │
│  - Priority-based command queue     │
│  Socket: /var/run/led-manager/led-manager.sock  │
└─────────────────────────────────────┘
              ▲
              │ Socket IPC
    ┌─────────┴─────────┐
    │                   │
┌───┴────┐      ┌───────┴────┐
│Bootmgr │      │   Server   │
│ Client │      │   Client   │
└────────┘      └────────────┘
```

## Hardware Requirements

**LED Panel:** 64x64 RGB LED Matrix (LED-MATRIX01 or compatible)
- Display type: RGB-LED
- Resolution: 64x64 pixels (4096 LEDs)
- LED size: 3mm pitch
- Dimensions: 192 x 192 x 14 mm
- Supply voltage: 5V
- Maximum power: 40W
- Interface: HUB75E (1/32 scan)
- Operating temperature: -20 to 55°C

**Pin Configuration (HUB75E connector):**
```
Left side:  R1, B1, R2, B2, A, C, CLK, OE
Right side: G1, GND, G2, E, B, D, LAT, GND
```

## Installation

### 1. Install RGB Matrix Library

The hardware requires the Henner Zeller's rpi-rgb-led-matrix library:

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y python3-dev python3-pillow

# Clone and build the library
cd /tmp
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

### 2. Install LED Manager Dependencies

```bash
cd /home/focus/focus/shared/led_manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install Systemd Service

```bash
sudo cp systemd/led-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable led-manager.service
sudo systemctl start led-manager.service
```

### 4. Verify Installation

```bash
# Check service status
sudo systemctl status led-manager.service

# Check if socket exists
ls -la /var/run/led-manager/led-manager.sock
```

## Usage

### From Python Code

```python
from shared.led_manager import LEDManagerClient

# Initialize client
led = LEDManagerClient()

# Show symbols
led.show_symbol('w')           # WiFi connected
led.show_symbol('t')           # Tunnel active
led.show_symbol('d')           # Discord active
led.show_symbol('error')       # Error symbol
led.show_symbol('checkmark')   # Success symbol

# Show animations
led.show_animation('wifi_searching')  # Loop forever
led.show_animation('boot', duration=2, frame_delay=0.3)
led.show_animation('idle')

# Show progress (0-100%)
led.show_progress(0)    # Empty bar
led.show_progress(50)   # Half full
led.show_progress(100)  # Full bar

# Convenience methods
led.show_boot()              # Boot animation
led.show_wifi_searching()    # WiFi search animation
led.show_wifi_connected()    # 'W' symbol
led.show_wifi_error()        # WiFi error symbol
led.show_tunnel_active()     # 'T' symbol
led.show_discord_active()    # 'D' symbol
led.show_idle()              # Idle animation

# Control
led.stop_current_animation()
led.clear()
```

### Priority System

Commands have three priority levels:

- **HIGH** (2): Errors, critical status - interrupts everything
- **MEDIUM** (1): Boot sequence, status symbols - normal priority
- **LOW** (0): Idle animations, progress updates - can be interrupted

```python
from shared.led_manager.led_protocol import Priority

# High priority error
led.show_error()  # Uses HIGH priority by default

# Low priority progress update
led.show_progress(75, priority=Priority.LOW)
```

## Protocol

### Command Format (JSON over Unix socket)

```json
{
  "command": "show_symbol",
  "priority": 1,
  "params": {
    "symbol": "w"
  }
}
```

### Response Format

```json
{
  "success": true,
  "message": "Command queued",
  "error": null
}
```

### Available Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `show_symbol` | `symbol: str` | Display static symbol |
| `show_animation` | `animation: str, duration?: float, frame_delay?: float` | Display animation |
| `show_progress` | `percentage: int` | Show progress bar (0-100%) |
| `stop_animation` | - | Stop current animation |
| `clear` | - | Clear display |
| `test` | - | Run test sequence |
| `shutdown` | - | Shutdown daemon |

## Available Symbols

- `w` - WiFi connected (letter W)
- `t` - Tunnel active (letter T)
- `d` - Discord active (letter D)
- `checkmark` / `check` - Success checkmark
- `error` / `x` - Error cross
- `wifi` - WiFi symbol
- `wifi_error` - WiFi barred (error)
- `hourglass` - Loading/waiting
- `dot` - Small dot

## Available Animations

- `wifi_searching` - Rotating WiFi search animation
- `boot` - Expanding square boot animation
- `activity` - Blinking activity indicator
- `idle` - Rotating single LED

## Progress Bar Display

The progress bar uses the full 64x64 LED matrix vertically with color gradient:

- 0% = 0 rows lit (empty)
- 50% = 32 rows lit (half)
- 100% = 64 rows lit (full)

Progress fills from bottom to top with color coding:
- **Green** (bottom third): 0-33%
- **Yellow** (middle third): 34-66%
- **Red** (top third): 67-100%

The high resolution provides smooth, granular progress indication.

## Troubleshooting

### Daemon won't start

```bash
# Check logs
sudo journalctl -u led-manager.service -n 50

# Check if port is in use
ls -la /var/run/led-manager/led-manager.sock

# Try starting manually
cd /home/focus/focus/shared/led_manager
source venv/bin/activate
python3 -m led_manager_daemon
```

### Client can't connect

```bash
# Check daemon is running
sudo systemctl status led-manager.service

# Check socket permissions
ls -la /var/run/led-manager/led-manager.sock

# Test connection
python3 -c "from shared.led_manager import LEDManagerClient; led = LEDManagerClient(); led.show_symbol('w')"
```

### Hardware not detected

Set mock mode to test without hardware:

```bash
# Edit systemd service
sudo nano /etc/systemd/system/led-manager.service

# Add environment variable
Environment="LED_MOCK_MODE=true"

# Restart service
sudo systemctl restart led-manager.service
```

## Configuration

Environment variables:

- `LED_SOCKET_PATH` - Socket path (default: `/var/run/led-manager/led-manager.sock`)
- `LED_MOCK_MODE` - Mock mode for testing (default: `false`)

## Files

```
shared/led_manager/
├── __init__.py                  # Package exports
├── led_manager_daemon.py        # Main daemon process
├── led_manager_client.py        # Client library
├── led_hardware.py              # Hardware control
├── led_animations.py            # Symbol/animation definitions
├── led_protocol.py              # IPC protocol
├── config.py                    # Configuration
├── requirements.txt             # Dependencies
├── systemd/
│   └── led-manager.service      # Systemd service file
└── README.md                    # This file
```

## Testing

Run hardware test sequence:

```python
from shared.led_manager import LEDManagerClient

led = LEDManagerClient()
led.test()  # Runs complete test sequence
```

## Development

To add new symbols or animations:

1. Edit `led_animations.py`
2. Add pattern to `Symbols` or `Animations` class
3. Add mapping to `SYMBOL_MAP` or `ANIMATION_MAP`
4. Restart daemon: `sudo systemctl restart led-manager.service`
