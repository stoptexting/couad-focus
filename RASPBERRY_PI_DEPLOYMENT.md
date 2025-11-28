# Sprint 2 Deployment Guide for Raspberry Pi

This guide will help you deploy the Sprint 2 hierarchical task management system to your Raspberry Pi.

## Overview

Sprint 2 introduces a hierarchical structure:
- **Project** → **Sprint** → **UserStory** → **Task**
- Multi-zone LED support
- Full CRUD operations for all entities
- Progress tracking at all levels

## Prerequisites

- Raspberry Pi with Raspbian/Raspberry Pi OS
- Python 3.7+ installed
- Node.js 18+ installed
- Git
- Internet connection (for initial setup)

---

## Part 1: Backup Current System

Before migrating, back up your existing Sprint 1 data:

```bash
# Navigate to the project directory
cd ~/Documents/focus

# Backup the database
cp server/instance/tasks.db server/instance/tasks.db.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -lh server/instance/tasks.db*
```

---

## Part 2: Update Code

### 2.1 Pull Latest Code

If using Git:

```bash
cd ~/Documents/focus
git pull origin main
```

If deploying manually, copy all the updated files to the Raspberry Pi.

### 2.2 Verify File Structure

Ensure you have these key new/updated files:

**Backend (server/):**
- `app/models/project.py` (new)
- `app/models/sprint.py` (new)
- `app/models/user_story.py` (new)
- `app/models/task.py` (updated - has user_story_id)
- `app/services/project_service.py` (new)
- `app/services/sprint_service.py` (new)
- `app/services/user_story_service.py` (new)
- `app/services/progress_calculator.py` (new)
- `app/services/multi_led_controller.py` (new)
- `app/routes/projects.py` (new)
- `app/routes/sprints.py` (new)
- `app/routes/user_stories.py` (new)
- `config.json` (new - LED zones configuration)
- `migrations/migrate_sprint1_to_sprint2.py` (new)

**Frontend (frontend/):**
- `lib/types.ts` (updated - new entity types)
- `lib/api/projects.ts` (new)
- `lib/api/sprints.ts` (new)
- `lib/api/userStories.ts` (new)
- `components/modals/ProjectFormModal.tsx` (new)
- `components/modals/SprintFormModal.tsx` (new)
- `components/modals/UserStoryFormModal.tsx` (new)
- `components/Navigation.tsx` (new)
- `app/projects/page.tsx` (new)
- `app/projects/[id]/page.tsx` (new)

---

## Part 3: Backend Migration

### 3.1 Install Python Dependencies

```bash
cd ~/Documents/focus/server

# Activate virtual environment (if using one)
source venv/bin/activate  # or create one: python3 -m venv venv

# Install any new dependencies
pip3 install -r requirements.txt
```

### 3.2 Run Database Migration

This script will:
- Add new tables (projects, sprints, user_stories)
- Add `user_story_id` column to tasks table
- Migrate existing tasks to the new hierarchy
- Preserve all your existing data

```bash
cd ~/Documents/focus/server

# Set PYTHONPATH to include shared modules
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH

# Run migration
python3 migrations/migrate_sprint1_to_sprint2.py
```

**Expected Output:**
```
============================================================
Sprint 1 → Sprint 2 Migration
============================================================

Database: /home/pi/Documents/focus/server/instance/tasks.db

Found X existing tasks from Sprint 1

Existing tasks:
  ✓ Task name [status]
  ...

Creating new tables...
✓ Added user_story_id column to tasks table

Creating default hierarchy for migration...
✓ Created project: 'Migrated from Sprint 1' (ID: xxx-xxx-xxx)
✓ Created sprint: 'Backlog Sprint' (ID: xxx-xxx-xxx)

Migrating tasks to UserStories...
  ✓ Task 'Task name' → UserStory (ID: xxx-xxx-xxx)
  ...

============================================================
Migration completed successfully!
============================================================
Migrated X tasks
  → Project: Migrated from Sprint 1
  → Sprint: Backlog Sprint
  → User Stories: X
  → Tasks: X

All existing tasks preserved with full hierarchy.
You can now view them at /api/projects/{project_id}
```

### 3.3 Verify Migration

```bash
# Check database schema
sqlite3 server/instance/tasks.db ".schema"

# Should show: tasks, projects, sprints, user_stories tables

# Check data
sqlite3 server/instance/tasks.db "SELECT COUNT(*) FROM projects;"
sqlite3 server/instance/tasks.db "SELECT COUNT(*) FROM sprints;"
sqlite3 server/instance/tasks.db "SELECT COUNT(*) FROM user_stories;"
sqlite3 server/instance/tasks.db "SELECT COUNT(*) FROM tasks;"
```

### 3.4 Configure LED Zones (Optional)

Edit `server/config.json` to configure your LED zones:

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

