# Focus Project Architecture

## Overview

The Focus project is structured into three main components to manage boot operations, LED display, and task management on a Raspberry Pi 4.

```
focus/
├── shared/led_manager/     # Shared LED controller daemon
├── bootmanager/            # Boot sequence & system management
└── server/                 # Flask task management API (future)
```

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  SHARED LED MANAGER (Daemon Process)                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Owns MAX7219 8x8 LED matrix hardware exclusively          │
│  • Unix domain socket server (/var/run/led-manager.sock)    │
│  • Priority-based command queue (HIGH/MEDIUM/LOW)            │
│  • Prevents concurrent hardware access issues                │
│  systemd: led-manager.service                                │
└──────────────────────────────────────────────────────────────┘
                            ▲
                            │ Socket IPC (JSON protocol)
            ┌───────────────┴────────────────┐
            │                                │
┌───────────┴──────────────┐    ┌────────────┴──────────────┐
│  BOOTMANAGER             │    │  SERVER (Future)          │
│  ━━━━━━━━━━━━━━━━━━━━    │    │  ━━━━━━━━━━━━━━━━━━━━━    │
│  • WiFi management       │    │  • Flask REST API         │
│  • SSH tunnel (ngrok)    │    │  • Task CRUD operations   │
│  • Discord bot           │    │  • Progress calculation   │
│  • Boot sequence         │    │  • HTTP tunnel (ngrok)    │
│  • LED status display    │    │  • LED progress bar       │
│  systemd: bootmanager    │    │  systemd: server.service  │
└──────────────────────────┘    └───────────────────────────┘
```

## Component Details

### 1. Shared LED Manager (`shared/led_manager/`)

**Purpose**: Centralized LED hardware control to prevent concurrency issues.

**Key Features**:
- Daemon process with exclusive hardware access
- Unix domain socket IPC for client communication
- Priority-based command queue (HIGH/MEDIUM/LOW)
- Support for symbols, animations, and progress bars

**Files**:
```
shared/led_manager/
├── led_manager_daemon.py       # Main daemon process
├── led_manager_client.py       # Client library
├── led_hardware.py             # Hardware control (MAX7219)
├── led_animations.py           # Symbols & animations
├── led_protocol.py             # IPC protocol definitions
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── systemd/
│   └── led-manager.service     # Systemd service
├── README.md                   # Documentation
└── example_usage.py            # Usage examples
```

**Systemd Service**: `led-manager.service`
- Starts at boot (multi-user.target)
- Required by bootmanager and server
- Automatic restart on failure

**API Examples**:
```python
from shared.led_manager import LEDManagerClient

led = LEDManagerClient()

# Symbols
led.show_symbol('w')          # WiFi connected
led.show_symbol('error')      # Error symbol

# Animations
led.show_animation('wifi_searching')
led.show_animation('idle')

# Progress (0-100%)
led.show_progress(75)         # 75% complete (6/8 rows lit)
```

---

### 2. Bootmanager (`bootmanager/`)

**Purpose**: Manages Raspberry Pi boot sequence and system services.

**Responsibilities**:
- WiFi connection and monitoring
- SSH tunnel via ngrok
- Discord bot for remote commands
- Job management and logging
- LED status indicators (via LED manager client)

**Key Changes**:
- ✅ Removed direct LED hardware control
- ✅ Now uses LED Manager client
- ✅ Systemd service depends on `led-manager.service`
- ✅ Gracefully handles LED manager unavailability

**Files**:
```
bootmanager/
├── src/
│   ├── main.py                 # Main orchestrator
│   ├── led_client.py           # LED manager client wrapper
│   ├── config.py               # Configuration
│   ├── network/                # WiFi & tunnel management
│   ├── discord/                # Discord bot & commands
│   └── utils/                  # Logger, process runner
├── systemd/
│   └── bootmanager.service     # Systemd service
└── requirements.txt            # Dependencies (no luma)
```

**Boot Sequence**:
1. Load configuration
2. Initialize logger
3. **Connect to LED manager** → Show boot animation
4. Connect to WiFi → Show WiFi searching → Show 'W'
5. Start ngrok tunnel → Show 'T'
6. Start Discord bot → Show 'D'
7. Send boot notification
8. Show idle animation

**Systemd Service**: `bootmanager.service`
- Depends on: `led-manager.service`, `network-online.target`
- Starts automatically at boot
- Restarts on failure (10s delay)

---

### 3. Server (`server/`) - Future Implementation

**Purpose**: Flask REST API for task management with LED progress display.

**Planned Features**:
- Task CRUD operations (create, read, update, delete)
- Progress calculation: `(completed_tasks / total_tasks) * 100`
- LED progress bar updates (0-100% → 0-8 rows lit)
- HTTP ngrok tunnel for web access
- JSON data storage (Sprint 1)

**Planned Structure**:
```
server/
├── app.py                      # Flask entry point
├── api/
│   ├── tasks.py                # Task CRUD endpoints
│   └── progress.py             # Progress calculation
├── models/
│   └── task.py                 # Task data model
├── services/
│   ├── task_service.py         # Business logic
│   └── led_service.py          # LED manager client
├── storage/
│   └── json_storage.py         # Data persistence
├── systemd/
│   └── server.service          # Systemd service
└── requirements.txt            # Flask, etc.
```

**LED Integration**:
```python
from shared.led_manager import LEDManagerClient
from shared.led_manager.led_protocol import Priority

