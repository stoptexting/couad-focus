# Fail-Safe System for Headless Raspberry Pi

This system ensures you **ALWAYS have SSH access** even if bootmanager crashes.

## Architecture - "Single Owner" Design

The failsafe system uses a **Single Owner** architecture to prevent port conflicts and ensure reliability:

### Layer 1: Emergency SSH Tunnel (ngrok-ssh.service)
- **Independent** systemd service that runs BEFORE bootmanager
- **Owns the SSH tunnel exclusively** - bootmanager queries this service, doesn't start its own
- Starts ngrok TCP tunnel on port 22 (SSH) with API on port 4040
- Restarts automatically if it crashes
- Logs to `/var/log/ngrok-ssh.log`
- **This is your guaranteed SSH access**

### Layer 2: Bootmanager HTTP Tunnel
- Bootmanager queries Layer 1 for SSH tunnel URL (doesn't create its own)
- Starts HTTP tunnel ONLY (using API port 4041 to avoid conflict)
- If HTTP tunnel fails, bootmanager continues running anyway
- No restart loop if tunnels fail

### Layer 3: Bootmanager Safe Mode
- Limits restart attempts (5 times in 10 minutes, then gives up)
- Runs AFTER emergency SSH tunnel is established
- Auto-pulls from git on startup
- **Non-fatal tunnel failures** - continues running even if HTTP tunnel fails

### Layer 4: Auto Git Pull
- Bootmanager pulls latest code on every startup (Step 0)
- Allows remote fixes by pushing to git
- Pi auto-updates on next restart

## Installation

**On your Raspberry Pi (when you have access):**

```bash
cd ~/focus/bootmanager/scripts
chmod +x install-failsafe.sh
./install-failsafe.sh
```

This will:
1. Install ngrok (if not present)
2. Create `config/ngrok-ssh.env` from template and prompt for auth token
3. Create and enable `ngrok-ssh.service` (emergency access)
4. Update bootmanager to safe mode (limited restarts)
5. Create helper script `~/get-ssh-tunnel.sh`

**IMPORTANT: Set up your ngrok auth token:**

```bash
cd ~/focus/bootmanager/config
cp ngrok-ssh.env.example ngrok-ssh.env
nano ngrok-ssh.env  # Add your actual ngrok auth token
```

Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken

## Usage

### Get SSH Tunnel URL

```bash
# On the Pi
~/get-ssh-tunnel.sh
```

Or check Discord - bootmanager sends the URL when it starts successfully.

### Check Emergency Tunnel Status

```bash
sudo systemctl status ngrok-ssh.service
tail -50 /var/log/ngrok-ssh.log
```

### Check Bootmanager Status

```bash
sudo systemctl status bootmanager
tail -50 /var/log/bootmanager.log
```

### Force Restart

```bash
# Restart emergency tunnel (if needed)
sudo systemctl restart ngrok-ssh.service

# Restart bootmanager
sudo systemctl restart bootmanager
```

### Disable Bootmanager (Emergency)

If bootmanager is completely broken and keeps restarting:

```bash
sudo systemctl stop bootmanager
sudo systemctl disable bootmanager
```

You'll still have SSH access via `ngrok-ssh.service`!

## Recovery Process

If you push bad code and lose access:

1. **Emergency SSH** still works via `ngrok-ssh.service`
2. Find the tunnel URL:
   - Check Discord (if bootmanager started successfully)
   - Or run `~/get-ssh-tunnel.sh` if you have local access
   - Or check systemd logs: `sudo journalctl -u ngrok-ssh -n 50`
3. SSH in using the emergency tunnel
4. Fix the code or revert:
   ```bash
   cd ~/focus
   git reset --hard <good-commit-hash>
   sudo systemctl restart bootmanager
   ```
5. Check bootmanager didn't hit restart limit:
   ```bash
   sudo systemctl reset-failed bootmanager  # Reset failure counter if needed
   sudo systemctl start bootmanager
   ```

## Service Dependencies

```
ngrok-ssh.service (SSH tunnel on port 4040 API)
    ↓
bootmanager.service (queries SSH tunnel, starts HTTP tunnel on port 4041 API)
    ↓
Discord notifications, HTTP tunnel, web services
```

**Port Allocation:**
- Port 4040: ngrok API for SSH tunnel (emergency service)
- Port 4041: ngrok API for HTTP tunnel (bootmanager service)
- This prevents port conflicts and ensures both services can run simultaneously

## Logs

- Emergency SSH tunnel: `/var/log/ngrok-ssh.log`
- Emergency SSH errors: `/var/log/ngrok-ssh.error.log`
- Bootmanager: `/var/log/bootmanager.log`
- Bootmanager errors: `/var/log/bootmanager.error.log`

## Troubleshooting

### Infinite Reboot Loop (FIXED in latest version)

**Symptoms:** LED shows "T", then system reboots, repeats 5 times, then stops.

**Cause (OLD VERSION):** Port conflict between ngrok-ssh.service and bootmanager trying to use same API port 4040.

**Fix (APPLIED):**
- Bootmanager now queries emergency tunnel instead of starting its own SSH tunnel
- HTTP tunnel uses port 4041 to avoid conflict
- Tunnel failures are non-fatal - bootmanager continues running

**If you're still seeing this:**
1. Update to latest code: `cd ~/focus && git pull`
2. Restart both services:
   ```bash
   sudo systemctl restart ngrok-ssh
   sudo systemctl restart bootmanager
   ```

### SSH Tunnel Not Found

**Symptoms:** Bootmanager warns "Emergency SSH tunnel not available"

**Check:**
1. Is ngrok-ssh.service running?
   ```bash
   sudo systemctl status ngrok-ssh
   ```
2. Is the auth token configured?
   ```bash
   cat ~/focus/bootmanager/config/ngrok-ssh.env
   ```
3. Check ngrok logs:
   ```bash
   tail -50 /var/log/ngrok-ssh.log
   ```

### HTTP Tunnel Fails

**Symptoms:** Warning "HTTP tunnel failed to start" but bootmanager continues

**This is normal if:**
- Nginx isn't running
- Frontend/backend services aren't ready
- Network is slow

**Bootmanager will continue and HTTP tunnel can be restarted later**

### Reset Bootmanager Failure Counter

If bootmanager hit the 5-restart limit:

```bash
sudo systemctl reset-failed bootmanager
sudo systemctl start bootmanager
```
