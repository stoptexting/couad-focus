# LED Boot Test Installation

This script tests the LED hardware at boot time, BEFORE any services start, to help diagnose LED issues.

## What It Does

- Runs automatically at boot (before led-manager, before bootmanager)
- Displays "CONNECTED" with green checkmark on LED panel
- Stays visible for 5 seconds
- Proves LED hardware works independently of daemon/services

## Installation (On Raspberry Pi)

### Step 1: Install the Service

```bash
cd ~/focus

# Copy service file to systemd
sudo cp shared/led_manager/systemd/led-test-boot.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to run at boot
sudo systemctl enable led-test-boot.service
```

### Step 2: Test Manually (Optional)

```bash
# Run the test script directly
sudo python3 shared/led_manager/test_led_boot.py

# Or run via systemd
sudo systemctl start led-test-boot.service

# Check logs
sudo journalctl -u led-test-boot.service -n 50
```

### Step 3: Reboot and Verify

```bash
sudo reboot
```

**What to look for:**
- During boot, LED panel should show "CONNECTED" with green checkmark for 5 seconds
- Then screen clears
- Then normal boot sequence continues

## Troubleshooting

### If "CONNECTED" appears:
✅ LED hardware works!
✅ wiring is correct
✅ rgbmatrix library is installed
✅ Problem is with led-manager daemon or bootmanager

### If nothing appears:
❌ Check hardware connections (13 GPIO pins)
❌ Check power supply to LED panel
❌ Check if rgbmatrix library is installed
❌ Check service logs: `sudo journalctl -u led-test-boot.service`

### Check Service Status

```bash
# View service status
sudo systemctl status led-test-boot.service

# View logs
sudo journalctl -u led-test-boot.service

# Disable if needed
sudo systemctl disable led-test-boot.service
```

## Uninstall

```bash
# Disable and remove service
sudo systemctl disable led-test-boot.service
sudo systemctl stop led-test-boot.service
sudo rm /etc/systemd/system/led-test-boot.service
sudo systemctl daemon-reload
```

## Boot Sequence

With this service enabled:

1. **led-test-boot.service** → Shows "CONNECTED" (5 seconds)
2. **led-manager.service** → Starts LED daemon
3. **bootmanager.service** → Starts your application

This helps isolate exactly where LED problems occur.
