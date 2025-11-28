# Quick Start - Raspberry Pi Deployment

**Sprint 2 is ready to deploy!** Follow these steps on your Raspberry Pi.

---

## TL;DR - Quick Commands

```bash
# 1. Backup database
cd ~/Documents/focus
cp server/instance/tasks.db server/instance/tasks.db.backup

# 2. Pull code (or copy files manually)
git pull origin main

# 3. Run migration
cd server
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 migrations/migrate_sprint1_to_sprint2.py

# 4. Install frontend deps
cd ~/Documents/focus/frontend
npm install

# 5. Build frontend
npm run build

# 6. Start backend
cd ~/Documents/focus/server
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 app.py &

# 7. Start frontend
cd ~/Documents/focus/frontend
npm run start &

# 8. Access at http://raspberry-pi-ip:3000
```

---

## Detailed Steps

### Step 1: Backup (2 minutes)
```bash
cd ~/Documents/focus
cp server/instance/tasks.db server/instance/tasks.db.backup.$(date +%Y%m%d)
```

### Step 2: Get Code (1 minute)
If using Git:
```bash
git pull origin main
```

If copying manually, transfer all files to `~/Documents/focus/`

### Step 3: Migrate Database (2 minutes)
```bash
cd ~/Documents/focus/server
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 migrations/migrate_sprint1_to_sprint2.py
```

**Expected:** Migration completes successfully, shows count of migrated tasks

### Step 4: Install Frontend Dependencies (5-10 minutes)
```bash
cd ~/Documents/focus/frontend
npm install
```

### Step 5: Build Frontend (5-10 minutes)
```bash
npm run build
```

**Note:** This may take time on Raspberry Pi. If out of memory:
```bash
export NODE_OPTIONS="--max-old-space-size=2048"
npm run build
```

### Step 6: Start Backend (1 minute)
```bash
cd ~/Documents/focus/server
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 app.py
```

**Test:** Open another terminal and run:
```bash
curl http://localhost:5001/api/projects
```

Should return JSON with projects.

### Step 7: Start Frontend (1 minute)
```bash
cd ~/Documents/focus/frontend
npm run start
```

### Step 8: Test
Open browser: `http://your-raspberry-pi-ip:3000`

You should see:
- Navigation with "Projects" link
- Click Projects → see your migrated project
- Click project → see sprints
- Can create new projects, sprints, user stories

---

## LED Configuration (Optional)

Edit `server/config.json` to configure LED zones:

```json
{
  "hardware": {
    "led_zones": [
      {"id": "zone-1", "name": "Sprint 1", "start_led": 0, "end_led": 31},
      {"id": "zone-2", "name": "Sprint 2", "start_led": 32, "end_led": 63}
    ],
    "total_leds": 64
  }
}
```

**Note:** Multi-zone hardware control requires daemon updates (future work). API is ready.

---

## Auto-Start on Boot (Production)

Create systemd services (see RASPBERRY_PI_DEPLOYMENT.md section 6 for details):

```bash
# Create service files
sudo nano /etc/systemd/system/focus-backend.service
sudo nano /etc/systemd/system/focus-frontend.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable focus-backend focus-frontend
sudo systemctl start focus-backend focus-frontend

# Check status
sudo systemctl status focus-backend
sudo systemctl status focus-frontend
```

---

## Troubleshooting

**Backend won't start:**
```bash
# Check PYTHONPATH
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH

# Kill existing processes
pkill -f "python3 app.py"
```

**Frontend build fails (out of memory):**
```bash
export NODE_OPTIONS="--max-old-space-size=2048"
npm run build
```

**Migration fails:**
```bash
# Restore backup
cp server/instance/tasks.db.backup.YYYYMMDD server/instance/tasks.db

# Try again
```

**Want to rollback:**
```bash
cd ~/Documents/focus/server
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 migrations/migrate_sprint1_to_sprint2.py --rollback
```

---

## What's New in Sprint 2

✅ **Hierarchical Structure:**
- Projects contain Sprints
- Sprints contain User Stories
- User Stories contain Tasks

✅ **Full UI:**
- Create/edit projects, sprints, user stories
- View progress at all levels
- Navigate hierarchy
- All Sprint 1 tasks preserved

✅ **Multi-zone LED Config:**
- Configure zones in config.json
- API ready (hardware integration pending)

---

## Files to Check

Required new/updated files:
- `server/app/models/project.py` ✅
- `server/app/models/sprint.py` ✅
- `server/app/models/user_story.py` ✅
- `server/config.json` ✅
- `server/migrations/migrate_sprint1_to_sprint2.py` ✅
- `frontend/app/projects/page.tsx` ✅
- `frontend/components/modals/ProjectFormModal.tsx` ✅

See SPRINT2_IMPLEMENTATION_SUMMARY.md for full file list.

---

## Need More Details?

- **Full deployment guide:** RASPBERRY_PI_DEPLOYMENT.md
- **Implementation details:** SPRINT2_IMPLEMENTATION_SUMMARY.md
- **Original spec:** sprint2.md

---

**Estimated deployment time:** 20-30 minutes
**Your Sprint 1 data will be preserved!**
**Rollback available if needed**

Good luck! 🚀
