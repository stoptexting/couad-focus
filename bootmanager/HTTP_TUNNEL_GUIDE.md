# HTTP Tunnel Guide

Complete guide to understanding and using the ngrok HTTP tunnel for accessing your Focus web app remotely.

## What is the HTTP Tunnel?

The HTTP tunnel is a **public HTTPS URL** that gives you remote access to your Focus Task Manager web interface from anywhere in the world. It's created by ngrok and tunnels traffic to your Raspberry Pi's nginx server.

### What's Exposed?

- **Frontend:** Next.js web interface (port 3000 → nginx port 80 → ngrok)
- **Backend API:** Flask REST API at `/api` (port 5000 → nginx port 80 → ngrok)
- **Health Check:** `/health` endpoint for monitoring

**Architecture:**
```
Internet → ngrok HTTPS tunnel → nginx (port 80) → {
    / → Next.js frontend (port 3000)
    /api → Flask backend (port 5000)
}
```

---

## When is the HTTP Tunnel Created?

### Boot Sequence

The HTTP tunnel is created at **Step 10.5** during bootmanager initialization:

1. **[0/11]** Pull latest code from git
2. **[1/11]** Load configuration
3. **[2/11]** Initialize logger
4. **[3/11]** Connect to LED manager
5. **[4/11]** Connect to Wi-Fi
6. **[5/11]** Query emergency SSH tunnel
7. **[6/11]** Initialize job manager
8. **[7/11]** Initialize service manager
9. **[8/11]** Start backend server (Flask on port 5000)
10. **[9/11]** Start frontend (Next.js on port 3000)
11. **[10/11]** Set up nginx reverse proxy
12. **[10.5/11]** ⭐ **Start ngrok HTTP tunnel** ← HERE
13. **[11/11]** Start Discord bot
14. Send boot notification with tunnel URLs

### Requirements

The HTTP tunnel is only created if:
- ✅ Nginx is installed and configured
- ✅ Nginx successfully starts
- ✅ Ngrok auth token is valid
- ✅ Network connectivity is available

**Note:** If nginx or HTTP tunnel fails, bootmanager **continues running** (non-fatal). You'll still have SSH access via the emergency tunnel.

---

## Where to Find the HTTP Tunnel URL

### 1. Console Output (during boot)

When the HTTP tunnel starts successfully:

```
[10.5/11] Starting ngrok HTTP tunnel...
[Ngrok] Starting HTTP tunnel for port 80...
[Ngrok] HTTP tunnel will require authentication (user: admin)
[Ngrok] Waiting for HTTP tunnel to establish...
[Ngrok] HTTP tunnel established: https://abc123.ngrok.io
✓ HTTP tunnel started
  Public URL: https://abc123.ngrok.io
  Username: admin
```

### 2. Bootmanager Logs

Check the logs at `/var/log/bootmanager.log`:

```bash
tail -50 /var/log/bootmanager.log | grep -i "http tunnel"
```

You should see:
```
INFO - HTTP tunnel started: https://abc123.ngrok.io
```

### 3. Discord Bot Notification

After boot completes, you'll receive a Discord message:

```
🚀 **Raspberry Pi Boot Manager - Ready**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 **Connexion SSH disponible :**
```
ssh focus@X.tcp.ngrok.io -p XXXXX
```
🌐 IP locale : 192.168.1.XX

🌍 **Site web public (protégé par mot de passe) :**
`https://abc123.ngrok.io`
👤 Username: `admin`

🎯 **Focus Task Manager :**
  • Backend: ✅ `http://localhost:5000`
  • Frontend: ✅ `http://localhost:3000`

⏰ Boot time : 45.2s
```

### 4. Query Ngrok API Directly

Since HTTP tunnel uses port 4041, you can query its status:

```bash
# On the Raspberry Pi
curl -s http://localhost:4041/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
for t in data.get('tunnels', []):
    if t.get('proto') == 'https':
        print(f'Public URL: {t.get(\"public_url\")}')
"
```

### 5. Programmatically via Discord Commands

You can also ask the Discord bot for the URL using commands (if implemented):

```
!status
!tunnels
```

---

## How to Use the HTTP Tunnel URL

### Step 1: Get the URL

Use any method above. Example URL: `https://abc123.ngrok.io`

### Step 2: Open in Browser

Simply paste the URL in your web browser:
```
https://abc123.ngrok.io
```

### Step 3: Authenticate

You'll see an **HTTP Basic Authentication** prompt:

**Username:** Your configured username (from `secret.env` → `NGROK_HTTP_USERNAME`)
**Password:** Your configured password (from `secret.env` → `NGROK_HTTP_PASSWORD`)

**Example credentials from config:**
```env
NGROK_HTTP_USERNAME=admin
NGROK_HTTP_PASSWORD=your_secure_password
```

### Step 4: Access Your App

After authentication, you'll see:
- **Focus Task Manager** web interface
- Create/edit tasks
- View progress
- Control LED animations
- All features of the local app, but accessible from anywhere!

---

## Configuration

### HTTP Tunnel Settings

Located in `bootmanager/config/secret.env`:

```env
# Ngrok Configuration
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
NGROK_HTTP_USERNAME=admin
NGROK_HTTP_PASSWORD=your_secure_password_here
```

