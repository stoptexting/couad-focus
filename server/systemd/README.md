# Focus Server Systemd Service

## Installation

On the Raspberry Pi, run:

```bash
# Copy service file to systemd
sudo cp /home/focus/focus/server/systemd/focus-server.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable focus-server

# Start the service
sudo systemctl start focus-server

# Check status
sudo systemctl status focus-server

# View logs
sudo journalctl -u focus-server -f
```

## Requirements

The `focus` user must be in the `gpio` and `video` groups for LED matrix access:

```bash
sudo usermod -aG gpio focus
sudo usermod -aG video focus
```

## Troubleshooting

If LED sync doesn't work, check logs for GPIO permission errors:
```bash
sudo journalctl -u focus-server -n 100
```
