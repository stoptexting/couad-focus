"""
Seed script for Sprint 2 demo data.

Generates a complete project hierarchy with realistic data:
- 1 Demo Project
- 2 Sprints (Sprint 1: active, Sprint 2: planned)
- Multiple User Stories per sprint with varied priorities
- Multiple Tasks per user story with mixed completion status
"""
import sys
import os
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import Project, Sprint, UserStory, Task


def seed_demo_project():
    """Create demo project with full hierarchy."""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Sprint 2 Demo Data Seeding")
        print("=" * 60)

        # Clear existing data
        print("\nClearing existing data...")
        Task.query.delete()
        UserStory.query.delete()
        Sprint.query.delete()
        Project.query.delete()
        db.session.commit()
        print("✓ Database cleared")

        # Create Demo Project
        print("\nCreating Demo Project...")
        project = Project(
            name="Focus Task Manager - Demo",
            description="Demo project showcasing Sprint 2 hierarchical task management"
        )
        db.session.add(project)
        db.session.flush()
        print(f"✓ Created project: {project.name}")

        # Sprint 1 - Active
        print("\nCreating Sprint 1 (Active)...")
        sprint1 = Sprint(
            name="Sprint 1 - Core Features",
            project_id=project.id,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today() + timedelta(days=7),
            status='active'
        )
        db.session.add(sprint1)
        db.session.flush()
        print(f"✓ Created sprint: {sprint1.name}")

        # Sprint 1 - User Stories
        us1_1 = UserStory(
            title="User Authentication System",
            description="Implement login, registration, and password reset functionality",
            sprint_id=sprint1.id,
            priority='P0',
            status='completed'
        )
        us1_2 = UserStory(
            title="Dashboard Overview",
            description="Create main dashboard with project statistics",
            sprint_id=sprint1.id,
            priority='P0',
            status='in_progress'
        )
        us1_3 = UserStory(
            title="Task CRUD Operations",
            description="Enable create, read, update, delete for tasks",
            sprint_id=sprint1.id,
            priority='P1',
            status='in_progress'
        )
        us1_4 = UserStory(
            title="Progress Visualization",
            description="Display progress bars and gauges for completion tracking",
            sprint_id=sprint1.id,
            priority='P2',
            status='new'
        )

        db.session.add_all([us1_1, us1_2, us1_3, us1_4])
        db.session.flush()
        print(f"✓ Created 4 user stories for Sprint 1")

        # Sprint 1 - Tasks for US 1 (Completed)
        tasks_us1_1 = [
            Task(title="Setup authentication library", user_story_id=us1_1.id, status='completed'),
            Task(title="Create login page UI", user_story_id=us1_1.id, status='completed'),
            Task(title="Implement password hashing", user_story_id=us1_1.id, status='completed'),
            Task(title="Add JWT token generation", user_story_id=us1_1.id, status='completed'),
            Task(title="Write authentication tests", user_story_id=us1_1.id, status='completed')
        ]

        # Sprint 1 - Tasks for US 2 (In Progress)
        tasks_us1_2 = [
            Task(title="Design dashboard layout", user_story_id=us1_2.id, status='completed'),
            Task(title="Fetch project statistics API", user_story_id=us1_2.id, status='completed'),
            Task(title="Create chart components", user_story_id=us1_2.id, status='new'),
            Task(title="Add real-time updates", user_story_id=us1_2.id, status='new')
        ]

        # Sprint 1 - Tasks for US 3 (In Progress)
        tasks_us1_3 = [
            Task(title="Create task model", user_story_id=us1_3.id, status='completed'),
            Task(title="Build task creation form", user_story_id=us1_3.id, status='completed'),
            Task(title="Implement task editing", user_story_id=us1_3.id, status='new'),
            Task(title="Add task deletion with confirmation", user_story_id=us1_3.id, status='new'),
            Task(title="Task validation and error handling", user_story_id=us1_3.id, status='new')
        ]

        # Sprint 1 - Tasks for US 4 (New)
        tasks_us1_4 = [
            Task(title="Research visualization libraries", user_story_id=us1_4.id, status='new'),
            Task(title="Design progress bar component", user_story_id=us1_4.id, status='new'),
            Task(title="Implement LED hardware integration", user_story_id=us1_4.id, status='new')
        ]

        all_tasks_s1 = tasks_us1_1 + tasks_us1_2 + tasks_us1_3 + tasks_us1_4
        db.session.add_all(all_tasks_s1)
        print(f"✓ Created {len(all_tasks_s1)} tasks for Sprint 1")

        # Sprint 2 - Planned
        print("\nCreating Sprint 2 (Planned)...")
        sprint2 = Sprint(
            name="Sprint 2 - Advanced Features",
            project_id=project.id,
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=28),
            status='planned'
        )
        db.session.add(sprint2)
        db.session.flush()
        print(f"✓ Created sprint: {sprint2.name}")

        # Sprint 2 - User Stories
        us2_1 = UserStory(
            title="Hierarchical Project Structure",
            description="Implement Project → Sprint → UserStory → Task hierarchy",
            sprint_id=sprint2.id,
            priority='P0',
            status='new'
        )
        us2_2 = UserStory(
            title="Multi-Zone LED Display",
            description="Support multiple LED zones for different gauges",
            sprint_id=sprint2.id,
            priority='P1',
            status='new'
        )
        us2_3 = UserStory(
            title="Tree Navigation UI",
            description="Build expandable/collapsible project tree interface",
            sprint_id=sprint2.id,
            priority='P1',
            status='new'
        )

        db.session.add_all([us2_1, us2_2, us2_3])
        db.session.flush()
        print(f"✓ Created 3 user stories for Sprint 2")

        # Sprint 2 - Tasks for US 1
        tasks_us2_1 = [
            Task(title="Design database schema", user_story_id=us2_1.id, status='new'),
            Task(title="Create migration scripts", user_story_id=us2_1.id, status='new'),
            Task(title="Build project service layer", user_story_id=us2_1.id, status='new'),
            Task(title="Implement REST API endpoints", user_story_id=us2_1.id, status='new')
        ]

        # Sprint 2 - Tasks for US 2
        tasks_us2_2 = [
            Task(title="Update LED protocol", user_story_id=us2_2.id, status='new'),
            Task(title="Create zone configuration", user_story_id=us2_2.id, status='new'),
            Task(title="Build multi-LED controller", user_story_id=us2_2.id, status='new'),
            Task(title="Test multi-zone updates", user_story_id=us2_2.id, status='new')
        ]

        # Sprint 2 - Tasks for US 3
        tasks_us2_3 = [
            Task(title="Design tree node component", user_story_id=us2_3.id, status='new'),
            Task(title="Implement expand/collapse logic", user_story_id=us2_3.id, status='new'),
            Task(title="Add drag-and-drop support", user_story_id=us2_3.id, status='new'),
            Task(title="Create context menus", user_story_id=us2_3.id, status='new'),
            Task(title="Add keyboard navigation", user_story_id=us2_3.id, status='new')
        ]

        all_tasks_s2 = tasks_us2_1 + tasks_us2_2 + tasks_us2_3
        db.session.add_all(all_tasks_s2)
        print(f"✓ Created {len(all_tasks_s2)} tasks for Sprint 2")

        # Commit all changes
        db.session.commit()

        # Print summary
        total_tasks = len(all_tasks_s1) + len(all_tasks_s2)
        completed_tasks = sum(1 for t in all_tasks_s1 + all_tasks_s2 if t.status == 'completed')

        print(f"\n{'=' * 60}")
        print(f"Demo Data Created Successfully!")
        print(f"{'=' * 60}")
        print(f"Project: {project.name}")
        print(f"  Sprints: 2")
        print(f"    - {sprint1.name} ({sprint1.status})")
        print(f"    - {sprint2.name} ({sprint2.status})")
        print(f"  User Stories: 7 (4 in Sprint 1, 3 in Sprint 2)")
        print(f"  Tasks: {total_tasks} ({completed_tasks} completed, {total_tasks - completed_tasks} pending)")
        print(f"\nOverall Progress: {round(completed_tasks / total_tasks * 100)}%")
        print(f"\nAccess at: /api/projects/{project.id}")


if __name__ == '__main__':
    seed_demo_project()
