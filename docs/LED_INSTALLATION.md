# 64x64 RGB LED Matrix Installation Guide

Complete guide for setting up the HUB75E RGB LED matrix with the Focus task management system.

## Table of Contents
- [Hardware Requirements](#hardware-requirements)
- [Wiring Setup](#wiring-setup)
- [Software Installation](#software-installation)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Hardware Requirements

### Required Components

1. **64x64 RGB LED Matrix Panel**
   - Type: HUB75E connector
   - Size: 64x64 pixels (4096 RGB LEDs)
   - Scan mode: 1/32 scan
   - Pitch: 2.5mm, 3mm, or 4mm

2. **Raspberry Pi**
   - Model: Raspberry Pi 2, 3, or 4 (Pi 5 not yet supported)
   - RAM: 1GB minimum, 2GB+ recommended
   - MicroSD: 16GB+ with Raspberry Pi OS

3. **Power Supply for LED Matrix**
   - Voltage: 5V DC regulated
   - Current: Minimum 4A, recommended 6-8A
   - Connector: Usually barrel jack or screw terminals
   - **CRITICAL**: Do NOT power matrix from Raspberry Pi!

4. **Wiring**
   - 13+ female-to-female jumper wires (for GPIO connections)
   - Or: Adafruit RGB Matrix HAT/Bonnet (recommended for clean setup)

5. **Optional but Recommended**
   - Heat sinks for Raspberry Pi CPU
   - Cooling fan (RGB matrix uses ~30-40% CPU continuously)
   - Ribbon cable or custom PCB for cleaner wiring

### Cost Estimate
- 64x64 RGB Matrix: $30-60
- 5V 8A Power Supply: $15-25
- Jumper wires: $5-10
- **Total**: ~$50-95 (excluding Raspberry Pi)

---

## Wiring Setup

### Understanding HUB75E Connector

The HUB75E connector has 16 pins in two rows:

```
Top row (8 pins):    R1  G1  B1  GND  R2  G2  B2  GND
Bottom row (8 pins):  A   B   C   D   E  CLK LAT  OE
```

**Pin Functions:**
- **R1, G1, B1**: RGB data for top half of panel
- **R2, G2, B2**: RGB data for bottom half of panel
- **A, B, C, D, E**: Row address selection (5 bits = 32 rows)
- **CLK**: Clock signal
- **LAT**: Latch (row data ready)
- **OE**: Output Enable (brightness control via PWM)
- **GND**: Ground (connect to both Pi and power supply)

### GPIO Pin Mapping

#### Standard "Regular" Mapping

Connect the HUB75E pins to Raspberry Pi GPIO as follows:

| HUB75E Pin | Function | → | Raspberry Pi GPIO | Physical Pin |
|------------|----------|---|-------------------|--------------|
| R1 | Red (top) | → | GPIO 11 | Pin 23 |
| G1 | Green (top) | → | GPIO 27 | Pin 13 |
| B1 | Blue (top) | → | GPIO 7 | Pin 26 |
| R2 | Red (bottom) | → | GPIO 8 | Pin 24 |
| G2 | Green (bottom) | → | GPIO 9 | Pin 21 |
| B2 | Blue (bottom) | → | GPIO 10 | Pin 19 |
| A | Row address A | → | GPIO 22 | Pin 15 |
| B | Row address B | → | GPIO 23 | Pin 16 |
| C | Row address C | → | GPIO 24 | Pin 18 |
| D | Row address D | → | GPIO 25 | Pin 22 |
| E | Row address E | → | GPIO 15 | Pin 10 |
| CLK | Clock | → | GPIO 17 | Pin 11 |
| LAT | Latch | → | GPIO 4 | Pin 7 |
| OE | Output Enable | → | GPIO 18 | Pin 12 |
| GND | Ground | → | GND | Pin 6, 9, 14, 20, etc. |

**Total connections: 14 wires (13 data + 1 ground)**

### Power Wiring

**CRITICAL SAFETY INFORMATION:**

1. **NEVER** power the LED matrix from the Raspberry Pi's 5V pins
2. Use a dedicated 5V power supply (4A minimum, 6-8A recommended)
3. Connect power supply ground to both matrix GND AND Raspberry Pi GND (common ground required)

```
Power Supply (5V 8A)
├─ +5V → LED Matrix power input
└─ GND → LED Matrix GND + Raspberry Pi GND (Pin 6)

Raspberry Pi GPIO
└─ 13 data pins → HUB75E connector
```

### Wiring Checklist

- [ ] All 13 GPIO data pins connected correctly
- [ ] Ground connected between Pi and matrix
- [ ] Matrix has separate 5V power supply
- [ ] Power supply can deliver 4A+ at 5V
- [ ] Double-checked all pin numbers (physical vs. GPIO)
- [ ] No loose connections
- [ ] Power supply NOT connected to Pi's 5V pins

### Using Adafruit RGB Matrix HAT (Alternative)

If using an Adafruit RGB Matrix HAT or Bonnet:

1. Simply plug the HAT onto the Raspberry Pi GPIO header
2. Connect the HUB75 cable from HAT to matrix
3. Power the matrix separately
4. Update config: `HARDWARE_MAPPING = 'adafruit-hat'` in `shared/led_manager/config.py`

**Advantages**: Clean wiring, screw terminals for power, level shifters included

---

## Software Installation

### Step 1: Prepare Raspberry Pi

1. **Update system**:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade -y
   ```

2. **Clone or pull the project**:
   ```bash
   cd ~
   git clone [your-repo-url] focus
   # OR if already cloned:
   cd ~/focus
   git pull
   ```

3. **Verify library source exists**:
   ```bash
   ls -l ~/focus/external/rpi-rgb-led-matrix/
   # Should show library source files
   ```

### Step 2: Run Installation Script

**ONE-COMMAND INSTALLATION:**

```bash
cd ~/focus
bash scripts/install_led_library.sh
```

This script will:
- Detect if running on Raspberry Pi
- Install build dependencies (python3-dev, cython3, gcc, g++, make)
- Clean any previous builds
- Compile the C++ library (~3 minutes)
- Build Python bindings (~2 minutes)
- Install the `rgbmatrix` module system-wide
- Verify installation

**Expected output:**
```
========================================
RGB LED Matrix Library Installer
========================================

Checking platform...
Platform: Linux armv7l ✓

...

========================================
Installation Complete! ✓
========================================
```

**Installation time: 5-10 minutes** depending on Raspberry Pi model.

### Step 3: Verify Installation

```bash
python3 -c "from rgbmatrix import RGBMatrix, RGBMatrixOptions; print('Success!')"
```

If successful, you should see: `Success!`

### Step 4: Configure System (Optional)

Some Raspberry Pi models may need additional configuration for optimal performance:

**Edit `/boot/config.txt`:**
```bash
sudo nano /boot/config.txt
```

**Add/modify:**
```ini
# Disable onboard audio (conflicts with PWM timing)
dtparam=audio=off

# Optional: Increase core frequency for stability
core_freq=250

# Optional: Disable Bluetooth if having timing issues
dtoverlay=disable-bt
```

**Reboot:**
```bash
sudo reboot
```

### Step 5: Set GPIO Permissions

The LED matrix requires GPIO access. You can either:

**Option A: Add user to gpio group (recommended)**
```bash
sudo usermod -a -G gpio $USER
# Log out and back in, or:
newgrp gpio
```

**Option B: Run with sudo (not recommended for production)**
```bash
sudo python3 ~/focus/shared/led_manager/led_manager_daemon.py
```

---

## Testing

### Quick Test

Run the example usage script:

```bash
cd ~/focus/shared/led_manager
python3 example_usage.py
```

**Expected behavior:**
1. **Boot animation**: Colorful scrolling pattern
2. **WiFi symbol**: Large green 'W' (scaled from 8x8 to 64x64)
3. **Progress bars**: Vertical bar filling 0% → 100%
   - Bottom third (0-33%): Green
   - Middle third (34-66%): Yellow
   - Top third (67-100%): Red
4. **Clear**: All LEDs turn off

### Test LED Manager Daemon

```bash
cd ~/focus/shared/led_manager
python3 led_manager_daemon.py
```

**Expected output:**
```
LED Manager Daemon starting...
Using RGB Matrix (64x64) - HARDWARE MODE
Socket server listening on /tmp/led_manager.sock
Ready to receive commands
```

### Send Test Commands

In another terminal:

```bash
cd ~/focus/shared/led_manager
python3 -c "
from led_manager_client import LEDManagerClient
client = LEDManagerClient()
client.show_symbol('w')  # Show WiFi symbol
"
```

You should see a large green 'W' on the matrix.

### Test from Flask Server

If the full system is running:

1. Start the server (frontend + backend)
2. Create or complete a task
3. Watch the LED matrix show progress as a vertical bar

---

## Troubleshooting

### Nothing Displays

**Check power:**
```bash
# Is the matrix power LED on?
# Measure voltage at matrix power connector (should be ~5V)
```

**Check library installation:**
```bash
python3 -c "from rgbmatrix import RGBMatrix; print('OK')"
# If ImportError: Library not installed correctly
```

**Check wiring:**
- Verify all 13 data pins are connected
- Verify ground is connected between Pi and matrix
- Double-check GPIO numbers (not physical pin numbers!)

**Check permissions:**
```bash
groups $USER
# Should include 'gpio'

ls -l /dev/gpiomem
# Should be readable by gpio group
```

### Display Flickers or Shows Artifacts

**Increase gpio_slowdown:**

Edit `shared/led_manager/config.py`:
```python
GPIO_SLOWDOWN = 3  # Try: 1, 2, 3, or 4
```

Higher values = more stable but slower refresh rate.

**Try different Raspberry Pi:**
- Pi 4 often needs `gpio_slowdown=3` or `4`
- Pi 3 usually works with `gpio_slowdown=1` or `2`
- Pi 2 may work with `gpio_slowdown=0` or `1`

### Wrong Colors or Missing Colors

**Check RGB pin connections:**
- R1, G1, B1 (top half)
- R2, G2, B2 (bottom half)

**Try swapping wires:**
- If red and blue are swapped, swap R1↔B1 and R2↔B2

### Only Half the Display Works

**Check row address pins:**
- A, B, C, D, E

For 64x64 matrix, all 5 row pins (including E) must be connected.

### Display is Very Dim

**Check power supply:**
- Ensure 5V is actually ~5V (not 4.5V or less)
- Use a power supply with sufficient current (4A+)

**Increase brightness:**

Edit `shared/led_manager/config.py`:
```python
MATRIX_BRIGHTNESS = 100  # 0-100
```

### Audio or PWM Conflicts

**Error: "Can't initialize PWM"**

Disable onboard audio:
```bash
sudo nano /boot/config.txt
# Add: dtparam=audio=off
sudo reboot
```

### High CPU Usage

**Normal**: RGB matrix uses 30-40% of one CPU core continuously.

**If >60%**: Check `gpio_slowdown` value - lower values = higher CPU usage.

### Matrix Shows Garbage/Random Pixels

1. **Check all connections** - especially clock (CLK) and latch (LAT)
2. **Verify common ground** between Pi and matrix
3. **Check voltage levels** - some matrices need 5V logic, Pi outputs 3.3V
   - Consider using Adafruit HAT (has level shifters)

---

## Advanced Configuration

### Configuration File

Edit `shared/led_manager/config.py`:

```python
# Matrix dimensions
MATRIX_ROWS = 64
MATRIX_COLS = 64

# Hardware settings
HARDWARE_MAPPING = 'regular'  # Or 'adafruit-hat'
GPIO_SLOWDOWN = 4             # Pi 4: 3-4, Pi 3: 1-2, Pi 2: 0-1

# Display settings
MATRIX_BRIGHTNESS = 100       # 0-100
PWM_BITS = 11                 # 1-11 (higher = better color, slower refresh)
SCAN_MODE = 1                 # 0=progressive, 1=interlaced

# Performance
PARALLEL_CHAINS = 1           # Number of parallel chains
CHAIN_LENGTH = 1              # Number of panels in series
```

### Performance Tuning

**For best color quality** (slower refresh):
```python
PWM_BITS = 11
GPIO_SLOWDOWN = 4
```

**For faster refresh** (less color depth):
```python
PWM_BITS = 7
GPIO_SLOWDOWN = 1
```

**For multiple panels:**
```python
CHAIN_LENGTH = 2  # Two panels in series
# Or:
PARALLEL_CHAINS = 2  # Two parallel chains
```

### Running as System Service

Create a systemd service for auto-start on boot:

```bash
sudo nano /etc/systemd/system/led-manager.service
```

```ini
[Unit]
Description=LED Matrix Manager
After=network.target

[Service]
Type=simple
User=focus
WorkingDirectory=/home/focus/focus/shared/led_manager
ExecStart=/usr/bin/python3 led_manager_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable led-manager
sudo systemctl start led-manager
sudo systemctl status led-manager
```

---

## Additional Resources

- **Library Documentation**: https://github.com/hzeller/rpi-rgb-led-matrix
- **Wiring Guide**: `external/rpi-rgb-led-matrix/wiring.md`
- **System Documentation**: `SYSTEM_DOCUMENTATION.md`
- **Requirements**: `shared/led_manager/requirements.txt`

---

## Quick Reference

**Installation:**
```bash
bash scripts/install_led_library.sh
```

**Test:**
```bash
python3 shared/led_manager/example_usage.py
```

**Run daemon:**
```bash
python3 shared/led_manager/led_manager_daemon.py
```

**Verify library:**
```bash
python3 -c "from rgbmatrix import RGBMatrix; print('OK')"
```

**Check permissions:**
```bash
groups $USER  # Should include 'gpio'
```

**Mock mode (testing without hardware):**
```bash
LED_MOCK_MODE=true python3 led_manager_daemon.py
```

---

**Last updated**: November 2024
