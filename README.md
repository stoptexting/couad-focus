# F.O.C.U.S. MOMENTUM

**Physical Task Management with LED Progress Visualization**

A Raspberry Pi 4-based task management system that combines a modern web interface with real-time progress visualization on a 64x64 RGB LED matrix. Sync with Taiga, control via Discord, access anywhere via Ngrok tunnels.

![Version](https://img.shields.io/badge/version-1.0.1-blue)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204-red)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [LED Display Layouts](#led-display-layouts)
- [Hardware Setup](#hardware-setup)
- [Systemd Services](#systemd-services)
- [Discord Bot Commands](#discord-bot-commands)
- [Taiga Integration](#taiga-integration)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

F.O.C.U.S. MOMENTUM provides tangible, physical feedback for project progress through a 64x64 RGB LED matrix display. The system supports hierarchical task management (Projects → Sprints → User Stories → Tasks) with automatic LED updates as tasks are completed.

### Key Capabilities

- **Web Dashboard**: Modern Next.js interface with neobrutalist design
- **LED Visualization**: Real-time progress display on 64x64 RGB matrix
- **Remote Access**: Ngrok tunneling for anywhere access
- **Discord Control**: Bot commands for remote system management
- **Taiga Sync**: Bidirectional integration with Taiga project management

---

## Features

| Feature | Description |
|---------|-------------|
| **Hierarchical Tasks** | Project → Sprint → User Story → Task structure |
| **LED Progress** | 4 display layouts (single, sprint, user story, cycling) |
| **Real-time Sync** | Automatic LED updates on task completion |
| **Taiga Integration** | Webhook-based sync with Taiga PM tool |
| **Discord Bot** | Remote control via Discord commands |
| **Auto-boot** | Automatic service startup on Raspberry Pi |
| **WiFi Management** | Auto-connect to configured hotspot |
| **Tunnel Access** | Ngrok SSH and HTTP tunnels for remote access |
| **Neobrutalist UI** | Sharp corners, bold typography, hard shadows |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL ACCESS                               │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────────┐    │
│  │ Taiga Server │    │ Discord API  │    │ Ngrok (SSH & HTTP)     │    │
│  └──────┬───────┘    └──────┬───────┘    └───────────┬────────────┘    │
└─────────┼───────────────────┼────────────────────────┼─────────────────┘
          │                   │                        │
          ▼                   ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      RASPBERRY PI 4                                     │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                     BOOTMANAGER                                    │ │
│  │  • WiFi Connection  • Ngrok Tunnels  • Discord Bot  • Services    │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                │                                        │
│  ┌─────────────────────────────┼─────────────────────────────────────┐ │
│  │                    NGINX (Port 80)                                 │ │
│  │           /  → Frontend    /api/* → Backend                       │ │
│  └─────────────┬─────────────────────────────┬───────────────────────┘ │
│                │                             │                          │
│  ┌─────────────▼─────────────┐  ┌────────────▼────────────────────┐   │
│  │     FRONTEND (3000)       │  │      BACKEND (5001)             │   │
│  │                           │  │                                  │   │
│  │  Next.js 16 + React 19    │  │  Flask 3.0 + SQLAlchemy         │   │
│  │  TypeScript + Tailwind    │  │  SQLite Database                │   │
│  │  React Query polling      │  │  Taiga Sync Service             │   │
│  │  Neobrutalist UI          │  │  LED Service                    │   │
│  └───────────────────────────┘  └──────────────┬──────────────────┘   │
│                                                 │                       │
│                           Unix Socket IPC       │                       │
│                    /tmp/led-manager.sock        │                       │
│                                                 ▼                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    LED MANAGER DAEMON                             │  │
│  │                                                                   │  │
│  │  • Priority Queue (HIGH/MEDIUM/LOW)                              │  │
│  │  • Exclusive Hardware Access                                      │  │
│  │  • JSON Protocol over Unix Socket                                │  │
│  └──────────────────────────────┬───────────────────────────────────┘  │
│                                 │ SPI Interface                        │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              64x64 RGB LED MATRIX (HUB75E)                       │  │
│  │                     4096 LEDs • Full Color                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Action** → Frontend React component
2. **API Call** → Flask backend `/api/*` endpoint
3. **Database Update** → SQLite via SQLAlchemy
4. **Progress Calculation** → Automatic percentage computation
5. **LED Update** → Unix socket command to LED daemon
6. **Hardware Display** → RGB matrix shows updated progress

---

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Frontend** | Next.js, React, TypeScript | 16.0.0, 19.2.0 |
| **Styling** | Tailwind CSS, shadcn/ui | 3.4.18 |
| **State** | TanStack React Query | 5.90.5 |
| **Backend** | Flask, SQLAlchemy | 3.0.0, 3.1.0 |
| **Database** | SQLite | 3.x |
| **LED Daemon** | Python, Unix Sockets | 3.11+ |
| **LED Library** | rpi-rgb-led-matrix | Latest |
| **Discord** | discord.py | 2.3.0+ |
| **Tunneling** | Ngrok | Latest |
| **Proxy** | Nginx | 1.x |

---

## Project Structure

```
focus/
├── frontend/                    # Next.js web application
│   ├── app/                     # App Router pages
│   │   ├── page.tsx            # Home (redirects to /taiga)
│   │   ├── taiga/              # Main task management UI
│   │   ├── gauges/             # LED gauge visualization
│   │   └── settings/           # Admin settings
│   ├── components/             # React components
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── gauges/             # Gauge display components
│   │   └── modals/             # Form modals
│   ├── lib/                    # Utilities and API
│   │   ├── api/                # API client modules
│   │   └── types.ts            # TypeScript interfaces
│   └── hooks/                  # Custom React hooks
│
├── server/                      # Flask REST API
│   ├── app/
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── project.py
│   │   │   ├── sprint.py
│   │   │   ├── user_story.py
│   │   │   ├── task.py
│   │   │   └── taiga_config.py # Taiga integration config
│   │   ├── routes/             # API endpoints
│   │   │   ├── projects.py
│   │   │   ├── sprints.py
│   │   │   ├── tasks.py
│   │   │   ├── gauges.py
│   │   │   └── taiga.py        # Taiga integration
│   │   └── services/           # Business logic
│   │       ├── led_service.py
│   │       ├── taiga_client.py
│   │       └── taiga_sync_service.py
│   ├── config.json             # LED zone configuration
│   ├── run.py                  # Entry point
│   └── requirements.txt
│
├── bootmanager/                 # System orchestration
│   ├── src/
│   │   ├── main.py             # Boot sequence (11 steps)
│   │   ├── config.py           # Configuration loader
│   │   ├── network/
│   │   │   ├── wifi_manager.py
│   │   │   └── tunnel_manager.py
│   │   ├── discord/
│   │   │   ├── bot.py
│   │   │   ├── commands.py
│   │   │   └── job_manager.py
│   │   └── services/
│   │       └── service_manager.py
│   ├── systemd/                # Service files
│   └── requirements.txt
│
└── shared/                      # Shared libraries
    └── led_manager/            # LED daemon
        ├── led_manager_daemon.py
        ├── led_manager_client.py
        ├── led_hardware.py
        ├── led_layout_renderer.py
        └── led_protocol.py
```

---

## Quick Start

### Prerequisites

- Raspberry Pi 4 (2GB+ RAM)
- 64x64 RGB LED Matrix (HUB75E interface)
- Raspberry Pi OS Lite (Debian 12 Bookworm)
- Python 3.11+
- Node.js 18+

### 4-Step Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/focus.git
cd focus

# 2. Run installation script
sudo bash install.sh

# 3. Configure credentials
mkdir -p ~/.config/bootmanager
cp bootmanager/config/secret.env.example ~/.config/bootmanager/secrets.env
nano ~/.config/bootmanager/secrets.env  # Fill in your credentials

# 4. Reboot to start services
sudo reboot
```

---

## Installation

### System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    nodejs npm \
    nginx \
    network-manager \
    git

# Enable SPI for LED matrix
sudo raspi-config nonint do_spi 0
```

### LED Matrix Library

```bash
# Install build tools
sudo apt install -y gcc g++ make cython3 python3-pillow

# Clone and build rpi-rgb-led-matrix
cd /home/focus
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git external/rpi-rgb-led-matrix
cd external/rpi-rgb-led-matrix
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

### Backend Setup

```bash
cd /home/focus/focus/server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Frontend Setup

```bash
cd /home/focus/focus/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### Bootmanager Setup

```bash
cd /home/focus/focus/bootmanager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Install Systemd Services

```bash
# Copy service files
sudo cp shared/led_manager/systemd/led-manager.service /etc/systemd/system/
sudo cp bootmanager/systemd/bootmanager.service /etc/systemd/system/
sudo cp server/systemd/focus-server.service /etc/systemd/system/

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable led-manager bootmanager focus-server

# Start services
sudo systemctl start led-manager bootmanager focus-server
```

---

## Configuration

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `secrets.env` | `~/.config/bootmanager/` | Credentials (Discord, Ngrok, WiFi) |
| `config.json` | `server/` | LED zone configuration |
| `.env` | `server/` | Flask environment |
| `.env.local` | `frontend/` | Frontend API URL |

### secrets.env (Required)

```bash
# Discord Bot
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=123456789012345678

# Ngrok
NGROK_AUTH_TOKEN=your_ngrok_token
NGROK_HTTP_USERNAME=admin
NGROK_HTTP_PASSWORD=secure_password

# WiFi
WIFI_SSID=YourNetworkName
WIFI_PASSWORD=YourPassword

# Optional: Service Paths
SERVER_PATH=/home/focus/focus/server
FRONTEND_PATH=/home/focus/focus/frontend
SERVER_PORT=5001
FRONTEND_PORT=3000
FRONTEND_DEV_MODE=false

# Optional: Retry Settings
WIFI_RETRY_ATTEMPTS=10
WIFI_RETRY_DELAY=5
```

### server/.env

```bash
FLASK_ENV=development
DATABASE_URI=sqlite:///instance/database.db
LED_SOCKET_PATH=/tmp/led-manager.sock
```

### server/config.json (LED Zones)

```json
{
  "hardware": {
    "led_zones": [
      {
        "id": "zone-1",
        "name": "Sprint 1",
        "start_led": 0,
        "end_led": 31,
        "default_color": [0, 255, 0]
      },
      {
        "id": "zone-2",
        "name": "Sprint 2",
        "start_led": 32,
        "end_led": 63,
        "default_color": [0, 255, 0]
      }
    ],
    "total_leds": 64,
    "matrix_width": 64,
    "matrix_height": 64
  },
  "defaults": {
    "primary_zone": "zone-1",
    "fallback_to_single": true
  }
}
```

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | - | Discord bot authentication token |
| `DISCORD_CHANNEL_ID` | - | Target Discord channel for commands |
| `NGROK_AUTH_TOKEN` | - | Ngrok authentication token |
| `NGROK_HTTP_USERNAME` | - | Basic auth username for HTTP tunnel |
| `NGROK_HTTP_PASSWORD` | - | Basic auth password for HTTP tunnel |
| `WIFI_SSID` | - | WiFi network name |
| `WIFI_PASSWORD` | - | WiFi password |
| `SERVER_PORT` | `5001` | Flask server port |
| `FRONTEND_PORT` | `3000` | Next.js frontend port |
| `FRONTEND_DEV_MODE` | `false` | Run frontend in dev mode |
| `LED_SOCKET_PATH` | `/tmp/led-manager.sock` | LED daemon socket path |
| `LED_MOCK_MODE` | `false` | Run LED daemon without hardware |

---

## API Reference

### Base URL

```
http://localhost:5001/api
```

Via Nginx: `http://<pi-ip>/api`

### Projects

#### List Projects
```http
GET /api/projects
```

**Response:**
```json
[
  {
    "id": "uuid-here",
    "name": "My Project",
    "description": "Project description",
    "preferred_layout": "single",
    "preferred_sprint_index": 0,
    "sprints": [...],
    "progress": {
      "percentage": 75,
      "completed_sprints": 3,
      "total_sprints": 4
    }
  }
]
```

#### Get Project with Full Tree
```http
GET /api/projects/:id
```

**Response:** Project with nested sprints → user stories → tasks

#### Create Project
```http
POST /api/projects
Content-Type: application/json

{
  "name": "New Project",
  "description": "Optional description"
}
```

#### Update Project
```http
PUT /api/projects/:id
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

#### Delete Project
```http
DELETE /api/projects/:id
```

#### Set Preferred Layout
```http
PUT /api/projects/:id/preferred-layout
Content-Type: application/json

{
  "layout": "sprint_view"
}
```

**Valid layouts:** `single`, `sprint_view`, `user_story_layout`

### Sprints

#### List Sprints
```http
GET /api/projects/:project_id/sprints
```

#### Create Sprint
```http
POST /api/projects/:project_id/sprints
Content-Type: application/json

{
  "name": "Sprint 1",
  "start_date": "2025-01-01",
  "end_date": "2025-01-14",
  "status": "planned"
}
```

**Valid statuses:** `planned`, `active`, `completed`

#### Update Sprint
```http
PUT /api/sprints/:id
Content-Type: application/json

{
  "name": "Sprint 1 - Updated",
  "status": "active"
}
```

#### Delete Sprint
```http
DELETE /api/sprints/:id
```

### User Stories

#### List User Stories
```http
GET /api/sprints/:sprint_id/user-stories
```

#### Create User Story
```http
POST /api/sprints/:sprint_id/user-stories
Content-Type: application/json

{
  "title": "As a user, I want to...",
  "description": "Acceptance criteria...",
  "priority": "P1",
  "status": "new"
}
```

**Valid priorities:** `P0`, `P1`, `P2`
**Valid statuses:** `new`, `in_progress`, `completed`

#### Update User Story
```http
PUT /api/user-stories/:id
Content-Type: application/json

{
  "title": "Updated title",
  "status": "in_progress"
}
```

#### Delete User Story
```http
DELETE /api/user-stories/:id
```

### Tasks

#### List Tasks
```http
GET /api/user-stories/:user_story_id/tasks
```

#### Create Task
```http
POST /api/user-stories/:user_story_id/tasks
Content-Type: application/json

{
  "title": "Implement feature X",
  "description": "Details..."
}
```

#### Update Task
```http
PUT /api/tasks/:id
Content-Type: application/json

{
  "title": "Updated task",
  "status": "completed"
}
```

**Valid statuses:** `new`, `completed`

#### Delete Task
```http
DELETE /api/tasks/:id
```

### LED Control

#### Get Gauge Data
```http
GET /api/projects/:id/gauges/:layout_type
```

**Layout types:** `single`, `sprint_view`, `user_story_layout`

**Response:**
```json
{
  "layout_type": "sprint_view",
  "project": {
    "name": "My Project",
    "progress": {"percentage": 75}
  },
  "sprints": [
    {"name": "Sprint 1", "progress": {"percentage": 100}},
    {"name": "Sprint 2", "progress": {"percentage": 50}}
  ]
}
```

#### Sync LED Matrix
```http
POST /api/projects/:id/sync-led-matrix/:layout_type
```

Triggers immediate LED update with specified layout.

#### Manual LED Update
```http
POST /api/leds/update
Content-Type: application/json

{
  "percentage": 75
}
```

### Taiga Integration

#### Login
```http
POST /api/taiga/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password",
  "auto_login": true
}
```

#### Set Project
```http
POST /api/taiga/project
Content-Type: application/json

{
  "project_url": "https://taiga.example.com/project/my-project"
}
```

#### Sync
```http
POST /api/taiga/sync
```

#### Get Tree
```http
GET /api/taiga/tree
```

Returns full project tree synced from Taiga.

#### Webhook (for Taiga to call)
```http
POST /api/taiga/webhook
X-Taiga-Webhook-Signature: <hmac-signature>
Content-Type: application/json

{
  "action": "change",
  "type": "task",
  "data": {...}
}
```

#### Get Version (for cache invalidation)
```http
GET /api/taiga/version
```

**Response:**
```json
{
  "version": 42,
  "last_webhook_at": "2025-01-15T10:30:00Z"
}
```

### Admin

#### Reset Database
```http
POST /api/admin/reset-database
```

Clears all project data (keeps Taiga auth config).

### Health Check
```http
GET /health
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## LED Display Layouts

### Single View
Project name with horizontal progress gauge.

```
┌────────────────────────────────────────────────────────────────┐
│  MY PROJECT                                                    │  ← Project name
│                                                                │
│  ████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░  │  ← Horizontal gauge
│                                                                │
│                        75%                                     │  ← Percentage
│                                                                │
│                    Sprint: 2                                   │  ← Current sprint
│                                                                │
│                     US: 8/12                                   │  ← Stories completed
└────────────────────────────────────────────────────────────────┘
```

### Sprint View
Project bar with 3 vertical sprint bars.

```
┌────────────────────────────────────────────────────────────────┐
│  ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░  75%        │  ← Project progress
│                                                                │
│     S1           S2           S3                               │  ← Sprint labels
│  ┌──────┐     ┌──────┐     ┌──────┐                           │
│  │██████│     │██████│     │██████│                           │
│  │██████│     │██████│     │██████│                           │
│  │██████│     │██████│     │░░░░░░│                           │
│  │██████│     │░░░░░░│     │░░░░░░│                           │
│  │░░░░░░│     │░░░░░░│     │░░░░░░│                           │
│  └──────┘     └──────┘     └──────┘                           │
│    100%         70%          40%                               │
└────────────────────────────────────────────────────────────────┘
```

### User Story Layout
Sprint progress with 2 user story bars.

```
┌────────────────────────────────────────────────────────────────┐
│  S1  ██████████████████████████░░░░░░░░░░░░░░░░░░░  80%       │  ← Sprint
│                                                                │
│  U1  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  50%       │  ← User Story 1
│                                                                │
│  U2  ████████████████████████████░░░░░░░░░░░░░░░░  70%       │  ← User Story 2
└────────────────────────────────────────────────────────────────┘
```

### Cycling Mode
Automatically cycles through user stories in pairs every N seconds.

---

## Hardware Setup

### Required Components

| Component | Specification | Purpose |
|-----------|--------------|---------|
| Raspberry Pi 4 | 2GB+ RAM | Main processor |
| MicroSD Card | 16GB+ Class 10 | System storage |
| Power Supply | 5V 3A USB-C | Pi power |
| LED Matrix | 64x64 RGB HUB75E | Display |
| Matrix Power | 5V 8A (minimum) | LED power |
| Jumper Wires | Female-Female | GPIO connections |

### LED Matrix Specifications (HUB75E)

- Resolution: 64x64 pixels (4096 LEDs)
- Pitch: 3mm
- Size: 192 x 192 x 14mm
- Interface: HUB75E (1/32 scan)
- Voltage: 5V DC
- Max Power: 40W

### GPIO Wiring Diagram

Connect the HUB75E connector to Raspberry Pi GPIO pins:

```
┌─────────────────────────────────────────────────────────────────┐
│                     HUB75E CONNECTOR                            │
│                                                                 │
│   Pin Layout (looking at connector on LED panel):               │
│                                                                 │
│   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐           │
│   │ R1  │ G1  │ B1  │ GND │ R2  │ G2  │ B2  │ GND │  Row 1    │
│   ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤           │
│   │  A  │  B  │  C  │  D  │  E  │ CLK │ LAT │ OE  │  Row 2    │
│   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 4 GPIO                          │
│                                                                 │
│   HUB75E Pin    →    RPi GPIO Pin    →    Physical Pin         │
│   ───────────────────────────────────────────────────          │
│   R1            →    GPIO 17         →    Pin 11               │
│   G1            →    GPIO 18         →    Pin 12               │
│   B1            →    GPIO 4          →    Pin 7                │
│   R2            →    GPIO 23         →    Pin 16               │
│   G2            →    GPIO 24         →    Pin 18               │
│   B2            →    GPIO 25         →    Pin 22               │
│   A             →    GPIO 22         →    Pin 15               │
│   B             →    GPIO 26         →    Pin 37               │
│   C             →    GPIO 27         →    Pin 13               │
│   D             →    GPIO 20         →    Pin 38               │
│   E             →    GPIO 21         →    Pin 40               │
│   CLK           →    GPIO 11         →    Pin 23               │
│   LAT           →    GPIO 4          →    Pin 7                │
│   OE            →    GPIO 18         →    Pin 12               │
│   GND           →    Ground          →    Pin 6, 9, 14, etc.   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Power Configuration

```
┌──────────────────────────────────────────────────────────────┐
│                     POWER CONFIGURATION                       │
│                                                               │
│  ┌─────────────┐                    ┌─────────────────────┐  │
│  │ 5V 3A PSU   │───USB-C──────────▶│ Raspberry Pi 4      │  │
│  └─────────────┘                    └─────────────────────┘  │
│                                                               │
│  ┌─────────────┐                    ┌─────────────────────┐  │
│  │ 5V 8A+ PSU  │───Barrel/Screw───▶│ LED Matrix Power    │  │
│  └─────────────┘                    └─────────────────────┘  │
│                                                               │
│  IMPORTANT: Connect GND from both power supplies together!   │
└──────────────────────────────────────────────────────────────┘
```

### Enable SPI

```bash
# Via raspi-config
sudo raspi-config
# Navigate: Interface Options → SPI → Enable

# Or via command line
sudo raspi-config nonint do_spi 0

# Verify
ls /dev/spidev*
# Should show: /dev/spidev0.0  /dev/spidev0.1
```

### User Permissions

```bash
# Add user to required groups
sudo usermod -a -G gpio focus
sudo usermod -a -G video focus

# Log out and back in for changes to take effect
```

---

## Systemd Services

### Service Overview

| Service | Description | Port/Socket | Dependencies |
|---------|-------------|-------------|--------------|
| `led-manager.service` | LED daemon | `/tmp/led-manager.sock` | network-online |
| `bootmanager.service` | System orchestrator | - | led-manager |
| `focus-server.service` | Flask API | 5001 | network-online |

### Service Files

#### led-manager.service

```ini
[Unit]
Description=Focus LED Manager Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=focus
Group=focus
WorkingDirectory=/home/focus/focus/shared/led_manager
Environment="PYTHONPATH=/home/focus/focus/shared"
ExecStart=/home/focus/focus/shared/led_manager/venv/bin/python3 -m led_manager_daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### bootmanager.service

```ini
[Unit]
Description=Focus Raspberry Pi Bootmanager
After=network-online.target led-manager.service
Wants=network-online.target
Requires=led-manager.service

[Service]
Type=simple
User=focus
Group=focus
WorkingDirectory=/home/focus/focus/bootmanager
Environment="PATH=/home/focus/focus/bootmanager/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/home/focus/focus/bootmanager:/home/focus/focus/shared"
ExecStart=/home/focus/focus/bootmanager/venv/bin/python3 -m src.main
Restart=always
RestartSec=10
StandardOutput=append:/var/log/bootmanager.log
StandardError=append:/var/log/bootmanager.error.log

[Install]
WantedBy=multi-user.target
```

### Service Management

```bash
# Start/stop/restart
sudo systemctl start led-manager
sudo systemctl stop bootmanager
sudo systemctl restart focus-server

# View status
sudo systemctl status bootmanager

# View logs
sudo journalctl -u bootmanager -f

# Enable/disable at boot
sudo systemctl enable led-manager
sudo systemctl disable bootmanager
```

---

## Discord Bot Commands

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `!<cmd>` | Execute shell command | `!ls -la` |
| `!ps` | List active jobs | `!ps` |
| `!tail <id> [n]` | Show last n lines of job | `!tail a3f7b21c 50` |
| `!stop <id>` | Stop running job | `!stop a3f7b21c` |
| `!status` | System status (CPU, RAM, uptime) | `!status` |
| `!services` | Service status | `!services` |
| `!urls` | Show SSH & HTTP tunnel URLs | `!urls` |
| `!restart-server` | Restart Flask backend | `!restart-server` |
| `!restart-frontend` | Restart Next.js | `!restart-frontend` |
| `!reboot` | Reboot Raspberry Pi | `!reboot` |
| `!help` | Show help message | `!help` |

### Setup Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to Bot → Add Bot
4. Enable "Message Content Intent"
5. Copy bot token to `secrets.env`
6. Go to OAuth2 → URL Generator
7. Select: `bot` scope, `Send Messages` + `Read Messages` permissions
8. Use generated URL to invite bot to your server
9. Copy channel ID to `secrets.env`

---

## Taiga Integration

### Setup Webhook in Taiga

1. Go to your Taiga project settings
2. Navigate to Integrations → Webhooks
3. Add new webhook:
   - **URL**: `https://your-ngrok-url.ngrok.io/api/taiga/webhook`
   - **Secret**: Generate a secure secret
4. Save the webhook secret in your Focus settings page

### Configure in Focus

1. Open Focus web UI
2. Go to Settings
3. Enter webhook secret
4. Save configuration

### Sync Flow

```
┌──────────────┐     Webhook     ┌──────────────┐     Sync     ┌──────────────┐
│    Taiga     │────────────────▶│    Focus     │─────────────▶│   LED Matrix │
│              │                 │   Backend    │              │              │
│ Task Updated │                 │ Update Local │              │ Show Progress│
└──────────────┘                 └──────────────┘              └──────────────┘
```

### Auto-Login

The system supports auto-login to Taiga. When enabled:
1. Credentials are securely stored locally
2. On boot, Focus automatically authenticates with Taiga
3. Sync happens automatically

---

## Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server (hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

**Dev server runs on:** `http://localhost:3000`

### Backend Development

```bash
cd server

# Activate virtual environment
source venv/bin/activate

# Start development server
python run.py

# Or with Flask CLI
export FLASK_APP=run.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5001
```

**API server runs on:** `http://localhost:5001`

### LED Manager Development

```bash
cd shared/led_manager

# Activate virtual environment
source venv/bin/activate

# Run in mock mode (no hardware)
export LED_MOCK_MODE=true
python -m led_manager_daemon

# Test client
python -c "from led_manager_client import LEDManagerClient; led = LEDManagerClient(); led.show_progress(50)"
```

### Running Without Raspberry Pi

For development on a regular machine:

1. Set `LED_MOCK_MODE=true` in environment
2. LED daemon will log commands instead of controlling hardware
3. All other functionality works normally

---

## Troubleshooting

### LED Not Displaying

**Solutions:**

1. **Check SPI is enabled:**
   ```bash
   ls /dev/spidev*
   # Should show /dev/spidev0.0
   ```

2. **Check user permissions:**
   ```bash
   groups
   # Should include: gpio video
   ```

3. **Check LED daemon is running:**
   ```bash
   sudo systemctl status led-manager
   ```

4. **Check socket exists:**
   ```bash
   ls -la /tmp/led-manager.sock
   ```

5. **Test manually:**
   ```bash
   cd shared/led_manager
   source venv/bin/activate
   python -c "from led_manager_client import LEDManagerClient; led = LEDManagerClient(); led.test()"
   ```

### WiFi Connection Issues

**Solutions:**

1. **Check credentials in secrets.env:**
   ```bash
   cat ~/.config/bootmanager/secrets.env | grep WIFI
   ```

2. **Check NetworkManager:**
   ```bash
   nmcli device status
   ```

3. **Manual connection test:**
   ```bash
   nmcli device wifi connect "SSID" password "password"
   ```

### Discord Bot Offline

**Solutions:**

1. **Check bot token is correct**
2. **Verify Message Content Intent is enabled** in Discord Developer Portal
3. **Check channel ID is correct**
4. **Check logs:**
   ```bash
   sudo journalctl -u bootmanager | grep -i discord
   ```

### Taiga Sync Errors

**Solutions:**

1. **Check Taiga credentials** - Try logging out and back in
2. **Check webhook secret matches** - Verify in Focus settings
3. **Manual sync:**
   ```bash
   curl -X POST http://localhost:5001/api/taiga/sync
   ```

### Service Won't Start

**Solutions:**

1. **Check service status:**
   ```bash
   sudo systemctl status <service-name>
   ```

2. **Check detailed logs:**
   ```bash
   sudo journalctl -u <service-name> -n 100 --no-pager
   ```

3. **Reset failed state:**
   ```bash
   sudo systemctl reset-failed <service-name>
   ```

### Common Log Locations

| Log | Location |
|-----|----------|
| LED Manager | `/var/log/led-manager.log` |
| Bootmanager | `/var/log/bootmanager.log` |
| Flask Server | `server/bootmanager_server.log` |
| Job Outputs | `~/.cmdruns/<job_id>.log` |

---

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

---

## Credits

- [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) by Henner Zeller
- [shadcn/ui](https://ui.shadcn.com/) for React components
- [TanStack Query](https://tanstack.com/query) for data fetching
- [discord.py](https://discordpy.readthedocs.io/) for Discord integration
- [Taiga](https://taiga.io/) for project management integration