### Security Notes

1. **Always use HTTPS:** Ngrok provides automatic HTTPS encryption
2. **Strong password:** Use a strong password for HTTP Basic Auth
3. **Limited access:** Only share the URL with trusted users
4. **Temporary URL:** Ngrok free tier URLs change on restart (consider paid plan for stable URLs)

### Changing Credentials

1. Edit `config/secret.env`:
   ```bash
   nano ~/focus/bootmanager/config/secret.env
   ```

2. Update username/password:
   ```env
   NGROK_HTTP_USERNAME=myusername
   NGROK_HTTP_PASSWORD=myNewSecurePassword123!
   ```

3. Restart bootmanager:
   ```bash
   sudo systemctl restart bootmanager
   ```

4. New tunnel will use updated credentials

---

## Troubleshooting

### HTTP Tunnel Not Created

**Check console/logs for:**

```
⚠ HTTP tunnel failed to start
```

**Common causes:**

1. **Nginx not installed/running**
   ```bash
   sudo systemctl status nginx
   ```
   Fix: Install nginx via `install.sh`

2. **Frontend/Backend not running**
   ```bash
   tail -50 /var/log/bootmanager.log | grep -E "Frontend|Backend"
   ```
   Fix: Check service logs, may need to build (`npm install` / `pip install`)

3. **Invalid ngrok auth token**
   ```bash
   cat ~/focus/bootmanager/config/secret.env | grep NGROK_AUTHTOKEN
   ```
   Fix: Get valid token from https://dashboard.ngrok.com

4. **Port conflict**
   - If another process is using port 4041 (HTTP tunnel API port)
   - Check: `sudo lsof -i :4041`

### Bootmanager Still Running (Good!)

Even if HTTP tunnel fails, bootmanager **continues running**. This is by design. You still have:
- ✅ Emergency SSH tunnel (for remote access)
- ✅ Local web app (on port 3000)
- ✅ All other services

### Can't Access the URL

**Problem:** URL opens but shows error

**Check:**
1. Is bootmanager still running?
   ```bash
   sudo systemctl status bootmanager
   ```

2. Is nginx running?
   ```bash
   sudo systemctl status nginx
   ```

3. Are frontend/backend healthy?
   - Check Discord notification for service status
   - Or check logs

**Problem:** Authentication fails

**Check credentials:**
```bash
cat ~/focus/bootmanager/config/secret.env | grep NGROK_HTTP
```

Ensure you're using the exact username/password from the config.

### URL Changes Every Reboot

**This is normal** with ngrok free tier. URLs are temporary and change when tunnel restarts.

**Solutions:**
1. Check Discord notification after each boot for new URL
2. Upgrade to ngrok paid plan for stable URLs
3. Use custom domain (requires ngrok paid plan)

---

## API Access

You can also use the HTTP tunnel URL for API calls:

### Example: Get Tasks

```bash
# Replace with your actual URL
curl -u admin:yourpassword https://abc123.ngrok.io/api/tasks
```

### Example: Create Task

```bash
curl -u admin:yourpassword \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"title":"New Task","description":"Task from API"}' \
  https://abc123.ngrok.io/api/tasks
```

### Example: Health Check (no auth required)

```bash
curl https://abc123.ngrok.io/health
```

---

## Ngrok Dashboard

You can also view your tunnels on the ngrok dashboard:

1. Go to: https://dashboard.ngrok.com
2. Login with your ngrok account
3. Navigate to **"Endpoints" → "Active Endpoints"**
4. You'll see both tunnels:
   - SSH tunnel (port 22) - from ngrok-ssh.service
   - HTTP tunnel (port 80) - from bootmanager

---

## Advanced: Webhook Integration

Since you have a public HTTPS URL, you can use it for webhooks:

- GitHub webhooks for CI/CD
- Discord webhooks for notifications
- Third-party service integrations

Example webhook URL:
```
https://abc123.ngrok.io/api/webhooks/github
```

---

## Summary

### Quick Reference

| What | Where | How |
|------|-------|-----|
| **When created** | Step 10.5 of boot | After nginx starts |
| **URL format** | `https://XXXXX.ngrok.io` | Random subdomain (free tier) |
| **Authentication** | HTTP Basic Auth | Username + Password |
| **What's exposed** | Full Focus web app | Frontend + Backend API |
| **Where to find URL** | Discord, logs, console | Check boot notification |
| **Uses port** | 4041 (API), 80 (nginx) | No conflict with SSH tunnel |
| **Is it required?** | No | Bootmanager continues if fails |

### Key Points

✅ HTTP tunnel gives you **remote web access** to your Focus app
✅ It's **protected by password** (HTTP Basic Auth)
✅ It's **created automatically** during boot (if nginx is running)
✅ Failure is **non-fatal** - bootmanager keeps running
✅ URL is shown in **Discord notification** and **logs**
✅ Just **open URL in browser** and enter credentials

---

Need more help? Check:
- `FAILSAFE.md` - Overall failsafe system architecture
- `INSTALL_FAILSAFE_FIX.md` - Installation instructions
- `/var/log/bootmanager.log` - Detailed logs
