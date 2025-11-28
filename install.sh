#!/bin/bash

# Focus Project - Master Installation Script
# Installs LED Manager, Bootmanager, and prepares Server infrastructure

set -e  # Exit on error

echo "======================================"
echo "Focus Project - Master Installer"
echo "======================================"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  WARNING: This doesn't appear to be a Raspberry Pi"
    echo "   Installation may not work correctly"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo "⚠️  Please run with sudo as a regular user, not as root directly"
    exit 1
fi

USER_HOME=$(eval echo ~$ACTUAL_USER)
PROJECT_ROOT="$USER_HOME/focus"
LED_MANAGER_DIR="$PROJECT_ROOT/shared/led_manager"
BOOTMANAGER_DIR="$PROJECT_ROOT/bootmanager"
SERVER_DIR="$PROJECT_ROOT/server"

echo "Installing for user: $ACTUAL_USER"
echo "Project root: $PROJECT_ROOT"
echo ""

# Verify project directory exists
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ Project directory not found: $PROJECT_ROOT"
    echo "   Please clone or copy the project to this location first"
    exit 1
fi

cd "$PROJECT_ROOT"

# ============================================================================
# SYSTEM DEPENDENCIES
# ============================================================================

echo "[1/10] Updating system packages..."
apt update
apt upgrade -y

echo ""
echo "[2/10] Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    openssh-server \
    network-manager \
    wireless-tools \
    curl \
    wget

# ============================================================================
# HARDWARE SETUP
# ============================================================================

echo ""
echo "[3/10] Enabling SPI interface for LED matrix..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" >> /boot/config.txt
    echo "✓ SPI enabled (reboot required)"
    SPI_REBOOT_NEEDED=true
else
    echo "✓ SPI already enabled"
fi

# ============================================================================
# NGROK INSTALLATION
# ============================================================================

echo ""
echo "[4/10] Installing ngrok..."
if ! command -v ngrok &> /dev/null; then
    cd /tmp
    wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
    tar xzf ngrok-v3-stable-linux-arm.tgz
    mv ngrok /usr/local/bin/
    rm ngrok-v3-stable-linux-arm.tgz
    echo "✓ ngrok installed"
else
    echo "✓ ngrok already installed"
fi

# ============================================================================
# LED MANAGER INSTALLATION
# ============================================================================

echo ""
echo "[5/10] Installing LED Manager..."
cd "$LED_MANAGER_DIR"

# Create virtual environment
if [ ! -d "venv" ]; then
    sudo -u $ACTUAL_USER python3 -m venv venv
    echo "✓ LED Manager virtual environment created"
else
    echo "✓ LED Manager virtual environment already exists"
fi

# Install dependencies
echo "  Installing LED Manager dependencies..."
sudo -u $ACTUAL_USER bash -c "source venv/bin/activate && pip3 install --upgrade pip && pip3 install -r requirements.txt"
echo "✓ LED Manager dependencies installed"

# Install systemd service
echo "  Installing LED Manager systemd service..."
cp systemd/led-manager.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable led-manager.service
echo "✓ LED Manager service installed and enabled"

# ============================================================================
# BOOTMANAGER INSTALLATION
# ============================================================================

echo ""
echo "[6/10] Installing Bootmanager..."
cd "$BOOTMANAGER_DIR"

# Create virtual environment
if [ ! -d "venv" ]; then
    sudo -u $ACTUAL_USER python3 -m venv venv
    echo "✓ Bootmanager virtual environment created"
else
    echo "✓ Bootmanager virtual environment already exists"
fi

# Install dependencies
echo "  Installing Bootmanager dependencies..."
sudo -u $ACTUAL_USER bash -c "source venv/bin/activate && pip3 install --upgrade pip && pip3 install -r requirements.txt"
echo "✓ Bootmanager dependencies installed"

# Create log directories
mkdir -p logs .cmdruns
chown -R $ACTUAL_USER:$ACTUAL_USER logs .cmdruns

