#!/bin/bash
# Install fail-safe SSH access system

set -e

echo "======================================"
echo "Installing Fail-Safe SSH Access"
echo "======================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "Please run as focus user (not root)"
   exit 1
fi

# Install ngrok if not present
if ! command -v ngrok &> /dev/null; then
    echo "[1/5] Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update
    sudo apt install -y ngrok
else
    echo "[1/5] Ngrok already installed ✓"
fi

# Copy and enable ngrok-ssh service (emergency access)
echo "[2/5] Setting up emergency SSH tunnel service..."
sudo cp ~/focus/bootmanager/systemd/ngrok-ssh.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ngrok-ssh.service
sudo systemctl restart ngrok-ssh.service

# Replace bootmanager service with safe mode version
echo "[3/5] Updating bootmanager to safe mode..."
sudo cp ~/focus/bootmanager/systemd/bootmanager-safe.service /etc/systemd/system/bootmanager.service
sudo systemctl daemon-reload

# Create helper script to get SSH tunnel URL
echo "[4/5] Creating helper script..."
cat > ~/get-ssh-tunnel.sh << 'SCRIPT'
#!/bin/bash
# Get current SSH tunnel URL

# Try ngrok API
if curl -s http://localhost:4040/api/tunnels &>/dev/null; then
    echo "SSH Tunnel from ngrok-ssh service:"
    curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
for t in data.get('tunnels', []):
    if t.get('proto') == 'tcp':
        url = t.get('public_url', '').replace('tcp://', '')
        if ':' in url:
            host, port = url.rsplit(':', 1)
            print(f'  ssh focus@{host} -p {port}')
            break
"
else
    echo "Ngrok not running or API not available"
fi

# Check ngrok log
echo ""
echo "Recent ngrok log:"
tail -5 /var/log/ngrok-ssh.log | grep -i "url=" || echo "No URL found in log yet"
SCRIPT

chmod +x ~/get-ssh-tunnel.sh

echo "[5/5] Testing services..."
sudo systemctl status ngrok-ssh.service --no-pager | head -5
echo ""
echo "======================================"
echo "✓ Fail-Safe System Installed!"
echo "======================================"
echo ""
echo "Emergency SSH tunnel: sudo systemctl status ngrok-ssh.service"
echo "Get tunnel URL: ~/get-ssh-tunnel.sh"
echo ""
echo "Restart bootmanager: sudo systemctl restart bootmanager"
echo ""
