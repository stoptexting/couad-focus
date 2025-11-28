# Focus - Complete System Documentation

**Version:** 1.0
**Last Updated:** 2025-11-01
**Target Platform:** Raspberry Pi 4

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Components](#components)
   - [Server (Backend)](#server-backend)
   - [Frontend](#frontend)
   - [Bootmanager](#bootmanager)
   - [LED Manager](#led-manager)
4. [Setup & Installation](#setup--installation)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Hardware Integration](#hardware-integration)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)
10. [Development Guide](#development-guide)

---

## System Overview

Focus is a Raspberry Pi 4-based task management system with physical LED progress visualization. It provides a web interface for managing tasks while displaying real-time progress on an 8x8 LED matrix.

### Key Features

- **Web-Based Task Management**: Create, update, and delete tasks through a modern React interface
- **Physical Progress Visualization**: 8x8 LED matrix displays task completion progress (0-100%)
- **Remote Access**: Secure tunneling via ngrok with basic authentication
- **Discord Integration**: Remote system control and monitoring via Discord bot
- **Automatic Boot Management**: Handles WiFi, services, tunnels, and LED status automatically
- **Real-Time Updates**: Frontend polls server every 2 seconds for instant feedback

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Flask (Python) | 3.0.0 |
| Frontend | Next.js (React, TypeScript) | 16.0.0 |
| Database | SQLite (via SQLAlchemy) | 3.1.0 |
| Bootmanager | Python asyncio | 3.11+ |
| LED Manager | Python daemon | 3.11+ |
| Hardware | 64x64 RGB LED Matrix (HUB75E) | rpi-rgb-led-matrix |
| Reverse Proxy | Nginx | Latest |
| Tunneling | Ngrok | Latest |

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  User's Browser                                         │
│  ├─ Next.js Frontend (React)                           │
│  └─ HTTP Requests to /api/*                            │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Ngrok HTTP Tunnel (Basic Auth)                        │
│  https://xyz.ngrok.io → Raspberry Pi Port 80           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Nginx Reverse Proxy (Port 80)                         │
│  ├─ /      → localhost:3000 (Frontend)                 │
│  └─ /api/* → localhost:5001 (Backend)                  │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
       ┌───────▼──────┐      ┌────────▼────────┐
       │   Frontend   │      │  Flask Server   │
       │   Next.js    │      │   Port 5001     │
       │   Port 3000  │      │                 │
       │              │      │  ┌──────────┐   │
       │              │      │  │ TaskSvc  │   │
       │              │      │  └────┬─────┘   │
       │              │      │       │         │
       │              │      │  ┌────▼─────┐   │
       │              │      │  │ LEDSvc   │   │
       └──────────────┘      │  └────┬─────┘   │
                             └───────┼─────────┘
                                     │ Socket IPC
                                     ▼
        ┌────────────────────────────────────────────────┐
        │  LED Manager Daemon                            │
        │  Unix Socket: /var/run/led-manager.sock        │
        │  ├─ Priority Queue (HIGH/MEDIUM/LOW)           │
        │  └─ Exclusive Hardware Access                  │
        └─────────────────┬──────────────────────────────┘
                          │
                          ▼
        ┌────────────────────────────────────────────────┐
        │  MAX7219 8x8 LED Matrix (SPI)                  │
        │  Physical progress visualization (0-8 rows)    │
        └────────────────────────────────────────────────┘
                          ▲
                          │ Socket IPC
        ┌─────────────────┴──────────────────────────────┐
        │  Bootmanager                                   │
        │  ├─ WiFi Management                            │
        │  ├─ Tunnel Management (ngrok SSH + HTTP)       │
        │  ├─ Service Manager (Server + Frontend)        │
        │  ├─ Nginx Manager                              │
        │  └─ Discord Bot                                │
        └────────────────────────────────────────────────┘
```

### Communication Patterns

| From | To | Protocol | Purpose |
|------|-----|----------|---------|
| Browser | Frontend | HTTP | UI rendering |
| Frontend | Backend | HTTP REST | Task CRUD operations |
| Backend | LED Manager | Unix Socket | Progress updates (LOW priority) |
| Bootmanager | LED Manager | Unix Socket | Status symbols (HIGH/MEDIUM priority) |
| Discord Bot | System | Discord API | Remote control |
| External | Raspberry Pi | Ngrok SSH | Emergency access |
| External | Raspberry Pi | Ngrok HTTP | Web UI access |

### Data Flow: Task Creation

```
User clicks "Add Task"
    ↓
Frontend sends POST /api/tasks
    ↓
Nginx proxies to localhost:5001/api/tasks
    ↓
Flask server receives request
    ↓
TaskService creates task in SQLite
    ↓
TaskService calculates new progress (completed/total * 100)
    ↓
LEDService sends progress update to LED Manager (LOW priority)
    ↓
LED Manager queues command
    ↓
LED Manager updates LED matrix (0-8 rows lit based on percentage)
    ↓
Flask returns task JSON to frontend
    ↓
Frontend updates UI with new task
    ↓
React Query auto-refetches after 2 seconds
```

---

## Components

### Server (Backend)

**Location:** `/server/`
**Technology:** Flask 3.0.0 (Python)
**Port:** 5001
**Database:** SQLite (via SQLAlchemy)

#### Responsibilities

- Task CRUD operations (Create, Read, Update, Delete)
- Progress calculation: `(completed_tasks / total_tasks) * 100`
- Automatic LED display updates after every task operation
- RESTful API for frontend consumption
- Database schema management via SQLAlchemy

#### Project Structure

```
server/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration classes
│   ├── models/
│   │   └── task.py           # Task model (SQLAlchemy)
│   ├── routes/
│   │   ├── tasks.py          # Task CRUD endpoints
│   │   ├── progress.py       # Progress statistics
│   │   └── leds.py           # LED control endpoints
│   ├── services/
│   │   ├── task_service.py   # Business logic for tasks
│   │   └── led_service.py    # LED Manager integration
│   └── extensions.py         # SQLAlchemy db instance
├── run.py                    # Production entry point
├── requirements.txt          # Python dependencies
└── venv/                     # Virtual environment
```

#### Key Files

**`app/models/task.py`** - Task Model
```python
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default='new')  # 'new' or 'completed'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**`app/services/task_service.py`** - Business Logic
- `get_all_tasks()`: Retrieve all tasks
- `get_task(task_id)`: Get single task by ID
- `create_task(data)`: Create new task, update LEDs
- `update_task(task_id, data)`: Update task, recalculate progress
- `delete_task(task_id)`: Delete task, update LEDs
- `get_progress_stats()`: Calculate completion percentage

**`app/services/led_service.py`** - LED Integration
```python
def update_progress(self, percentage: float):
    """Send progress update to LED Manager with LOW priority"""
    client = LEDManagerClient()
    client.show_progress(percentage)
```

#### Dependencies

```
Flask==3.0.0
Flask-CORS==4.0.0
SQLAlchemy==3.1.0
python-dotenv==1.0.0
```

#### Running Locally

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Server starts on `http://localhost:5001`

---

### Frontend

**Location:** `/frontend/`
**Technology:** Next.js 16.0.0 (React 19.2.0, TypeScript)
**Port:** 3000

#### Responsibilities

- Task management user interface
- Real-time progress visualization with gauge component
- Auto-refresh every 2 seconds via TanStack React Query
- Task creation and editing via modal dialogs
- Responsive grid layout for task cards

#### Project Structure

```
frontend/
├── app/
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Main task list page
│   └── globals.css           # Global styles
├── components/
│   ├── TaskCard.tsx          # Individual task display
│   ├── ProgressGauge.tsx     # Circular progress indicator
│   └── TaskFormModal.tsx     # Create/edit dialog
├── lib/
│   ├── api/
│   │   ├── client.ts         # Axios instance
│   │   └── tasks.ts          # Task API functions
│   └── types/
│       └── task.ts           # TypeScript interfaces
├── package.json
└── next.config.ts
```

#### Key Features

**Auto-Refresh**
```typescript
// React Query auto-refetch configuration
const { data: tasks } = useQuery({
  queryKey: ['tasks'],
  queryFn: fetchTasks,
  refetchInterval: 2000  // Poll every 2 seconds
})
```

**Progress Gauge**
- Displays completion percentage (0-100%)
- Color-coded: Red (0-33%), Yellow (34-66%), Green (67-100%)
- Shows completed/total task counts

**Task Cards**
- Title and description
- Status badge (New/Completed)
- Edit and Delete buttons
- Timestamp display

#### API Client Configuration

**Development:** Uses relative URLs through nginx proxy
**Production:** Also uses relative URLs (proxied by nginx)

```typescript
// lib/api/client.ts
const apiClient = axios.create({
  baseURL: '/api',  // Proxied through nginx
  timeout: 10000,
});
```

#### Dependencies (Key)

```json
{
  "next": "16.0.0",
  "react": "19.2.0",
  "typescript": "5.9.3",
  "@tanstack/react-query": "5.90.5",
  "axios": "1.12.2",
  "@radix-ui/react-dialog": "1.1.4",
  "tailwindcss": "3.4.18",
  "lucide-react": "0.546.0"
}
```

#### Running Locally

```bash
cd frontend
npm install
npm run dev
```

Frontend starts on `http://localhost:3000`

---

### Bootmanager

**Location:** `/bootmanager/`
**Technology:** Python 3.11+ with asyncio
**Purpose:** Boot orchestration and system management

#### Responsibilities

1. **WiFi Management**: Connect to configured hotspot, handle reconnections
2. **Tunnel Management**: Start ngrok SSH and HTTP tunnels
3. **Service Management**: Start and monitor server + frontend processes
4. **Nginx Management**: Generate config from template, start reverse proxy
5. **Discord Bot**: Enable remote control and status monitoring
6. **LED Coordination**: Display boot status symbols (W, T, D)
7. **Monitoring Loop**: Check WiFi, tunnels, and services every 60 seconds

#### Project Structure

```
bootmanager/
├── src/
│   ├── main.py                    # Entry point, boot sequence
│   ├── config/
│   │   └── settings.py            # Load secrets.env
│   ├── network/
│   │   ├── wifi_manager.py        # NetworkManager WiFi control
│   │   └── tunnel_manager.py      # Ngrok tunnel management
│   ├── services/
│   │   ├── job_manager.py         # Background process tracking
│   │   └── service_manager.py     # Server + frontend lifecycle
│   ├── discord/
│   │   ├── bot.py                 # Discord bot commands
│   │   └── commands.py            # Command handlers
│   ├── nginx_manager.py           # Nginx config generation
│   └── led_client.py              # LED Manager wrapper
├── config/
│   └── nginx.conf.template        # Nginx template
├── systemd/
│   └── bootmanager.service        # Systemd unit file
├── requirements.txt
└── venv/
```

#### Boot Sequence (11 Steps)

The bootmanager follows this exact sequence on startup:

```
1. Git Pull
   └─ Updates code from repository

2. Load Configuration
   └─ Reads ~/.config/focus/secrets.env

3. Connect to LED Manager
   └─ Establishes socket connection
   └─ Shows boot animation

4. WiFi Connection
   └─ Connects to configured hotspot
   └─ Shows 'W' symbol on LED when connected

5. Query SSH Tunnel
   └─ Checks ngrok-ssh.service status
   └─ Logs SSH tunnel URL

6. Initialize Job Manager
   └─ Sets up background process tracking

7. Start Service Manager
   └─ Prepares to manage server/frontend

8. Start Backend Server
   └─ Launches Flask on port 5001
   └─ Waits for health check

9. Start Frontend
   └─ Launches Next.js on port 3000

10. Setup Nginx
    └─ Generates config from template
    └─ Starts reverse proxy on port 80
    └─ Starts HTTP tunnel (shows 'T' on LED)

11. Start Discord Bot
    └─ Connects to Discord
    └─ Sends boot notification with URLs
    └─ Shows 'D' symbol on LED
```

#### Key Modules

**WiFi Manager** (`src/network/wifi_manager.py`)
```python
class WiFiManager:
    def connect_to_hotspot(ssid: str, password: str) -> bool
    def get_ip_address() -> str
    def check_connection() -> bool
```
- Uses NetworkManager D-Bus interface
- Automatic reconnection on failure
- Returns IP address for status reporting

**Tunnel Manager** (`src/network/tunnel_manager.py`)
```python
class TunnelManager:
    def start_http_tunnel(port: int, auth: tuple) -> str
    def check_tunnel_status() -> bool
    def restart_tunnel()
```
- Manages ngrok HTTP tunnel (bootmanager-controlled)
- Monitors ngrok-ssh.service (systemd-controlled)
- Returns public URLs for remote access

**Service Manager** (`src/services/service_manager.py`)
```python
class ServiceManager:
    def start_server() -> subprocess.Popen
    def start_frontend() -> subprocess.Popen
    def check_health() -> bool
    def restart_if_needed()
```
- Starts server and frontend as background processes
- Health check endpoints
- Auto-restart on failure

**Discord Bot** (`src/discord/bot.py`)

Commands:
- `/status` - System status (WiFi, tunnels, services)
- `/jobs` - List running background processes
- `/start <job>` - Start a service (server, frontend)
- `/stop <job>` - Stop a service
- `/tail <job>` - View recent logs
- `/restart <job>` - Restart a service

**Nginx Manager** (`src/nginx_manager.py`)
```python
class NginxManager:
    def generate_config(frontend_port, backend_port)
    def start_nginx()
    def reload_nginx()
```
- Generates `/etc/nginx/sites-available/focus`
- Creates reverse proxy configuration
- Enables and reloads nginx

#### Monitoring Loop

Runs every 60 seconds:
```python
while True:
    # Check WiFi connection
    if not wifi_manager.check_connection():
        wifi_manager.reconnect()

    # Check SSH tunnel (log if down)
    ssh_status = tunnel_manager.check_ssh_tunnel()

    # Check HTTP tunnel (restart if down)
    if not tunnel_manager.check_http_tunnel():
        tunnel_manager.restart_http_tunnel()

    # Check services (restart if needed)
    service_manager.restart_if_needed()

    await asyncio.sleep(60)
```

#### Dependencies

```
discord.py==2.3.0
requests==2.31.0
netifaces==0.11.0
PyYAML==6.0
python-dotenv==1.0.0
```

#### Systemd Service

**File:** `systemd/bootmanager.service`
```ini
[Unit]
Description=Focus Bootmanager
After=network-online.target led-manager.service
Requires=led-manager.service

[Service]
Type=simple
User=focus
WorkingDirectory=/home/focus/focus/bootmanager
ExecStart=/home/focus/focus/bootmanager/venv/bin/python src/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

### LED Manager

**Location:** `/shared/led_manager/`
**Technology:** Python 3.11+ daemon
**Hardware:** MAX7219 8x8 LED Matrix
**IPC:** Unix domain socket

#### Purpose

Centralized daemon for exclusive LED hardware control. Prevents concurrent access issues by providing a socket-based IPC architecture where multiple clients can send commands through a priority queue.

#### Architecture

**Problem:** Multiple processes (bootmanager, server) need to control the LED matrix, but direct hardware access from multiple processes causes conflicts.

**Solution:** Single daemon process with exclusive hardware access. All other components communicate via Unix socket.

#### Project Structure

```
shared/led_manager/
├── led_manager_daemon.py      # Main daemon process
├── led_manager_client.py      # Client library
├── led_hardware.py            # Direct MAX7219 control
├── led_animations.py          # Symbols and animations
├── led_protocol.py            # Command/response format
├── systemd/
│   └── led-manager.service    # Systemd unit file
├── example_usage.py           # Usage examples
└── requirements.txt
```

#### Components

**1. Daemon** (`led_manager_daemon.py`)

Entry point: `python led_manager_daemon.py`

```python
class LEDManagerDaemon:
    def __init__(self):
        self.socket_path = "/var/run/led-manager/led-manager.sock"
        self.command_queue = PriorityQueue()  # Priority-based
        self.hardware = LEDHardware()

    def run(self):
        # Start worker thread for command processing
        threading.Thread(target=self._worker).start()

        # Accept client connections
        while True:
            conn, addr = self.sock.accept()
            self._handle_client(conn)
```

**Multi-threaded Architecture:**
- **Main thread:** Accepts client connections, receives commands
- **Worker thread:** Processes commands from priority queue
- **Priority levels:** HIGH (2), MEDIUM (1), LOW (0)

**2. Client Library** (`led_manager_client.py`)

```python
class LEDManagerClient:
    def show_symbol(self, symbol: str, priority: str = 'MEDIUM'):
        """Show a single symbol (w, t, d, error, check)"""

    def show_animation(self, animation: str, priority: str = 'HIGH'):
        """Start looping animation (boot, wifi_searching, idle)"""

    def show_progress(self, percentage: float, priority: str = 'LOW'):
        """Display progress bar (0-100% → 0-8 rows)"""

    def clear(self, priority: str = 'MEDIUM'):
        """Clear the display"""

    def stop_animation(self, priority: str = 'HIGH'):
        """Stop any running animation"""
```

**Auto-retry:** 3 attempts with 2-second timeout per command

**3. Hardware Controller** (`led_hardware.py`)

```python
class LEDHardware:
    def __init__(self, mock_mode: bool = False):
        if mock_mode:
            self.device = None  # Console output only
        else:
            self.device = max7219(
                spi(port=0, device=0, bus_speed_hz=8000000),
                width=8, height=8
            )

    def display_matrix(self, matrix: List[List[int]]):
        """Display 8x8 matrix on LED"""

    def clear(self):
        """Turn off all LEDs"""
```

**4. Animations** (`led_animations.py`)

**Symbols:**
- `W` - WiFi connected
- `T` - Tunnel established
- `D` - Discord bot connected
- Error symbol (X)
- Checkmark

**Animations:**
- `boot` - Startup animation
- `wifi_searching` - Scanning animation
- `idle` - Rotating dot (1-second loop)

**Progress Bar:**
```
0-12%:   1 row lit  ████████
13-24%:  2 rows lit ████████
25-37%:  3 rows lit ████████
38-49%:  4 rows lit ████████
50-62%:  5 rows lit ████████
63-74%:  6 rows lit ████████
75-87%:  7 rows lit ████████
88-100%: 8 rows lit ████████
```

**5. Protocol** (`led_protocol.py`)

**Command Format (JSON):**
```json
{
  "command": "SHOW_PROGRESS",
  "params": {
    "percentage": 75.5
  },
  "priority": "LOW"
}
```

**Response Format (JSON):**
```json
{
  "status": "success",
  "message": "Command executed successfully"
}
```

**Command Types:**
- `SHOW_SYMBOL` - Display single symbol
- `SHOW_ANIMATION` - Start looping animation
- `SHOW_PROGRESS` - Display progress bar
- `CLEAR` - Clear display
- `STOP_ANIMATION` - Stop animation
- `TEST` - Hardware test

#### Usage Examples

**From Server (Python):**
```python
from shared.led_manager import LEDManagerClient

led = LEDManagerClient()
led.show_progress(75.0)  # 75% completion (LOW priority)
```

**From Bootmanager (Python):**
```python
from led_client import LEDClient

led = LEDClient()
led.show_wifi_searching()  # HIGH priority animation
led.show_symbol('w')       # WiFi connected (MEDIUM priority)
led.show_symbol('t')       # Tunnel up (MEDIUM priority)
```

**Command-Line Testing:**
```bash
# Send raw JSON command
echo '{"command":"SHOW_SYMBOL","params":{"symbol":"w"},"priority":"MEDIUM"}' | \
  socat - UNIX-CONNECT:/var/run/led-manager/led-manager.sock
```

#### Hardware Connection

**Wiring Diagram:**

```
MAX7219 Module          Raspberry Pi 4
────────────────────────────────────────
VCC        ────────────> Pin 2  (5V)
GND        ────────────> Pin 6  (GND)
DIN (Data) ────────────> Pin 19 (GPIO 10, MOSI)
CS (Chip)  ────────────> Pin 24 (GPIO 8, CE0)
CLK (Clock)────────────> Pin 23 (GPIO 11, SCLK)
```

**SPI Configuration:**
- **Port:** 0
- **Device:** 0
- **Bus Speed:** 8 MHz
- **Interface:** `/dev/spidev0.0`

**Enable SPI:**
```bash
sudo raspi-config
# Interface Options > SPI > Enable
```

#### Dependencies

```
luma.led_matrix==1.7.0
luma.core==2.4.0
spidev==3.5
Pillow==10.0.0
```

#### Systemd Service

**File:** `systemd/led-manager.service`
```ini
[Unit]
Description=Focus LED Manager Daemon
After=local-fs.target

[Service]
Type=exec
User=focus
WorkingDirectory=/home/focus/focus/shared/led_manager
ExecStartPre=/bin/mkdir -p /var/run/led-manager
ExecStart=/home/focus/focus/shared/led_manager/venv/bin/python led_manager_daemon.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Start Order:** LED Manager must start before bootmanager and server.

---

## Setup & Installation

### Prerequisites

**Hardware:**
- Raspberry Pi 4 (recommended)
- MAX7219 8x8 LED Matrix
- 5 jumper wires for SPI connection
- Power supply (5V, 3A recommended)
- SD card (16GB+)

**Software:**
- Raspberry Pi OS (64-bit recommended)
- Python 3.11+
- Node.js 18+ and npm
- Git
- Internet connection (for initial setup)

### Installation Steps

#### 1. Clone Repository

```bash
cd ~
git clone <repository-url> focus
cd focus
```

#### 2. Run Installation Script

The automated installer handles all dependencies:

```bash
chmod +x install.sh
sudo ./install.sh
```

**What the installer does:**
1. Updates system packages
2. Installs Python 3.11, pip, venv
3. Installs Node.js 18 and npm
4. Installs git, nginx, openssh-server
5. Enables SPI interface for LED matrix
6. Installs ngrok
7. Creates Python virtual environments
8. Installs Python dependencies (server, bootmanager, led-manager)
9. Installs npm dependencies (frontend)
10. Copies systemd service files
11. Creates log directories with proper permissions
12. Enables and starts services

#### 3. Configure Secrets

Create configuration file:

```bash
mkdir -p ~/.config/focus
nano ~/.config/focus/secrets.env
```

Add the following:

```bash
# WiFi Settings
WIFI_SSID=YourHotspotName
WIFI_PASSWORD=YourWiFiPassword

# Discord Bot
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_discord_channel_id_here

# Ngrok
NGROK_AUTH_TOKEN=your_ngrok_auth_token_here
NGROK_HTTP_USERNAME=admin
NGROK_HTTP_PASSWORD=secure_password_here

# LED Manager
LED_SOCKET_PATH=/var/run/led-manager/led-manager.sock
LED_MOCK_MODE=false

# Service Ports
SERVER_PORT=5001
FRONTEND_PORT=3000
```

**Getting Tokens:**

**Discord Bot Token:**
1. Go to https://discord.com/developers/applications
2. Create New Application
3. Go to "Bot" section, click "Add Bot"
4. Copy token
5. Enable "Message Content Intent" under Privileged Gateway Intents
6. Invite bot to your server (OAuth2 > URL Generator > bot scope)

**Discord Channel ID:**
1. Enable Developer Mode in Discord (User Settings > Advanced)
2. Right-click your channel > Copy ID

**Ngrok Auth Token:**
1. Sign up at https://ngrok.com
2. Go to https://dashboard.ngrok.com/get-started/your-authtoken
3. Copy your auth token

#### 4. Connect LED Matrix

Wire the MAX7219 to Raspberry Pi:

```
MAX7219 VCC  → RPi Pin 2  (5V)
MAX7219 GND  → RPi Pin 6  (GND)
MAX7219 DIN  → RPi Pin 19 (GPIO 10, MOSI)
MAX7219 CS   → RPi Pin 24 (GPIO 8, CE0)
MAX7219 CLK  → RPi Pin 23 (GPIO 11, SCLK)
```

Verify SPI is enabled:
```bash
ls /dev/spidev*
# Should show: /dev/spidev0.0  /dev/spidev0.1
```

#### 5. Start Services

```bash
# Start LED Manager first
sudo systemctl start led-manager

# Start bootmanager (will start everything else)
sudo systemctl start bootmanager

# Check status
sudo systemctl status led-manager
sudo systemctl status bootmanager

# View logs
journalctl -u led-manager -f
journalctl -u bootmanager -f
```

#### 6. Verify Installation

**Check LED Manager:**
```bash
# Test LED with a symbol
cd ~/focus/shared/led_manager
source venv/bin/activate
python example_usage.py
```

**Check Services:**
```bash
# Server health check
curl http://localhost:5001/health

# Frontend (should see HTML)
curl http://localhost:3000

# Nginx proxy
curl http://localhost/api/health
```

**Get Public URLs:**
Check Discord for boot notification, or run:
```bash
# SSH tunnel
systemctl status ngrok-ssh | grep "url="

# HTTP tunnel
journalctl -u bootmanager | grep "HTTP Tunnel"
```

---

## Configuration

### Environment Variables

**File:** `~/.config/focus/secrets.env`

| Variable | Description | Example |
|----------|-------------|---------|
| `WIFI_SSID` | WiFi network name | `MyPhone` |
| `WIFI_PASSWORD` | WiFi password | `password123` |
| `DISCORD_BOT_TOKEN` | Discord bot auth token | `MTIzNDU2Nzg5...` |
| `DISCORD_CHANNEL_ID` | Discord channel for notifications | `1234567890123456789` |
| `NGROK_AUTH_TOKEN` | Ngrok authentication token | `2abc123...` |
| `NGROK_HTTP_USERNAME` | HTTP tunnel basic auth username | `admin` |
| `NGROK_HTTP_PASSWORD` | HTTP tunnel basic auth password | `secure_pass` |
| `LED_SOCKET_PATH` | LED Manager socket location | `/var/run/led-manager/led-manager.sock` |
| `LED_MOCK_MODE` | Use mock LED (no hardware) | `false` |
| `SERVER_PORT` | Flask server port | `5001` |
| `FRONTEND_PORT` | Next.js port | `3000` |

### Nginx Configuration

**Template:** `bootmanager/config/nginx.conf.template`

The bootmanager generates `/etc/nginx/sites-available/focus` from this template at boot.

**Key Settings:**
- Listens on port 80
- Routes `/` to frontend (port 3000)
- Routes `/api/` to backend (port 5001)
- WebSocket support for Next.js hot reload
- Client max body size: 10M

**Manual Reload:**
```bash
sudo nginx -t  # Test config
sudo systemctl reload nginx
```

### Service Configuration

**LED Manager:** `shared/led_manager/systemd/led-manager.service`
- User: `focus`
- Socket: `/var/run/led-manager/led-manager.sock`
- Logs: `/var/log/led-manager.log`

**Bootmanager:** `bootmanager/systemd/bootmanager.service`
- User: `focus`
- Depends on: `led-manager.service`, `network-online.target`
- Logs: `/var/log/bootmanager.log`

**Ngrok SSH:** `ngrok-ssh.service` (created by installer)
- Provides persistent SSH tunnel
- Auto-restarts on failure
- Independent of bootmanager

### Frontend Configuration

**File:** `frontend/.env.local` (optional for development)

```bash
NEXT_PUBLIC_API_URL=http://localhost:5001
```

**Note:** In production, frontend uses relative URLs (`/api`) that nginx proxies to the backend.

### Server Configuration

**File:** `server/app/config.py`

```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tasks.db'
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
```

---

## API Reference

### Base URL

**Local:** `http://localhost:5001`
**Production (proxied):** `https://your-ngrok-url.ngrok.io/api`

### Authentication

No authentication required (basic auth on ngrok tunnel).

### Endpoints

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /api/tasks

List all tasks.

**Response:**
```json
{
  "tasks": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Complete documentation",
      "description": "Write full system docs",
      "status": "new",
      "created_at": "2025-11-01T10:30:00Z",
      "updated_at": "2025-11-01T10:30:00Z"
    }
  ]
}
```

#### GET /api/tasks/:id

Get single task by ID.

**Parameters:**
- `id` (path) - Task UUID

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Complete documentation",
  "description": "Write full system docs",
  "status": "new",
  "created_at": "2025-11-01T10:30:00Z",
  "updated_at": "2025-11-01T10:30:00Z"
}
```

**Error (404):**
```json
{
  "error": "Task not found"
}
```

#### POST /api/tasks

Create new task.

**Request Body:**
```json
{
  "title": "New task title",
  "description": "Optional description",
  "status": "new"
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "New task title",
  "description": "Optional description",
  "status": "new",
  "created_at": "2025-11-01T10:30:00Z",
  "updated_at": "2025-11-01T10:30:00Z"
}
```

**Side Effects:**
- Recalculates progress percentage
- Sends LED update with LOW priority

#### PUT /api/tasks/:id

Update existing task.

**Parameters:**
- `id` (path) - Task UUID

**Request Body:**
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "status": "completed"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Updated title",
  "description": "Updated description",
  "status": "completed",
  "created_at": "2025-11-01T10:30:00Z",
  "updated_at": "2025-11-01T11:45:00Z"
}
```

**Side Effects:**
- Recalculates progress percentage
- Sends LED update with LOW priority

#### DELETE /api/tasks/:id

Delete task.

**Parameters:**
- `id` (path) - Task UUID

**Response (204):**
```
(empty body)
```

**Side Effects:**
- Recalculates progress percentage
- Sends LED update with LOW priority

#### GET /api/progress

Get progress statistics.

**Response:**
```json
{
  "total": 10,
  "completed": 7,
  "percentage": 70.0,
  "remaining": 3
}
```

**Calculation:**
```
percentage = (completed / total) * 100
remaining = total - completed
```

#### POST /api/leds/progress

Manually trigger LED progress update.

**Request Body:**
```json
{
  "percentage": 75.5
}
```

**Response:**
```json
{
  "status": "success",
  "message": "LED updated to 75.5%"
}
```

### Error Responses

**400 Bad Request:**
```json
{
  "error": "Invalid request data",
  "details": "Title is required"
}
```

**404 Not Found:**
```json
{
  "error": "Task not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "message": "Database connection failed"
}
```

---

## Hardware Integration

### LED Matrix Setup

#### Hardware Specifications

**64x64 RGB LED Matrix Panel (HUB75E):**
- Matrix Size: 64x64 pixels (4096 RGB LEDs)
- Driver: HUB75E interface
- Communication: Parallel GPIO (13 pins)
- Scan Mode: 1/32 scan
- Voltage: 5V DC (dedicated power supply required)
- Current Draw: 2-4A typical, up to 8A max (all LEDs on white)
- PWM Bits: 11-bit per color channel
- Color Depth: True 24-bit color (16.7M colors)
- Refresh Rate: ~300-500Hz (configurable)
- Library: rpi-rgb-led-matrix (Henner Zeller)
- Compatibility: Raspberry Pi 1-4 (Pi 5 not yet supported)

#### Wiring Connection

**HUB75E Connector Pinout (64x64 RGB Matrix):**

```
HUB75E Pin    →  Raspberry Pi GPIO
─────────────────────────────────────
R1 (Red 1)    →  GPIO 11  (Pin 23)
G1 (Green 1)  →  GPIO 27  (Pin 13)
B1 (Blue 1)   →  GPIO 7   (Pin 26)
R2 (Red 2)    →  GPIO 8   (Pin 24)
G2 (Green 2)  →  GPIO 9   (Pin 21)
B2 (Blue 2)   →  GPIO 10  (Pin 19)
A (Row Addr)  →  GPIO 22  (Pin 15)
B (Row Addr)  →  GPIO 23  (Pin 16)
C (Row Addr)  →  GPIO 24  (Pin 18)
D (Row Addr)  →  GPIO 25  (Pin 22)
E (Row Addr)  →  GPIO 15  (Pin 10)
CLK (Clock)   →  GPIO 17  (Pin 11)
LAT (Latch)   →  GPIO 4   (Pin 7)
OE (Output)   →  GPIO 18  (Pin 12)
GND           →  GND      (Pin 6, 9, 14, 20, 25, 30, 34, 39)
```

**IMPORTANT: Power Supply**
- Do NOT power the matrix from Raspberry Pi!
- Use dedicated 5V power supply (minimum 4A recommended)
- Connect matrix power separately
- Connect GND of Pi and matrix power supply together (common ground)

**Visual Connection Diagram:**
```
     5V Power Supply           Raspberry Pi 4
     (4A+ recommended)          GPIO Header
     ┌──────────┐               ┌─────────┐
     │  +5V  GND│               │ 13 pins │───┐
     └───┬───┬──┘               │ to LED  │   │
         │   │                  │ matrix  │   │
         │   └──────┐           └─────────┘   │
         │          │                         │
         ▼          ▼                         ▼
    ┌────────────────────────────────────────────┐
    │          64x64 RGB LED Matrix              │
    │          (HUB75E connector)                │
    │                                            │
    │  Power: +5V, GND (from power supply)      │
    │  Data:  13 GPIO pins (from Raspberry Pi)  │
    └────────────────────────────────────────────┘
```

**Alternative: Adafruit RGB Matrix HAT/Bonnet**
If using an Adafruit HAT, set in `shared/led_manager/config.py`:
```python
HARDWARE_MAPPING = 'adafruit-hat'  # Instead of 'regular'
```

#### Library Installation

**ONE-COMMAND INSTALLATION:**
```bash
# On Raspberry Pi, run from project root:
bash scripts/install_led_library.sh
```

This script automatically:
- Installs build dependencies (python3-dev, cython3, gcc, etc.)
- Compiles the rpi-rgb-led-matrix C++ library
- Builds and installs Python bindings
- Verifies the installation
- Takes ~5-10 minutes

**Verify Installation:**
```bash
python3 -c "from rgbmatrix import RGBMatrix; print('Installation successful!')"
```

**Manual Installation (if needed):**
```bash
cd external/rpi-rgb-led-matrix
make -C lib clean
make -C lib -j$(nproc)
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

**System Configuration:**
The library uses GPIO pins and hardware timers, which may conflict with:
- **Audio**: Disable onboard audio if experiencing issues
- **Bluetooth**: May cause timing issues on some Pi models
- **Other GPIO users**: Ensure no conflicts with other hardware

Add to `/boot/config.txt` if needed:
```bash
# Disable onboard audio (conflicts with PWM timing)
dtparam=audio=off

# Optional: Increase core frequency for better stability
core_freq=250
```

#### Testing Hardware

**Test LED Matrix:**
```bash
cd ~/focus/shared/led_manager

# Basic test (requires root for GPIO access)
sudo python3 example_usage.py

# Or run as regular user with GPIO permissions
# (see permissions setup below)
python3 example_usage.py
```

**Expected Display Behavior:**
- **Boot animation**: Colorful pattern sequence
- **WiFi symbol (W)**: Large green 'W' scaled to 64x64
- **Progress bars**: Vertical bar filling from bottom to top
  - 0-33%: Green
  - 34-66%: Yellow
  - 67-100%: Red
- **Clear**: All LEDs off

**If Matrix Doesn't Display:**

1. **Check power supply**:
   - Matrix should have dedicated 5V power (4A+ recommended)
   - Check if power LED on matrix is lit
   - Measure voltage at matrix power connector (~5V)

2. **Verify library installation**:
   ```bash
   python3 -c "from rgbmatrix import RGBMatrix; print('OK')"
   ```

3. **Check GPIO permissions**:
   ```bash
   # Add user to gpio group
   sudo usermod -a -G gpio $USER

   # Or run with sudo (not recommended for production)
   sudo python3 example_usage.py
   ```

4. **Verify wiring**:
   - Double-check HUB75E connector pinout
   - Ensure all 13 data pins are connected
   - Verify common ground between Pi and power supply

5. **Try with different gpio_slowdown**:
   Edit `shared/led_manager/config.py`:
   ```python
   GPIO_SLOWDOWN = 2  # Try values: 0, 1, 2, 3, 4
   ```
   Higher values reduce timing issues but may lower refresh rate

6. **Test in mock mode** (no hardware required):
   ```bash
   cd ~/focus/shared/led_manager
   LED_MOCK_MODE=true python3 led_manager_daemon.py
   ```

**Hardware Diagnostics:**
```bash
# Check GPIO group membership
groups $USER
# Should include 'gpio'

# Test basic GPIO access
ls -l /dev/gpiomem
# Should be readable by gpio group

# Monitor CPU usage (RGB matrix uses ~30-40% of one core)
top -p $(pgrep -f led_manager)

# Check for kernel messages (timing issues, etc.)
dmesg | tail -20
```

**Common Issues and Solutions:**

| Issue | Symptom | Solution |
|-------|---------|----------|
| Flickering | Screen flickers or shows artifacts | Increase `gpio_slowdown` to 2 or 3 |
| Dim display | LEDs barely visible | Check power supply, increase `brightness` in config |
| Wrong colors | Colors appear incorrect | Verify RGB pin connections (R1, G1, B1, R2, G2, B2) |
| Half screen | Only top/bottom half works | Check row address pins (A, B, C, D, E) |
| No display | Nothing shows | Check power, wiring, library installation |
| Audio conflict | Error about PWM/audio | Disable onboard audio in `/boot/config.txt` |

### LED Display Protocol

#### Symbols

| Symbol | Character | Display | Usage |
|--------|-----------|---------|-------|
| WiFi | `w` | W shape | WiFi connected |
| Tunnel | `t` | T shape | Ngrok tunnel up |
| Discord | `d` | D shape | Discord bot connected |
| Check | `check` | ✓ shape | Success indicator |
| Error | `error` | X shape | Error indicator |

**Example:**
```python
led.show_symbol('w')  # Shows 'W' on LED matrix
```

#### Animations

| Animation | Description | Priority | Usage |
|-----------|-------------|----------|-------|
| `boot` | Startup sequence | HIGH | Bootmanager startup |
| `wifi_searching` | Scanning effect | HIGH | Connecting to WiFi |
| `idle` | Rotating dot | LOW | Idle state |

**Example:**
```python
led.show_animation('wifi_searching')  # Loops until stopped
led.stop_animation()
```

#### Progress Bar

**Visual Representation:**

```
  0% ────────  12% ████████  25% ████████
                              ████████

 37% ████████  50% ████████  62% ████████
     ████████      ████████      ████████
     ████████      ████████      ████████
                   ████████      ████████
                                 ████████

 75% ████████  87% ████████ 100% ████████
     ████████      ████████      ████████
     ████████      ████████      ████████
     ████████      ████████      ████████
     ████████      ████████      ████████
     ████████      ████████      ████████
                   ████████      ████████
                                 ████████
```

**Calculation:**
```python
percentage = (completed_tasks / total_tasks) * 100
rows_lit = int(percentage / 12.5)  # 8 rows total, 12.5% each
```

**Example:**
```python
led.show_progress(75.0)  # Shows 6 rows lit (75% ÷ 12.5 = 6)
```

#### Priority System

Commands are processed based on priority:

| Priority | Value | Usage |
|----------|-------|-------|
| HIGH | 2 | Boot animations, critical status |
| MEDIUM | 1 | Status symbols (W, T, D) |
| LOW | 0 | Progress updates from server |

**Behavior:**
- HIGH priority commands interrupt LOW priority animations
- Commands of equal priority are processed FIFO (first-in, first-out)
- Server progress updates use LOW priority to not interrupt boot sequence

**Example:**
```python
# During boot:
led.show_animation('boot', priority='HIGH')      # Shows immediately

# Server tries to update:
led.show_progress(50, priority='LOW')            # Queued, waits for boot

# Boot completes:
# Progress update now displays
```

### Hardware Troubleshooting

#### LED Matrix Not Working

**Check SPI:**
```bash
ls /dev/spidev*
# If empty, SPI is not enabled
sudo raspi-config  # Enable in Interface Options
```

**Check Wiring:**
```bash
# Test with multimeter
# VCC should be ~5V
# GND should be 0V
```

**Check Permissions:**
```bash
# Verify user is in correct groups
groups focus
# Should include: spi, gpio, dialout

# Add if missing:
sudo usermod -a -G spi,gpio focus
```

**Test with Mock Mode:**
```bash
cd ~/focus/shared/led_manager
LED_MOCK_MODE=true python led_manager_daemon.py

# In another terminal:
python example_usage.py
# Should print to console instead of LED
```

#### Partial Display Issues

**Symptom:** Only some LEDs light up

**Causes:**
1. Insufficient power supply (need 5V, 3A)
2. Loose wiring connections
3. Faulty LED module

**Solutions:**
```bash
# Check power supply voltage
# Test with fewer LEDs:
python -c "
from led_hardware import LEDHardware
led = LEDHardware()
led.display_matrix([[1,0,0,0,0,0,0,0]] * 8)  # Single column
"
```

#### Socket Connection Issues

**Symptom:** `Connection refused` errors

**Causes:**
1. LED Manager daemon not running
2. Socket file doesn't exist
3. Permission issues

**Solutions:**
```bash
# Check daemon status
sudo systemctl status led-manager

# Check socket exists
ls -l /var/run/led-manager/led-manager.sock

# Check permissions
sudo chmod 666 /var/run/led-manager/led-manager.sock

# Restart daemon
sudo systemctl restart led-manager
```

---

## Deployment

### System Requirements

**Hardware:**
- Raspberry Pi 4 (2GB+ RAM recommended)
- MAX7219 8x8 LED Matrix
- SD Card: 16GB minimum, 32GB recommended
- Power Supply: 5V, 3A (official Raspberry Pi PSU recommended)

**Software:**
- Raspberry Pi OS (64-bit recommended)
- Python 3.11+
- Node.js 18+
- 500MB free disk space for dependencies

### Service Architecture

```
System Boot
    ↓
led-manager.service starts
    ↓ (depends on)
bootmanager.service starts
    ↓ (manages)
├─ WiFi Connection
├─ SSH Tunnel (ngrok-ssh.service)
├─ Server Process (Flask on port 5001)
├─ Frontend Process (Next.js on port 3000)
├─ HTTP Tunnel (ngrok process)
└─ Discord Bot
    ↓ (configures)
nginx.service
    ↓
System Ready
```

### Systemd Services

#### Service Files Location

```
/etc/systemd/system/
├── led-manager.service       # LED daemon
├── bootmanager.service        # Boot orchestrator
└── ngrok-ssh.service          # SSH tunnel
```

#### Service Management Commands

```bash
# Start services
sudo systemctl start led-manager
sudo systemctl start bootmanager

# Stop services
sudo systemctl stop bootmanager
sudo systemctl stop led-manager

# Restart services
sudo systemctl restart bootmanager

# Enable on boot
sudo systemctl enable led-manager
sudo systemctl enable bootmanager

# Disable on boot
sudo systemctl disable bootmanager

# Check status
sudo systemctl status led-manager
sudo systemctl status bootmanager

# View logs
journalctl -u led-manager -f
journalctl -u bootmanager -f
journalctl -u bootmanager --since "10 minutes ago"
```

### Nginx Deployment

**Configuration:** `/etc/nginx/sites-available/focus`

The bootmanager generates this from the template at startup.

**Enable Site:**
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/focus /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

**Logs:**
```bash
# Access log
tail -f /var/log/nginx/access.log

# Error log
tail -f /var/log/nginx/error.log
```

### Process Management

The bootmanager manages server and frontend as background processes.

**View Processes:**
```bash
# Via Discord bot:
/jobs

# Manually:
ps aux | grep python | grep run.py     # Server
ps aux | grep node | grep next          # Frontend
```

**Restart Processes (via Discord):**
```
/restart server
/restart frontend
```

**View Process Logs (via Discord):**
```
/tail server 50
/tail frontend 50
```

### Remote Access

#### SSH Tunnel

Managed by `ngrok-ssh.service`.

**Get SSH URL:**
```bash
# Via Discord: Check boot notification message

# Manually:
systemctl status ngrok-ssh | grep "url="
# Output: url=tcp://0.tcp.ngrok.io:12345

# Connect:
ssh -p 12345 focus@0.tcp.ngrok.io
```

#### HTTP Tunnel

Managed by bootmanager.

**Get HTTP URL:**
```bash
# Via Discord: Check boot notification message

# Manually:
journalctl -u bootmanager | grep "HTTP Tunnel" | tail -1
# Output: HTTP Tunnel: https://abc123.ngrok.io
```

**Access:**
```
URL: https://abc123.ngrok.io
Username: admin (or your NGROK_HTTP_USERNAME)
Password: [your NGROK_HTTP_PASSWORD]
```

### Backup & Restore

#### Backup Database

```bash
# Backup SQLite database
cd ~/focus/server
cp tasks.db tasks.db.backup.$(date +%Y%m%d_%H%M%S)

# Automated backup script
cat > ~/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
cp ~/focus/server/tasks.db $BACKUP_DIR/tasks.db.$(date +%Y%m%d_%H%M%S)
# Keep only last 7 backups
ls -t $BACKUP_DIR/tasks.db.* | tail -n +8 | xargs rm -f
EOF

chmod +x ~/backup_db.sh

# Run daily via cron
crontab -e
# Add: 0 2 * * * /home/focus/backup_db.sh
```

#### Restore Database

```bash
cd ~/focus/server
# Stop server first
sudo systemctl stop bootmanager

# Restore
cp tasks.db.backup.20251101_120000 tasks.db

# Start server
sudo systemctl start bootmanager
```

#### Backup Configuration

```bash
# Backup secrets
cp ~/.config/focus/secrets.env ~/.config/focus/secrets.env.backup

# Backup entire config directory
tar czf ~/config_backup_$(date +%Y%m%d).tar.gz ~/.config/focus/
```

### Updates

#### Update Code

```bash
cd ~/focus
git pull origin main

# Restart services
sudo systemctl restart bootmanager
sudo systemctl restart led-manager
```

#### Update Dependencies

**Python (Server, Bootmanager, LED Manager):**
```bash
# Server
cd ~/focus/server
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate

# Bootmanager
cd ~/focus/bootmanager
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate

# LED Manager
cd ~/focus/shared/led_manager
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate

# Restart
sudo systemctl restart bootmanager led-manager
```

**Frontend:**
```bash
cd ~/focus/frontend
npm install
npm run build

# Restart
sudo systemctl restart bootmanager
```

### Production Checklist

Before deploying to production:

- [ ] Update `secrets.env` with secure passwords
- [ ] Enable SPI interface
- [ ] Test LED matrix wiring
- [ ] Verify WiFi credentials
- [ ] Test Discord bot connection
- [ ] Test ngrok tunnels (SSH and HTTP)
- [ ] Verify nginx configuration
- [ ] Check systemd services are enabled
- [ ] Test automatic restart on failure
- [ ] Verify database backups are working
- [ ] Test remote access via Discord
- [ ] Check all ports are not exposed (only nginx on 80)
- [ ] Verify basic auth on HTTP tunnel
- [ ] Test full boot sequence
- [ ] Monitor logs for errors

---

## Troubleshooting

### Common Issues

#### LED Manager Issues

**Problem:** LED Manager won't start

**Check:**
```bash
sudo systemctl status led-manager
journalctl -u led-manager -n 50
```

**Common Causes:**
1. SPI not enabled
2. Permission issues with `/var/run/led-manager/`
3. Python dependencies missing

**Solutions:**
```bash
# Enable SPI
sudo raspi-config  # Interface Options > SPI

# Fix permissions
sudo mkdir -p /var/run/led-manager
sudo chown focus:focus /var/run/led-manager

# Reinstall dependencies
cd ~/focus/shared/led_manager
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

---

**Problem:** Socket connection refused

**Check:**
```bash
ls -l /var/run/led-manager/led-manager.sock
```

**Solutions:**
```bash
# Restart daemon
sudo systemctl restart led-manager

# Check if socket exists
test -S /var/run/led-manager/led-manager.sock && echo "Socket exists" || echo "Socket missing"

# If socket missing, daemon is not running properly
journalctl -u led-manager -n 100
```

---

#### Bootmanager Issues

**Problem:** Bootmanager fails to start

**Check:**
```bash
sudo systemctl status bootmanager
journalctl -u bootmanager -n 100
```

**Common Causes:**
1. LED Manager not running (dependency)
2. Missing secrets.env file
3. Invalid Discord token

**Solutions:**
```bash
# Ensure LED Manager is running
sudo systemctl start led-manager

# Verify secrets file exists
ls ~/.config/focus/secrets.env

# Test Discord token manually
cd ~/focus/bootmanager
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser('~/.config/focus/secrets.env'))
print('Token:', os.getenv('DISCORD_BOT_TOKEN')[:20] + '...')
"
```

---

**Problem:** WiFi won't connect

**Check:**
```bash
nmcli device wifi list
nmcli connection show
```

**Solutions:**
```bash
# Test connection manually
nmcli device wifi connect "YourSSID" password "YourPassword"

# Verify secrets.env has correct SSID and password
cat ~/.config/focus/secrets.env | grep WIFI

# Check WiFi is enabled
rfkill list
# If blocked: rfkill unblock wifi
```

---

#### Server Issues

**Problem:** Server won't start

**Check:**
```bash
# If bootmanager is managing it:
journalctl -u bootmanager | grep "server"

# Test manually:
cd ~/focus/server
source venv/bin/activate
python run.py
```

**Common Causes:**
1. Port 5001 already in use
2. Database file permissions
3. Missing dependencies

**Solutions:**
```bash
# Check port
sudo netstat -tulpn | grep 5001
# If occupied: kill <PID>

# Fix database permissions
cd ~/focus/server
chmod 644 tasks.db
chown focus:focus tasks.db

# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

---

**Problem:** Database errors

**Check:**
```bash
cd ~/focus/server
sqlite3 tasks.db ".schema"
```

**Solutions:**
```bash
# Backup first
cp tasks.db tasks.db.backup

# Recreate database
rm tasks.db
python -c "
from app import create_app
from app.config import ProductionConfig
from app.extensions import db
app = create_app(ProductionConfig)
with app.app_context():
    db.create_all()
"

# If needed, restore backup
cp tasks.db.backup tasks.db
```

---

#### Frontend Issues

**Problem:** Frontend won't start

**Check:**
```bash
# If bootmanager is managing it:
journalctl -u bootmanager | grep "frontend"

# Test manually:
cd ~/focus/frontend
npm run dev
```

**Common Causes:**
1. Port 3000 already in use
2. Node modules missing
3. Build errors

**Solutions:**
```bash
# Check port
sudo netstat -tulpn | grep 3000

# Reinstall dependencies
cd ~/focus/frontend
rm -rf node_modules package-lock.json
npm install

# Build
npm run build
npm run start
```

---

**Problem:** API requests fail (404 or CORS errors)

**Check:**
```bash
# Test direct API
curl http://localhost:5001/health

# Test through nginx
curl http://localhost/api/health
```

**Solutions:**
```bash
# Verify nginx config
sudo nginx -t

# Check nginx is routing correctly
cat /etc/nginx/sites-available/focus | grep "proxy_pass"

# Reload nginx
sudo systemctl reload nginx
```

---

#### Tunnel Issues

**Problem:** Ngrok tunnels won't start

**Check:**
```bash
# SSH tunnel
systemctl status ngrok-ssh

# HTTP tunnel
journalctl -u bootmanager | grep -i tunnel
```

**Common Causes:**
1. Invalid ngrok auth token
2. Network connectivity issues
3. Ngrok not installed

**Solutions:**
```bash
# Test ngrok manually
ngrok config check
ngrok config view

# Re-add auth token
ngrok authtoken YOUR_TOKEN_HERE

# Test HTTP tunnel manually
ngrok http 80 --authtoken=YOUR_TOKEN --basic-auth="admin:password"
```

---

**Problem:** Cannot access via ngrok URL

**Check:**
```bash
# Test locally first
curl http://localhost/api/health

# Check ngrok dashboard
# https://dashboard.ngrok.com/endpoints/status
```

**Solutions:**
```bash
# Verify tunnel is up
journalctl -u bootmanager | grep "HTTP Tunnel" | tail -1

# Test with basic auth
curl -u admin:password https://YOUR_NGROK_URL.ngrok.io/api/health

# Check nginx is listening
sudo netstat -tulpn | grep :80
```

---

#### Discord Bot Issues

**Problem:** Discord bot won't connect

**Check:**
```bash
journalctl -u bootmanager | grep -i discord
```

**Common Causes:**
1. Invalid bot token
2. Bot not invited to server
3. Network issues

**Solutions:**
```bash
# Verify token is valid
# Go to: https://discord.com/developers/applications
# Check bot token hasn't been regenerated

# Ensure bot has required intents
# Dashboard > Bot > Privileged Gateway Intents
# Enable: Message Content Intent

# Re-invite bot to server
# Dashboard > OAuth2 > URL Generator
# Scopes: bot
# Permissions: Send Messages, Read Message History
```

---

**Problem:** Discord commands not working

**Check:**
```bash
# Bot should log command usage
journalctl -u bootmanager | grep "Command"
```

**Solutions:**
```bash
# Verify channel ID is correct
echo $DISCORD_CHANNEL_ID

# Test bot can send messages
# Send a test message in Discord
# Bot should respond to /status
```

---

### Logs and Diagnostics

#### System Logs

```bash
# LED Manager
journalctl -u led-manager -f
journalctl -u led-manager --since "1 hour ago"
journalctl -u led-manager -p err  # Errors only

# Bootmanager
journalctl -u bootmanager -f
journalctl -u bootmanager --since "today"
journalctl -u bootmanager -p warning

# All services
journalctl -xe

# Clear old logs
sudo journalctl --vacuum-time=7d  # Keep last 7 days
```

#### Application Logs

```bash
# LED Manager
tail -f /var/log/led-manager.log

# Bootmanager
tail -f /var/log/bootmanager.log

# Nginx access
tail -f /var/log/nginx/access.log

# Nginx errors
tail -f /var/log/nginx/error.log
```

#### Process Diagnostics

```bash
# Check all Focus processes
ps aux | grep -E "(python.*focus|node.*next)"

# Check ports
sudo netstat -tulpn | grep -E "(5001|3000|80)"

# Check CPU and memory
htop
# Filter: F4, type "focus"

# Check disk space
df -h
du -sh ~/focus/*
```

#### Network Diagnostics

```bash
# Check WiFi connection
nmcli device status
nmcli connection show --active

# Check internet connectivity
ping -c 4 8.8.8.8

# Check DNS
nslookup google.com

# Check ngrok connectivity
curl https://ngrok.com

# Check firewall (if enabled)
sudo iptables -L
```

#### Hardware Diagnostics

```bash
# Check SPI
ls -l /dev/spidev*
lsmod | grep spi

# Check LED connection (GPIO voltage)
gpio readall  # If wiringpi installed

# Test LED without daemon
cd ~/focus/shared/led_manager
source venv/bin/activate
python -c "
from led_hardware import LEDHardware
led = LEDHardware()
led.display_matrix([[1]*8] * 8)  # All LEDs on
"
```

---

## Development Guide

### Local Development

#### Server Development

```bash
cd ~/focus/server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run in debug mode
python -c "
from app import create_app
from app.config import Config
app = create_app(Config)
app.run(debug=True, host='0.0.0.0', port=5001)
"
```

**Hot Reload:** Flask debug mode auto-reloads on code changes.

#### Frontend Development

```bash
cd ~/focus/frontend
npm install
npm run dev
```

**Hot Reload:** Next.js dev server auto-reloads on changes.
**Access:** http://localhost:3000

#### LED Manager Development (Mock Mode)

```bash
cd ~/focus/shared/led_manager
source venv/bin/activate

# Run in mock mode (no hardware)
LED_MOCK_MODE=true python led_manager_daemon.py

# Test in another terminal
python example_usage.py
```

### Project Structure

```
focus/
├── server/                  # Flask backend
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   └── config.py        # Configuration
│   └── run.py               # Entry point
│
├── frontend/                # Next.js frontend
│   ├── app/                 # Pages (App Router)
│   ├── components/          # React components
│   ├── lib/
│   │   ├── api/             # API client
│   │   └── types/           # TypeScript types
│   └── public/              # Static assets
│
├── bootmanager/             # Boot orchestrator
│   ├── src/
│   │   ├── network/         # WiFi & tunnels
│   │   ├── services/        # Process management
│   │   ├── discord/         # Discord bot
│   │   └── main.py          # Boot sequence
│   └── config/              # Templates
│
├── shared/
│   └── led_manager/         # LED daemon
│       ├── led_manager_daemon.py
│       ├── led_manager_client.py
│       ├── led_hardware.py
│       ├── led_animations.py
│       └── led_protocol.py
│
└── install.sh               # Automated installer
```

### Adding Features

#### Add New API Endpoint

1. **Define route** in `server/app/routes/`:
```python
# server/app/routes/my_feature.py
from flask import Blueprint, jsonify

bp = Blueprint('my_feature', __name__)

@bp.route('/api/my-feature', methods=['GET'])
def get_my_feature():
    return jsonify({"message": "Hello"})
```

2. **Register blueprint** in `server/app/__init__.py`:
```python
from app.routes import my_feature
app.register_blueprint(my_feature.bp)
```

3. **Update frontend API client** in `frontend/lib/api/`:
```typescript
// frontend/lib/api/my-feature.ts
export const fetchMyFeature = async () => {
  const response = await apiClient.get('/my-feature');
  return response.data;
};
```

4. **Use in component**:
```typescript
const { data } = useQuery({
  queryKey: ['myFeature'],
  queryFn: fetchMyFeature
});
```

#### Add New LED Animation

1. **Define animation** in `shared/led_manager/led_animations.py`:
```python
ANIMATIONS = {
    'my_animation': [
        [[1,0,0,0,0,0,0,1],  # Frame 1
         ...],
        [[0,1,0,0,0,0,1,0],  # Frame 2
         ...]
    ]
}
```

2. **Use from client**:
```python
led.show_animation('my_animation')
```

#### Add Discord Bot Command

1. **Define command** in `bootmanager/src/discord/commands.py`:
```python
@bot.command(name='mycommand')
async def my_command(ctx):
    await ctx.send("Command executed!")
```

2. **Use in Discord**:
```
/mycommand
```

### Testing

#### Manual Testing

**Server:**
```bash
# Health check
curl http://localhost:5001/health

# Create task
curl -X POST http://localhost:5001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Test task","description":"Testing"}'

# List tasks
curl http://localhost:5001/api/tasks
```

**LED Manager:**
```bash
cd ~/focus/shared/led_manager
python example_usage.py
```

**Full System:**
```bash
# Restart everything
sudo systemctl restart led-manager bootmanager

# Check status
sudo systemctl status led-manager bootmanager

# Monitor logs
journalctl -u bootmanager -f
```

### Best Practices

1. **Always test with mock mode first** before connecting hardware
2. **Use virtual environments** for Python projects
3. **Keep secrets.env secure** (never commit to git)
4. **Backup database** before schema changes
5. **Test boot sequence** after configuration changes
6. **Monitor logs** during development
7. **Use Discord bot** for remote testing
8. **Document new features** in this file

---

## Appendix

### File Locations Summary

| Component | Location |
|-----------|----------|
| Server | `/home/focus/focus/server/` |
| Frontend | `/home/focus/focus/frontend/` |
| Bootmanager | `/home/focus/focus/bootmanager/` |
| LED Manager | `/home/focus/focus/shared/led_manager/` |
| Secrets | `~/.config/focus/secrets.env` |
| Nginx Config | `/etc/nginx/sites-available/focus` |
| Systemd Services | `/etc/systemd/system/` |
| Logs | `/var/log/` and `journalctl` |
| LED Socket | `/var/run/led-manager/led-manager.sock` |

### Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js development/production |
| Server | 5001 | Flask API |
| Nginx | 80 | Reverse proxy |
| Ngrok HTTP | Random | Public tunnel |
| Ngrok SSH | Random | SSH tunnel |

### External Services

| Service | Purpose | URL |
|---------|---------|-----|
| Discord | Bot control | https://discord.com/developers/applications |
| Ngrok | Tunneling | https://dashboard.ngrok.com |
| GitHub | Code repository | (your repository URL) |

### Useful Commands

```bash
# Quick status check
systemctl status led-manager bootmanager nginx

# View all logs
journalctl -u led-manager -u bootmanager -f

# Restart everything
sudo systemctl restart led-manager && sudo systemctl restart bootmanager

# Update and restart
cd ~/focus && git pull && sudo systemctl restart bootmanager

# Backup database
cp ~/focus/server/tasks.db ~/tasks.db.backup.$(date +%Y%m%d)

# Check disk space
df -h && du -sh ~/focus/*

# Monitor system
htop
```

---

**Documentation Version:** 1.0
**Last Updated:** 2025-11-01
**Maintained by:** Focus Development Team

For issues or questions, please refer to the [Troubleshooting](#troubleshooting) section or check the logs using `journalctl`.