**Zone Configuration:**
- `start_led` and `end_led`: LED index range for this zone
- `default_color`: RGB array [R, G, B] (0-255)
- Zones can be any size and position
- `fallback_to_single`: If true, uses first zone when multi-zone not available

### 3.5 Test Backend

```bash
cd ~/Documents/focus/server

# Set PYTHONPATH
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH

# Run Flask development server
python3 app.py
```

**Test endpoints:**
```bash
# In another terminal
curl http://localhost:5001/api/projects
curl http://localhost:5001/api/sprints
curl http://localhost:5001/api/user-stories
```

---

## Part 4: Frontend Build & Deployment

### 4.1 Install Frontend Dependencies

```bash
cd ~/Documents/focus/frontend

# Install dependencies
npm install
```

### 4.2 Configure API URL

Verify `frontend/.env.local` points to your Raspberry Pi:

```bash
# For local development
NEXT_PUBLIC_API_URL=http://localhost:5001/api

# For production (use Pi's IP address)
# NEXT_PUBLIC_API_URL=http://192.168.1.XXX:5001/api
```

### 4.3 Build Frontend

```bash
cd ~/Documents/focus/frontend

# Build production bundle
npm run build
```

This will create an optimized production build in `frontend/.next/`

### 4.4 Run Frontend

**Development Mode:**
```bash
npm run dev
# Access at http://raspberry-pi-ip:3000
```

**Production Mode:**
```bash
npm run start
# Access at http://raspberry-pi-ip:3000
```

---

## Part 5: LED Hardware Integration (Optional)

The backend API is ready for multi-zone LED support, but requires daemon updates.

### 5.1 Current LED Status

✅ **Completed:**
- Multi-zone configuration (config.json)
- Multi-LED controller service
- API endpoints for multi-zone updates

⚠️ **Pending (future work):**
- LED protocol SHOW_MULTI_PROGRESS command
- LED daemon multi-zone handler
- LED client show_multi_progress() method

### 5.2 LED Daemon Updates (Future)

When implementing multi-zone support in the LED daemon:

1. Add `SHOW_MULTI_PROGRESS` command to protocol
2. Update daemon to handle zone data
3. Update LED client with `show_multi_progress()` method

**Current Workaround:**
- System works in single-zone mode
- Use existing LED commands
- Multi-zone API endpoints return zone data but won't control hardware yet

---

## Part 6: Systemd Service Setup (Production)

For production deployment, set up systemd services to auto-start.

### 6.1 Backend Service

Create `/etc/systemd/system/focus-backend.service`:

```ini
[Unit]
Description=Focus Task Manager Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Documents/focus/server
Environment="PYTHONPATH=/home/pi/Documents/focus/shared"
ExecStart=/usr/bin/python3 /home/pi/Documents/focus/server/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.2 Frontend Service

Create `/etc/systemd/system/focus-frontend.service`:

```ini
[Unit]
Description=Focus Task Manager Frontend
After=network.target focus-backend.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Documents/focus/frontend
Environment="NEXT_PUBLIC_API_URL=http://localhost:5001/api"
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.3 Enable Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable focus-backend
sudo systemctl enable focus-frontend

# Start services
sudo systemctl start focus-backend
sudo systemctl start focus-frontend

# Check status
sudo systemctl status focus-backend
sudo systemctl status focus-frontend

# View logs
sudo journalctl -u focus-backend -f
sudo journalctl -u focus-frontend -f
```

---

## Part 7: Testing

### 7.1 Backend API Tests

```bash
# Test projects
curl http://localhost:5001/api/projects

# Test creating a project
curl -X POST http://localhost:5001/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "description": "Testing Sprint 2"}'

# Test getting project with full tree (replace {id})
curl http://localhost:5001/api/projects/{id}

# Test progress calculation
curl http://localhost:5001/api/projects/{id}/progress
```

### 7.2 Frontend UI Tests

1. Open browser: `http://raspberry-pi-ip:3000`
2. Verify navigation shows "Projects" link
3. Click "Projects" - should show project list
4. Click "New Project" - modal should open
5. Create a project
6. Click on project - should show detail page
7. Click "Add Sprint" - modal should open
8. Create sprints and user stories
9. Verify progress calculations update

### 7.3 LED Tests (if hardware connected)

```bash
# Test LED zones endpoint
curl http://localhost:5001/api/leds/zones

# Test LED config endpoint
curl http://localhost:5001/api/leds/config

# Test multi-zone update (returns data, hardware control pending)
curl -X POST http://localhost:5001/api/leds/multi-update \
  -H "Content-Type: application/json" \
  -d '[
    {"zone_id": "zone-1", "percentage": 75},
    {"zone_id": "zone-2", "percentage": 50}
  ]'
```

---

## Part 8: Rollback (if needed)

