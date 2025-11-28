# Installing Failsafe System Fix

This guide walks you through deploying the infinite reboot fix on your Raspberry Pi.

## What Was Fixed

The infinite reboot loop when launching tunnels has been resolved by implementing a "Single Owner" architecture:
- `ngrok-ssh.service` exclusively manages the SSH tunnel (port 4040)
- Bootmanager queries the SSH tunnel instead of creating its own
- Bootmanager only manages the HTTP tunnel (port 4041)
- No more port conflicts = no more infinite reboots

## Prerequisites

- SSH access to your Raspberry Pi
- The code changes already pulled to the Pi (via auto-pull or manual `git pull`)

## Installation Steps

### 1. Navigate to the bootmanager directory

```bash
cd ~/focus/bootmanager
```

### 2. Create the ngrok auth token environment file

```bash
# Copy the example file
cp config/ngrok-ssh.env.example config/ngrok-ssh.env

# Edit and add your actual ngrok auth token
nano config/ngrok-ssh.env
```

**Get your auth token from:** https://dashboard.ngrok.com/get-started/your-authtoken

The file should look like this:
```
NGROK_AUTHTOKEN=your_actual_token_here
```

Save and exit (Ctrl+X, Y, Enter in nano).

### 3. Verify the environment file is git-ignored

```bash
# This should NOT show config/ngrok-ssh.env (should be ignored)
git status
```

If you see `config/ngrok-ssh.env` in git status, something is wrong. The `.gitignore` should exclude it.

### 4. Update systemd services

```bash
# Copy the updated ngrok-ssh service file
sudo cp systemd/ngrok-ssh.service /etc/systemd/system/

# Reload systemd to pick up changes
sudo systemctl daemon-reload
```

### 5. Restart the services

```bash
# Restart emergency SSH tunnel first
sudo systemctl restart ngrok-ssh

# Wait a few seconds for it to initialize
sleep 5

# Restart bootmanager
sudo systemctl restart bootmanager
```

### 6. Verify everything is working

```bash
# Check emergency tunnel status (should be active/running)
sudo systemctl status ngrok-ssh

# Check bootmanager status (should be active/running)
sudo systemctl status bootmanager

# Get your SSH tunnel URL
~/get-ssh-tunnel.sh
```

### 7. Check the logs

```bash
# Emergency tunnel logs (should show ngrok URL)
tail -50 /var/log/ngrok-ssh.log

# Bootmanager logs (should show "Emergency SSH tunnel found")
tail -50 /var/log/bootmanager.log
```

## Expected Output

### ngrok-ssh.service logs
You should see something like:
```
t=... lvl=info msg="started tunnel" obj=tunnels name=command_line addr=... url=tcp://X.tcp.ngrok.io:XXXXX
```

### bootmanager.log
You should see:
```
[5/11] Querying emergency SSH tunnel...
[Ngrok] Querying emergency SSH tunnel (ngrok-ssh.service)...
[Ngrok] Found emergency SSH tunnel: tcp://X.tcp.ngrok.io:XXXXX
✓ Emergency SSH tunnel found
  SSH: ssh focus@X.tcp.ngrok.io -p XXXXX
```

### What you should NOT see
- ❌ No "Failed to start ngrok tunnel" followed by immediate restart
- ❌ No infinite loop of LED showing "T" then rebooting
- ❌ No `sys.exit(1)` in bootmanager logs

## Troubleshooting

### Emergency tunnel not starting

**Check auth token:**
```bash
cat ~/focus/bootmanager/config/ngrok-ssh.env
```

**Check service logs:**
```bash
sudo journalctl -u ngrok-ssh -n 100
```

**Common issues:**
- Invalid auth token
- Network connectivity problems
- Port 4040 already in use by something else

### Bootmanager warns "Emergency SSH tunnel not available"

This is OK! Bootmanager will continue running. Check if ngrok-ssh.service is actually running:

```bash
sudo systemctl status ngrok-ssh
```

If it's not running, start it:
```bash
sudo systemctl start ngrok-ssh
sudo systemctl enable ngrok-ssh  # Enable auto-start on boot
```

### Reset failure counter

If bootmanager hit the restart limit before the fix:

```bash
sudo systemctl reset-failed bootmanager
sudo systemctl start bootmanager
```

## Verification Checklist

- [ ] `config/ngrok-ssh.env` exists and contains valid auth token
- [ ] `config/ngrok-ssh.env` is NOT tracked by git
- [ ] `ngrok-ssh.service` is active and running
- [ ] Emergency tunnel URL visible in logs
- [ ] `bootmanager.service` is active and running
- [ ] Bootmanager logs show "Emergency SSH tunnel found"
- [ ] No reboot loops observed
- [ ] Can SSH via the emergency tunnel

## Next Steps

1. **Test the emergency tunnel:** Use the SSH command from logs to connect
2. **Reboot the Pi:** Ensure services start correctly on boot
3. **Monitor for a few hours:** Check that no restart loops occur
4. **Update Discord notification:** Should receive boot notification with tunnel URLs

## Need Help?

Check the full documentation: `FAILSAFE.md`

Or review the logs:
- `/var/log/ngrok-ssh.log` - Emergency tunnel
- `/var/log/bootmanager.log` - Bootmanager output
- `/var/log/bootmanager.error.log` - Bootmanager errors