# Install systemd service
echo "  Installing Bootmanager systemd service..."
cp systemd/bootmanager.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bootmanager.service
echo "✓ Bootmanager service installed and enabled"

# ============================================================================
# CONFIGURATION SETUP
# ============================================================================

echo ""
echo "[7/10] Setting up configuration..."

# Create config directory
CONFIG_DIR="$USER_HOME/.config/focus"
mkdir -p "$CONFIG_DIR"
chown -R $ACTUAL_USER:$ACTUAL_USER "$CONFIG_DIR"

# Copy example config if secrets.env doesn't exist
if [ ! -f "$CONFIG_DIR/secrets.env" ]; then
    # Check both locations for example config
    if [ -f "$PROJECT_ROOT/bootmanager/config/secrets.env.example" ]; then
        sudo -u $ACTUAL_USER cp "$PROJECT_ROOT/bootmanager/config/secrets.env.example" "$CONFIG_DIR/secrets.env"
        echo "✓ Created secrets.env from example"
        CONFIG_NEEDS_EDIT=true
    elif [ -f "$PROJECT_ROOT/bootmanager/config/secret.env.example" ]; then
        sudo -u $ACTUAL_USER cp "$PROJECT_ROOT/bootmanager/config/secret.env.example" "$CONFIG_DIR/secrets.env"
        echo "✓ Created secrets.env from example"
        CONFIG_NEEDS_EDIT=true
    else
        echo "⚠️  No example config found, creating blank secrets.env"
        sudo -u $ACTUAL_USER cat > "$CONFIG_DIR/secrets.env" << 'EOF'
# Focus Project Configuration

# WiFi Settings (used by bootmanager)
WIFI_SSID=YourHotspotName
WIFI_PASSWORD=YourPassword

# Discord Bot (used by bootmanager)
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_channel_id

# Ngrok (used by bootmanager & server)
NGROK_AUTH_TOKEN=your_ngrok_token

# LED Manager
LED_SOCKET_PATH=/var/run/led-manager.sock
LED_MOCK_MODE=false
EOF
        chown $ACTUAL_USER:$ACTUAL_USER "$CONFIG_DIR/secrets.env"
        echo "✓ Created blank secrets.env"
        CONFIG_NEEDS_EDIT=true
    fi
else
    echo "✓ secrets.env already exists"
fi

# ============================================================================
# SERVER PREPARATION (FUTURE)
# ============================================================================

echo ""
echo "[8/10] Preparing Server directory..."
if [ -d "$SERVER_DIR" ]; then
    cd "$SERVER_DIR"

    # Create placeholder requirements.txt if it doesn't exist
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt << 'EOF'
# Flask Server Dependencies (to be added when implementing)
# Flask>=2.3.0
# Flask-CORS>=4.0.0
# requests>=2.31.0
EOF
        chown $ACTUAL_USER:$ACTUAL_USER requirements.txt
        echo "✓ Created placeholder requirements.txt"
    fi

    # Create data directory
    mkdir -p data
    chown -R $ACTUAL_USER:$ACTUAL_USER data
    echo "✓ Server directory prepared"
else
    echo "⚠️  Server directory not found, skipping"
fi

# ============================================================================
# PERMISSIONS AND OWNERSHIP
# ============================================================================

echo ""
echo "[9/10] Setting permissions..."

# Set ownership of entire project
chown -R $ACTUAL_USER:$ACTUAL_USER "$PROJECT_ROOT"

# Create socket directory with proper permissions
mkdir -p /var/run/led-manager
chmod 755 /var/run/led-manager

# Set log file permissions
touch /var/log/led-manager.log /var/log/led-manager.error.log
touch /var/log/bootmanager.log /var/log/bootmanager.error.log
chown $ACTUAL_USER:$ACTUAL_USER /var/log/led-manager.log /var/log/led-manager.error.log
chown $ACTUAL_USER:$ACTUAL_USER /var/log/bootmanager.log /var/log/bootmanager.error.log

echo "✓ Permissions set"