If you need to revert to Sprint 1:

```bash
cd ~/Documents/focus/server

# Rollback migration
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 migrations/migrate_sprint1_to_sprint2.py --rollback

# Or restore from backup
cp server/instance/tasks.db.backup.YYYYMMDD_HHMMSS server/instance/tasks.db
```

---

## Part 9: Seed Demo Data (Optional)

To add demo data for testing:

```bash
cd ~/Documents/focus/server

export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 seed_sprint2.py
```

This creates:
- 1 demo project
- 2 sprints
- 7 user stories
- ~30 tasks

---

## Troubleshooting

### Backend won't start

**Error: ModuleNotFoundError: No module named 'led_manager'**
```bash
# Ensure PYTHONPATH includes shared directory
export PYTHONPATH=/home/pi/Documents/focus/shared:$PYTHONPATH
```

**Error: Database is locked**
```bash
# Stop any running Flask instances
pkill -f "python3 app.py"

# Restart
cd ~/Documents/focus/server
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 app.py
```

### Frontend build fails

**Error: ENOSPC (out of space)**
```bash
# Increase memory for build (on Pi)
export NODE_OPTIONS="--max-old-space-size=2048"
npm run build
```

### Migration fails

**Database already migrated:**
- Migration script checks if tables exist and user_story_id column exists
- Safe to run multiple times

**Want fresh start:**
```bash
# Delete database
rm server/instance/tasks.db

# Run migration (creates fresh database)
cd server
export PYTHONPATH=~/Documents/focus/shared:$PYTHONPATH
python3 migrations/migrate_sprint1_to_sprint2.py
```

### LED zones not working

- Multi-zone hardware control requires LED daemon updates (pending)
- API endpoints work and return zone data
- Single-zone mode still works with existing LED daemon

---

## Next Steps

After deployment:

1. **Verify all data migrated correctly**
   - Check that all Sprint 1 tasks appear under "Migrated from Sprint 1" project

2. **Create new projects**
   - Use the UI to create new projects, sprints, and user stories

3. **Configure LED zones**
   - Edit `server/config.json` to match your LED hardware setup

4. **Monitor system**
   - Check logs: `journalctl -u focus-backend -f`
   - Watch for errors

5. **Future enhancements (optional)**
   - Implement LED daemon multi-zone support
   - Add tree view components
   - Add advanced gauge layouts

---

## Summary

**What's New in Sprint 2:**
- ✅ Hierarchical structure (Project → Sprint → UserStory → Task)
- ✅ Full CRUD for all entities via UI
- ✅ Progress tracking at all levels
- ✅ Multi-zone LED configuration (API ready)
- ✅ Modern UI with modal forms
- ✅ Navigation between projects
- ✅ All Sprint 1 data preserved during migration

**What Works:**
- Backend API (26 endpoints)
- Frontend UI (projects, sprints, user stories)
- Database migration
- Progress calculations
- Single-zone LED control

**What's Pending:**
- Multi-zone LED hardware integration (daemon updates)
- Optional tree view components
- Optional advanced gauge layouts

---

## Support

If you encounter issues:

1. Check logs: `journalctl -u focus-backend -f`
2. Verify database: `sqlite3 server/instance/tasks.db ".schema"`
3. Test API endpoints: `curl http://localhost:5001/api/projects`
4. Check file permissions
5. Verify PYTHONPATH is set correctly

---

## File Checklist

Before deployment, ensure these files exist:

**Backend Core:**
- [ ] `server/app/models/project.py`
- [ ] `server/app/models/sprint.py`
- [ ] `server/app/models/user_story.py`
- [ ] `server/app/services/project_service.py`
- [ ] `server/app/services/sprint_service.py`
- [ ] `server/app/services/user_story_service.py`
- [ ] `server/app/services/progress_calculator.py`
- [ ] `server/app/routes/projects.py`
- [ ] `server/app/routes/sprints.py`
- [ ] `server/app/routes/user_stories.py`
- [ ] `server/config.json`
- [ ] `server/migrations/migrate_sprint1_to_sprint2.py`

**Frontend Core:**
- [ ] `frontend/lib/api/projects.ts`
- [ ] `frontend/lib/api/sprints.ts`
- [ ] `frontend/lib/api/userStories.ts`
- [ ] `frontend/components/modals/ProjectFormModal.tsx`
- [ ] `frontend/components/modals/SprintFormModal.tsx`
- [ ] `frontend/components/modals/UserStoryFormModal.tsx`
- [ ] `frontend/components/Navigation.tsx`
- [ ] `frontend/app/projects/page.tsx`
- [ ] `frontend/app/projects/[id]/page.tsx`

---

**Deployment Date:** ___________
**Deployed By:** ___________
**Migration Successful:** [ ] Yes [ ] No
**Notes:** ___________________________________________
