# Raspberry Pi Boot Manager

A comprehensive remote management system for Raspberry Pi that provides SSH access via ngrok tunnel and Discord bot command execution, with visual feedback through an LED matrix.

## Features

- **Automatic Wi-Fi Connection**: Connects to configured hotspot on boot
- **SSH Tunnel via Ngrok**: Establishes public SSH access through ngrok
- **Discord Bot Control**: Execute commands remotely via Discord
- **LED Matrix Display**: Visual status feedback on 8x8 MAX7219 LED matrix
- **Process Management**: Track and manage background jobs
- **Auto-Recovery**: Automatic reconnection on network failures
- **Security**: Command blacklist to prevent dangerous operations

## Hardware Requirements

| Component | Specification |
|-----------|---------------|
| **Raspberry Pi** | Raspberry Pi 4 Model B (2GB+ RAM recommended) |
| **LED Matrix** | MAX7219 8×8 monochrome red LED matrix |
| **Power Supply** | 5V 3A USB-C (official recommended) |
| **Storage** | MicroSD 16GB+ (Class 10 minimum) |

### GPIO Wiring (MAX7219)

```
MAX7219 → Raspberry Pi 4
━━━━━━━━━━━━━━━━━━━━━━━
VCC  → Pin 2  (5V)
GND  → Pin 6  (Ground)
DIN  → Pin 19 (GPIO 10, MOSI)
CS   → Pin 24 (GPIO 8, CE0)
CLK  → Pin 23 (GPIO 11, SCLK)
```

## Software Requirements

- Raspberry Pi OS Lite (Debian 12 Bookworm)
- Python 3.11+
- Discord Bot with Message Content Intent enabled
- Ngrok account with auth token

## Installation

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/yourusername/raspberry-pi-boot-manager.git
cd raspberry-pi-boot-manager
```

### 2. Configure Secrets

```bash
# Create config directory
mkdir -p ~/.config/bootmanager

# Copy and edit configuration
cp config/secrets.env.example ~/.config/bootmanager/secrets.env
nano ~/.config/bootmanager/secrets.env
```

Fill in your credentials:
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `DISCORD_CHANNEL_ID`: Discord channel ID for commands
- `NGROK_AUTH_TOKEN`: Your ngrok authentication token
- `WIFI_SSID`: Your Wi-Fi network name
- `WIFI_PASSWORD`: Your Wi-Fi password

### 3. Run Installation Script

```bash
sudo bash install.sh
```

This will:
- Install system dependencies
- Enable SPI interface
- Install ngrok
- Create Python virtual environment
- Install Python packages
- Set up systemd service
- Configure auto-start on boot

### 4. Reboot

```bash
sudo reboot
```

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Enable **Message Content Intent** (required!)
5. Copy the bot token to `secrets.env`
6. Invite bot to your server with appropriate permissions
7. Get the channel ID where you want to use commands (enable Developer Mode in Discord settings)

## Usage

### Discord Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!<command>` | Execute shell command | `!ls -la` |
| `!ps` | List active jobs | `!ps` |
| `!tail <id> [n]` | Show last n lines of job output | `!tail a3f7b21c 50` |
| `!stop <id>` | Stop a running job | `!stop a3f7b21c` |
| `!status` | Show system status | `!status` |
| `!help` | Show help message | `!help` |

### LED Status Indicators

- **Boot Animation**: System starting up
- **Wi-Fi Searching**: Connecting to network (animated)
- **W**: Wi-Fi connected
- **Wi-Fi Barred**: Connection error
- **T**: Tunnel active
- **D**: Discord bot active
- **Rotating Dot**: Idle state
- **Checkmark**: Success
- **X**: Error

### Example Workflows

#### Run a Python Script
```
!python3 /home/focus/script.py
```

#### Monitor System Resources
```
!top -b -n 1 | head -20
```

#### Check Running Jobs
```
!ps
```

#### View Job Output
```
!tail a3f7b21c 30
```

#### Stop a Job
```
!stop a3f7b21c
```