# ============================================================================
# POLKIT CONFIGURATION
# ============================================================================

echo ""
echo "[9.5/10] Configuring polkit for passwordless service management..."

# Copy polkit rule to allow focus user to manage services without password
POLKIT_DIR="/etc/polkit-1/localauthority/50-local.d"
mkdir -p "$POLKIT_DIR"
cp "$PROJECT_ROOT/shared/polkit/10-focus-services.pkla" "$POLKIT_DIR/"
chmod 644 "$POLKIT_DIR/10-focus-services.pkla"

echo "✓ Polkit configured (focus user can manage services without sudo password)"

# ============================================================================
# SERVICE STARTUP
# ============================================================================

echo ""
echo "[10/10] Starting services..."

# Reload systemd
systemctl daemon-reload

# Start LED Manager first
echo "  Starting LED Manager..."
systemctl start led-manager.service

# Wait for socket to be available
sleep 2

if [ -S "/var/run/led-manager.sock" ]; then
    echo "✓ LED Manager started successfully"
else
    echo "⚠️  LED Manager socket not found, checking status..."
    systemctl status led-manager.service --no-pager
fi

# Start Bootmanager
echo "  Starting Bootmanager..."
systemctl start bootmanager.service
sleep 1

echo "✓ Services started"

# ============================================================================
# INSTALLATION COMPLETE
# ============================================================================

echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""

# Check service status
echo "Service Status:"
echo "---------------"
systemctl is-active led-manager.service &> /dev/null && echo "✓ LED Manager: RUNNING" || echo "✗ LED Manager: STOPPED"
systemctl is-active bootmanager.service &> /dev/null && echo "✓ Bootmanager: RUNNING" || echo "✗ Bootmanager: STOPPED"
echo ""

echo "Installation Summary:"
echo "---------------------"
echo "✓ LED Manager installed (shared/led_manager/)"
echo "✓ Bootmanager installed (bootmanager/)"
echo "✓ Server directory prepared (server/)"
echo "✓ Systemd services configured"
echo ""

if [ "$CONFIG_NEEDS_EDIT" = true ]; then
    echo "⚠️  IMPORTANT - Configuration Required:"
    echo "-------------------------------------"
    echo "1. Edit your configuration file:"
    echo "   nano $CONFIG_DIR/secrets.env"
    echo ""
    echo "   Update the following:"
    echo "   - WIFI_SSID and WIFI_PASSWORD"
    echo "   - DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID"
    echo "   - NGROK_AUTH_TOKEN"
    echo ""
    echo "2. Configure ngrok (if not already done):"
    echo "   ngrok config add-authtoken YOUR_TOKEN"
    echo ""
fi

echo "Useful Commands:"
echo "----------------"
echo "View LED Manager status:"
echo "  sudo systemctl status led-manager.service"
echo ""
echo "View Bootmanager status:"
echo "  sudo systemctl status bootmanager.service"
echo ""
echo "View LED Manager logs:"
echo "  journalctl -u led-manager.service -f"
echo ""
echo "View Bootmanager logs:"
echo "  journalctl -u bootmanager.service -f"
echo ""
echo "Restart services:"
echo "  sudo systemctl restart led-manager.service"
echo "  sudo systemctl restart bootmanager.service"
echo ""
echo "Test LED Manager:"
echo "  cd $LED_MANAGER_DIR"
echo "  source venv/bin/activate"
echo "  python3 example_usage.py"
echo ""

if [ "$SPI_REBOOT_NEEDED" = true ]; then
    echo "⚠️  REBOOT REQUIRED:"
    echo "-------------------"
    echo "SPI was enabled for the LED matrix."
    echo "Please reboot to apply changes:"
    echo "  sudo reboot"
    echo ""
fi

echo "======================================"
echo ""
echo "For more information, see:"
echo "  - ARCHITECTURE.md"
echo "  - shared/led_manager/README.md"
echo "  - bootmanager/RASPBERRY_PI_BOOT_MANAGER_SPECS.md"
echo ""
