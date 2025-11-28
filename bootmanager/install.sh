#!/bin/bash

# Raspberry Pi Boot Manager - Installation Script
# This script sets up the boot manager on a Raspberry Pi

set -e  # Exit on error

echo "======================================"
echo "Raspberry Pi Boot Manager - Installer"
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
INSTALL_DIR="$USER_HOME/focus/bootmanager"

echo "Installing for user: $ACTUAL_USER"
echo "Installation directory: $INSTALL_DIR"
echo ""

# Step 1: Update system
echo "[1/8] Updating system packages..."
apt update
apt upgrade -y

# Step 2: Install system dependencies
echo ""
echo "[2/8] Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    openssh-server \
    network-manager \
    wireless-tools \
    nginx

# Step 3: Enable SPI for LED matrix
echo ""
echo "[3/8] Enabling SPI interface..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" >> /boot/config.txt
    echo "✓ SPI enabled (reboot required)"
else
    echo "✓ SPI already enabled"
fi

# Step 4: Install ngrok
echo ""
echo "[4/8] Installing ngrok..."
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

# Step 5: Set up project directory
echo ""
echo "[5/8] Setting up project directory..."
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ Project directory not found: $INSTALL_DIR"
    echo "   Please clone or copy the project to this location first"
    exit 1
fi

cd "$INSTALL_DIR"

# Step 6: Create Python virtual environment
echo ""
echo "[6/8] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    sudo -u $ACTUAL_USER python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install dependencies
echo "Installing Python dependencies..."
sudo -u $ACTUAL_USER bash -c "source venv/bin/activate && pip3 install --upgrade pip --break-system-packages && pip3 install -r requirements.txt --break-system-packages"
echo "✓ Python dependencies installed"

# Step 7: Set up configuration
echo ""
echo "[7/8] Setting up configuration..."

# Create config directories
mkdir -p "$USER_HOME/.config/bootmanager"
chown -R $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.config/bootmanager"

# Copy example config if secrets.env doesn't exist
if [ ! -f "$USER_HOME/.config/bootmanager/secrets.env" ]; then
    if [ -f "config/secrets.env.example" ]; then
        sudo -u $ACTUAL_USER cp config/secrets.env.example "$USER_HOME/.config/bootmanager/secrets.env"
        echo "✓ Created secrets.env from example"
        echo "⚠️  IMPORTANT: Edit $USER_HOME/.config/bootmanager/secrets.env with your credentials"
    else
        echo "⚠️  secrets.env.example not found, you'll need to create secrets.env manually"
    fi
else
    echo "✓ secrets.env already exists"
fi

# Create log directories
mkdir -p logs .cmdruns
chown -R $ACTUAL_USER:$ACTUAL_USER logs .cmdruns

# Step 8: Install systemd service
echo ""
echo "[8/8] Installing systemd service..."

# Copy service file
cp systemd/bootmanager.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable bootmanager.service

echo "✓ Systemd service installed and enabled"

echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit configuration:"
echo "   nano $USER_HOME/.config/bootmanager/secrets.env"
echo ""
echo "2. Configure ngrok:"
echo "   ngrok config add-authtoken YOUR_TOKEN"
echo ""
echo "3. Test the service:"
echo "   sudo systemctl start bootmanager.service"
echo "   sudo systemctl status bootmanager.service"
echo ""
echo "4. View logs:"
echo "   journalctl -u bootmanager.service -f"
echo ""
echo "5. Reboot to apply SPI changes:"
echo "   sudo reboot"
echo ""
echo "======================================"