## Service Management

### Start Service
```bash
sudo systemctl start bootmanager.service
```

### Stop Service
```bash
sudo systemctl stop bootmanager.service
```

### Restart Service
```bash
sudo systemctl restart bootmanager.service
```

### Check Status
```bash
sudo systemctl status bootmanager.service
```

### View Logs
```bash
# Real-time logs
journalctl -u bootmanager.service -f

# Last 100 lines
journalctl -u bootmanager.service -n 100
```

## Security Features

### Command Blacklist

The following dangerous patterns are automatically blocked:

- `rm -rf /` - Delete root directory
- `sudo rm` - Privileged deletion
- `dd if=/dev/zero` - Disk wipe
- `mkfs.*` - Format filesystem
- Fork bombs and other malicious patterns

### Best Practices

1. **Restrict Discord Channel**: Only allow trusted users in the command channel
2. **Use SSH Keys**: Configure SSH key authentication instead of passwords
3. **Monitor Logs**: Regularly check command execution logs
4. **Keep Updated**: Update system packages regularly
5. **Firewall**: Consider setting up UFW firewall rules

## Troubleshooting

### Service Won't Start

```bash
# Check detailed error
sudo systemctl status bootmanager.service

# View full logs
journalctl -u bootmanager.service -n 100
```

### LED Matrix Not Working

```bash
# Check SPI is enabled
ls -l /dev/spidev0.0

# If missing, enable SPI
sudo raspi-config
# Interface Options > SPI > Enable
```

### Discord Bot Not Responding

1. Verify bot token in `~/.config/bootmanager/secrets.env`
2. Ensure **Message Content Intent** is enabled in Discord Developer Portal
3. Check bot has permission to read/send messages in the channel
4. Verify channel ID is correct

### Wi-Fi Connection Failed

```bash
# Check Wi-Fi credentials
cat ~/.config/bootmanager/secrets.env

# Test connection manually
nmcli device wifi connect "YOUR_SSID" password "YOUR_PASSWORD"
```

### Ngrok Tunnel Issues

```bash
# Verify ngrok is installed
which ngrok

# Test ngrok manually
ngrok tcp 22 --authtoken YOUR_TOKEN
```

## Directory Structure

```
raspberry-pi-boot-manager/
├── src/
│   ├── main.py                 # Main orchestrator
│   ├── config.py               # Configuration loader
│   ├── network/
│   │   ├── wifi_manager.py     # Wi-Fi connection
│   │   └── tunnel_manager.py   # Ngrok tunnel
│   ├── display/
│   │   ├── led_controller.py   # LED matrix control
│   │   └── animations.py       # LED patterns
│   ├── discord/
│   │   ├── bot.py              # Discord bot
│   │   ├── commands.py         # Command handlers
│   │   └── job_manager.py      # Process management
│   └── utils/
│       ├── logger.py           # Logging system
│       └── process_runner.py   # Secure command execution
├── systemd/
│   └── bootmanager.service     # Systemd service file
├── config/
│   └── secrets.env.example     # Configuration template
├── logs/                       # Application logs
├── .cmdruns/                   # Job execution logs
├── requirements.txt            # Python dependencies
├── install.sh                  # Installation script
└── README.md                   # This file
```

## Logs Location

- **Main Log**: `logs/bootmanager.log`
- **Error Log**: `logs/bootmanager.error.log`
- **Job Logs**: `.cmdruns/<job_id>.log`
- **System Log**: `journalctl -u bootmanager.service`

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop bootmanager.service
sudo systemctl disable bootmanager.service

# Remove service file
sudo rm /etc/systemd/system/bootmanager.service
sudo systemctl daemon-reload

# Remove project directory
rm -rf ~/raspberry-pi-boot-manager

# Remove configuration
rm -rf ~/.config/bootmanager
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the technical documentation in `RASPBERRY_PI_BOOT_MANAGER_SPECS.md`

---

**Built for Raspberry Pi 4 with ❤️**
