"""
Migration script from Sprint 1 to Sprint 2.

This script migrates existing Sprint 1 tasks to the new hierarchical structure:
Project → Sprint → UserStory → Task

Strategy: Full migration - preserve all existing tasks under a default hierarchy.
"""
import sys
import os
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date


def migrate():
    """Execute migration from Sprint 1 to Sprint 2."""
    print("=" * 60)
    print("Sprint 1 → Sprint 2 Migration")
    print("=" * 60)

    # Connect directly to database to avoid model schema issues
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'tasks.db')
    print(f"\nDatabase: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Check if migration is needed
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    if not cursor.fetchone():
        print("No tasks table found. Creating fresh Sprint 2 database...")
        conn.close()

        # Import here to create tables
        from app import create_app
        from app.extensions import db
        app = create_app()
        with app.app_context():
            db.create_all()
        print("✓ Database tables created successfully")
        return

    # Step 2: Get existing tasks
    cursor.execute("SELECT id, title, description, status, created_at, updated_at FROM tasks")
    existing_tasks = cursor.fetchall()
    print(f"\nFound {len(existing_tasks)} existing tasks from Sprint 1")

    if len(existing_tasks) == 0:
        print("No tasks to migrate.")

        # Just ensure all new tables exist
        cursor.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, created_at TIMESTAMP NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS sprints (id TEXT PRIMARY KEY, name TEXT NOT NULL, project_id TEXT NOT NULL, start_date DATE, end_date DATE, status TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS user_stories (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT, sprint_id TEXT NOT NULL, priority TEXT NOT NULL, status TEXT NOT NULL, FOREIGN KEY(sprint_id) REFERENCES sprints(id) ON DELETE CASCADE)")

        # Add user_story_id column if it doesn't exist
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'user_story_id' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN user_story_id TEXT REFERENCES user_stories(id) ON DELETE CASCADE")
            print("✓ Added user_story_id column to tasks table")

        conn.commit()
        conn.close()
        print("✓ Database schema updated")
        return

    # Step 3: Show existing tasks
    print("\nExisting tasks:")
    for task in existing_tasks:
        task_id, title, desc, status, created, updated = task
        status_symbol = "✓" if status == "completed" else "○"
        print(f"  {status_symbol} {title} [{status}]")

    # Step 4: Create new tables
    print("\nCreating new tables...")
    cursor.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, created_at TIMESTAMP NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS sprints (id TEXT PRIMARY KEY, name TEXT NOT NULL, project_id TEXT NOT NULL, start_date DATE, end_date DATE, status TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_stories (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT, sprint_id TEXT NOT NULL, priority TEXT NOT NULL, status TEXT NOT NULL, FOREIGN KEY(sprint_id) REFERENCES sprints(id) ON DELETE CASCADE)")

    # Add user_story_id column to tasks
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'user_story_id' not in columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN user_story_id TEXT REFERENCES user_stories(id) ON DELETE CASCADE")
        print("✓ Added user_story_id column to tasks table")

    # Step 5: Create default hierarchy
    print("\nCreating default hierarchy for migration...")

    import uuid
    from datetime import datetime

    # Create default Project
    project_id = str(uuid.uuid4())
    project_name = "Migrated from Sprint 1"
    cursor.execute(
        "INSERT INTO projects (id, name, description, created_at) VALUES (?, ?, ?, ?)",
        (project_id, project_name, "Legacy tasks migrated from Sprint 1 simple structure", datetime.utcnow())
    )
    print(f"✓ Created project: '{project_name}' (ID: {project_id})")

    # Create default Sprint
    sprint_id = str(uuid.uuid4())
    sprint_name = "Backlog Sprint"
    cursor.execute(
        "INSERT INTO sprints (id, name, project_id, start_date, status) VALUES (?, ?, ?, ?, ?)",
        (sprint_id, sprint_name, project_id, date.today(), 'active')
    )
    print(f"✓ Created sprint: '{sprint_name}' (ID: {sprint_id})")

    # Step 6: Migrate tasks to UserStories
    print("\nMigrating tasks to UserStories...")
    migrated_count = 0

    for task in existing_tasks:
        task_id, title, desc, status, created, updated = task

        # Create UserStory for this task
        user_story_id = str(uuid.uuid4())
        us_title = f"US: {title}"
        us_desc = f"Migrated from Sprint 1 task\n\nOriginal task: {desc or '(no description)'}"
        us_status = 'completed' if status == 'completed' else 'in_progress'

        cursor.execute(
            "INSERT INTO user_stories (id, title, description, sprint_id, priority, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user_story_id, us_title, us_desc, sprint_id, 'P2', us_status)
        )

        # Link task to UserStory
        cursor.execute(
            "UPDATE tasks SET user_story_id = ? WHERE id = ?",
            (user_story_id, task_id)
        )

        migrated_count += 1
        print(f"  ✓ Task '{title}' → UserStory (ID: {user_story_id})")

    # Commit all changes
    conn.commit()
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"Migration completed successfully!")
    print(f"{'=' * 60}")
    print(f"Migrated {migrated_count} tasks")
    print(f"  → Project: {project_name}")
    print(f"  → Sprint: {sprint_name}")
    print(f"  → User Stories: {migrated_count}")
    print(f"  → Tasks: {migrated_count}")
    print(f"\nAll existing tasks preserved with full hierarchy.")
    print(f"You can now view them at /api/projects/{project_id}")


def rollback():
    """Rollback migration (for testing)."""
    print("Rolling back migration...")
    print("WARNING: This will delete all migrated data!")

    response = input("Are you sure? (yes/no): ")
    if response.lower() != 'yes':
        print("Rollback cancelled.")
        return

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'tasks.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Remove user_story_id links from tasks
    cursor.execute("UPDATE tasks SET user_story_id = NULL")

    # Delete all new entities
    cursor.execute("DELETE FROM user_stories")
    cursor.execute("DELETE FROM sprints")
    cursor.execute("DELETE FROM projects")

    conn.commit()
    conn.close()
    print("✓ Rollback complete. Back to Sprint 1 structure.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback()
    else:
        migrate()
