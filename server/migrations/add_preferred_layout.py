"""
Migration script to add preferred_layout column to projects table.

This adds support for storing each project's preferred LED layout type.
"""
import sys
import os
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate():
    """Add preferred_layout column to projects table."""
    print("=" * 60)
    print("Adding preferred_layout column to projects")
    print("=" * 60)

    # Connect to database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'database.db')
    print(f"\nDatabase: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if projects table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    if not cursor.fetchone():
        print("❌ Projects table not found. Please run main migrations first.")
        conn.close()
        return

    # Check if column already exists
    cursor.execute("PRAGMA table_info(projects)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'preferred_layout' in columns:
        print("✓ Column 'preferred_layout' already exists. No migration needed.")
        conn.close()
        return

    # Add preferred_layout column
    print("\nAdding preferred_layout column...")
    cursor.execute("ALTER TABLE projects ADD COLUMN preferred_layout TEXT DEFAULT 'single'")

    # Update all existing projects to have 'single' as default
    cursor.execute("UPDATE projects SET preferred_layout = 'single' WHERE preferred_layout IS NULL")

    conn.commit()
    conn.close()

    print("✓ Successfully added preferred_layout column")
    print(f"\n{'=' * 60}")
    print("Migration completed successfully!")
    print(f"{'=' * 60}")


def rollback():
    """Rollback migration."""
    print("Rolling back preferred_layout column addition...")

    response = input("Are you sure you want to remove the preferred_layout column? (yes/no): ")
    if response.lower() != 'yes':
        print("Rollback cancelled.")
        return

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
    # For simplicity, we'll just note this limitation
    print("⚠️  SQLite doesn't support DROP COLUMN.")
    print("   To rollback, you would need to recreate the projects table.")
    print("   This is not implemented to avoid data loss.")

    conn.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback()
    else:
        migrate()