led = LEDManagerClient()

# Update progress with LOW priority (won't interrupt bootmanager)
percentage = (completed_tasks / total_tasks) * 100
led.show_progress(int(percentage), priority=Priority.LOW)
```

**API Endpoints** (planned):
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/:id` - Get task details
- `POST /api/tasks` - Create task
- `PUT /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task
- `GET /api/progress` - Get current progress (auto-updates LED)

---

## Communication Protocol

### Socket IPC (JSON over Unix Socket)

**Socket Path**: `/var/run/led-manager.sock`

**Command Format**:
```json
{
  "command": "show_progress",
  "priority": 0,
  "params": {
    "percentage": 75
  }
}
```

**Response Format**:
```json
{
  "success": true,
  "message": "Command queued",
  "error": null
}
```

**Priority Levels**:
- `0` (LOW): Progress updates, idle animations
- `1` (MEDIUM): Status symbols, boot sequence
- `2` (HIGH): Errors, critical alerts

---

## Installation & Deployment

### 1. Install LED Manager

```bash
cd /home/focus/focus/shared/led_manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

sudo cp systemd/led-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable led-manager.service
sudo systemctl start led-manager.service
```

### 2. Update Bootmanager

```bash
cd /home/focus/focus/bootmanager
source venv/bin/activate
pip install -r requirements.txt  # luma removed

sudo cp systemd/bootmanager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart bootmanager.service
```

### 3. Verify Services

```bash
# Check LED manager
sudo systemctl status led-manager.service
ls -la /var/run/led-manager.sock

# Check bootmanager
sudo systemctl status bootmanager.service
journalctl -u bootmanager.service -n 50
```

---

## Service Dependencies

```
led-manager.service (starts first)
    ├── bootmanager.service (depends on led-manager)
    └── server.service (future, depends on led-manager)
```

Systemd ensures `led-manager.service` starts before dependent services.

---

## Testing

### Test LED Manager

```bash
cd /home/focus/focus/shared/led_manager
source venv/bin/activate
python3 example_usage.py
```

### Test Bootmanager LED Integration

```bash
# Check logs for LED connection
journalctl -u bootmanager.service -n 100 | grep LED

# Expected output:
# "✓ LED manager client connected"
# "LED manager client connected"
```

### Test Server LED Integration (Future)

```bash
cd /home/focus/focus/server
source venv/bin/activate
python3 example_led_usage.py
```

---

## Migration Summary

### What Changed

**Before**:
- Bootmanager directly controlled LED hardware
- Potential concurrency issues if multiple services accessed LEDs
- LED code tightly coupled to bootmanager

**After**:
- LED Manager daemon owns hardware exclusively
- Multiple services communicate via socket IPC
- Priority-based queue prevents conflicts
- Clean separation of concerns

### Files Moved

```
bootmanager/src/display/led_controller.py  →  shared/led_manager/led_hardware.py
bootmanager/src/display/animations.py      →  shared/led_manager/led_animations.py
```

### Dependencies Changed

**Removed from bootmanager/requirements.txt**:
```
luma.led_matrix>=1.7.0
luma.core>=2.4.0
```

**Added to shared/led_manager/requirements.txt**:
```
luma.led_matrix>=1.7.0
luma.core>=2.4.0
psutil>=5.9.0
```

---

## Future Enhancements

1. **Server Implementation**: Flask API for task management
2. **Web Interface**: Next.js frontend for task CRUD
3. **Multiple LED Zones**: Support multiple LED matrices
4. **Animation Library**: Expand symbol/animation collection
5. **Remote LED Control**: API endpoint for LED commands
6. **LED State Persistence**: Remember last display on restart

---

## Troubleshooting

### LED Manager Won't Start

```bash
# Check logs
sudo journalctl -u led-manager.service -n 50

# Try manual start
cd /home/focus/focus/shared/led_manager
source venv/bin/activate
python3 -m led_manager_daemon
```

### Bootmanager Can't Connect to LED Manager

```bash
# Verify socket exists
ls -la /var/run/led-manager.sock

# Check LED manager status
sudo systemctl status led-manager.service

# Check bootmanager logs
journalctl -u bootmanager.service -n 50 | grep LED
```

### Hardware Not Detected (Mock Mode)

```bash
# Edit LED manager service
sudo nano /etc/systemd/system/led-manager.service

# Add environment variable
Environment="LED_MOCK_MODE=true"

# Restart
sudo systemctl restart led-manager.service
```

---

## Documentation

- **LED Manager**: `shared/led_manager/README.md`
- **Bootmanager**: `bootmanager/RASPBERRY_PI_BOOT_MANAGER_SPECS.md`
- **Server**: `server/CONTEXT.md` (task management specs)
- **Architecture**: This file (`ARCHITECTURE.md`)

---

## Contact

For issues or questions, check:
- GitHub Issues: (your repository)
- System logs: `journalctl -u [service-name]`
- LED Manager logs: `/var/log/led-manager.log`
- Bootmanager logs: `/var/log/bootmanager.log`
