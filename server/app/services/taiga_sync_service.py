"""Taiga sync service for synchronizing Taiga data to local database."""
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple, List

from app.extensions import db
from app.models import Project, Sprint, UserStory, Task, TaigaConfig
from app.services.taiga_client import (
    TaigaClient,
    TaigaAuthError,
    TaigaClientError,
    TaigaNotFoundError,
    TaigaPermissionError
)

logger = logging.getLogger(__name__)


class TaigaSyncService:
    """Service for synchronizing Taiga data to local database."""

    def __init__(self):
        """Initialize sync service."""
        self.client: Optional[TaigaClient] = None

    def get_config(self) -> Optional[TaigaConfig]:
        """Get the current Taiga configuration."""
        return TaigaConfig.query.first()

    def get_or_create_config(self) -> TaigaConfig:
        """Get existing config or create a new one."""
        config = TaigaConfig.query.first()
        if not config:
            config = TaigaConfig()
            db.session.add(config)
            db.session.commit()
        return config

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Taiga and store the token.

        Args:
            username: Taiga username
            password: Taiga password

        Returns:
            Dict with login result

        Raises:
            TaigaAuthError: Invalid credentials
        """
        config = self.get_or_create_config()

        # Create client with configured base URL
        self.client = TaigaClient(base_url=config.base_url)

        # Authenticate
        auth_result = self.client.authenticate(username, password)

        # Store authentication state
        config.username = username
        config.taiga_user_id = auth_result.get('id')
        config.user_email = auth_result.get('email')
        config.auth_token = auth_result['auth_token']
        config.token_obtained_at = datetime.utcnow()
        config.sync_status = 'authenticated'
        config.last_error = None

        db.session.commit()

        logger.info(f"Taiga login successful for user: {username} (ID: {config.taiga_user_id})")

        return {
            'success': True,
            'username': auth_result.get('username', username),
            'full_name': auth_result.get('full_name', ''),
            'user_id': config.taiga_user_id,
            'message': 'Login successful'
        }

    def logout(self) -> Dict[str, Any]:
        """
        Clear Taiga authentication and project configuration.

        Returns:
            Dict with logout result
        """
        config = self.get_config()
        if config:
            config.username = None
            config.taiga_user_id = None
            config.user_email = None
            config.auth_token = None
            config.token_obtained_at = None
            config.project_url = None
            config.project_slug = None
            config.taiga_project_id = None
            config.local_project_id = None
            config.sync_status = 'not_configured'
            config.last_error = None
            db.session.commit()

        logger.info("Taiga logout completed")

        return {
            'success': True,
            'message': 'Logged out successfully'
        }

    def set_project(self, project_url: str) -> Dict[str, Any]:
        """
        Set the Taiga project to sync from.

        Args:
            project_url: Full Taiga project URL

        Returns:
            Dict with project info

        Raises:
            ValueError: Invalid URL format
            TaigaAuthError: Not authenticated
        """
        config = self.get_config()
        if not config or not config.auth_token:
            raise TaigaAuthError('Not authenticated. Please login first.')

        # Normalize URL to ensure proper https:// scheme
        project_url = self._normalize_url(project_url)

        # Parse project slug from URL
        slug = TaigaClient.parse_project_url(project_url)
        if not slug:
            raise ValueError('Invalid Taiga project URL format')

        # Setup client with token
        self._ensure_client(config)

        # Fetch project to verify access
        project_info = self.client.get_project_by_slug(slug)

        # Update config
        config.project_url = project_url
        config.project_slug = slug
        config.taiga_project_id = project_info['id']
        config.last_error = None

        db.session.commit()

        logger.info(f"Taiga project set: {project_info['name']} (slug: {slug})")

        return {
            'success': True,
            'project_name': project_info['name'],
            'project_slug': slug,
            'taiga_project_id': project_info['id'],
            'message': f"Connected to project: {project_info['name']}"
        }

    def disconnect_project(self) -> Dict[str, Any]:
        """
        Disconnect from current project (keeps auth).

        Returns:
            Dict with result
        """
        config = self.get_config()
        if config:
            config.project_url = None
            config.project_slug = None
            config.taiga_project_id = None
            config.local_project_id = None
            config.last_sync_at = None
            config.sync_status = 'authenticated' if config.auth_token else 'not_configured'
            config.last_error = None
            db.session.commit()

        return {
            'success': True,
            'message': 'Project disconnected'
        }

    def sync(self) -> Dict[str, Any]:
        """
        Perform full synchronization of project hierarchy from Taiga.

        Returns:
            Dict with sync summary

        Raises:
            TaigaAuthError: Not authenticated
            ValueError: No project configured
        """
        config = self.get_config()
        if not config or not config.auth_token:
            raise TaigaAuthError('Not authenticated. Please login first.')

        if not config.taiga_project_id:
            raise ValueError('No project configured. Please set a project first.')

        # Setup client
        self._ensure_client(config)

        # Update status
        config.sync_status = 'syncing'
        db.session.commit()

        try:
            # Fetch all data from Taiga
            logger.info(f"Starting sync for Taiga project {config.taiga_project_id}")

            project_data = self.client.get_project(config.taiga_project_id)
            milestones = self.client.get_milestones(config.taiga_project_id)
            user_stories = self.client.get_user_stories(config.taiga_project_id)
            tasks = self.client.get_tasks(config.taiga_project_id)

            # Debug logging for task sync investigation
            logger.info(f"Fetched {len(tasks)} tasks from Taiga")
            if tasks:
                sample_task = tasks[0]
                logger.info(f"Sample task keys: {list(sample_task.keys())}")
                logger.info(f"Sample task user_story field: {sample_task.get('user_story')}")
                logger.info(f"Sample task user_story_id field: {sample_task.get('user_story_id')}")

            # Sync to local database
            summary = self._sync_to_database(
                project_data=project_data,
                milestones=milestones,
                user_stories=user_stories,
                tasks=tasks,
                config=config
            )

            # Update config
            config.sync_status = 'synced'
            config.last_sync_at = datetime.utcnow()
            config.last_error = None
            db.session.commit()

            logger.info(f"Sync completed: {summary}")

            return {
                'success': True,
                'summary': summary,
                'last_sync_at': config.last_sync_at.isoformat()
            }

        except Exception as e:
            config.sync_status = 'error'
            config.last_error = str(e)[:500]
            db.session.commit()
            logger.error(f"Sync failed: {e}")
            raise

    def get_tree(self) -> Dict[str, Any]:
        """
        Get the project tree with progress for the frontend.

        Returns:
            Dict with full project hierarchy and progress
        """
        config = self.get_config()
        if not config or not config.local_project_id:
            return {
                'project': None,
                'sprints': [],
                'has_data': False
            }

        project = Project.query.get(config.local_project_id)
        if not project:
            return {
                'project': None,
                'sprints': [],
                'has_data': False
            }

        # Build the tree with progress
        sprints_data = []
        for sprint in project.sprints.order_by(Sprint.start_date.asc().nullslast()):
            if sprint.name == 'Backlog':
                continue  # Skip backlog sprint
            sprint_dict = sprint.to_dict(include_user_stories=True, include_progress=True)
            sprints_data.append(sprint_dict)

        return {
            'project': project.to_dict(include_sprints=False, include_progress=True),
            'sprints': sprints_data,
            'has_data': True,
            'last_sync_at': config.last_sync_at.isoformat() if config.last_sync_at else None
        }

    def _ensure_client(self, config: TaigaConfig) -> None:
        """Ensure client is initialized with auth token."""
        if not self.client:
            self.client = TaigaClient(base_url=config.base_url)

        if config.auth_token:
            self.client.set_auth_token(config.auth_token)

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL to ensure proper https:// scheme.

        Fixes URLs like 'https//example.com' (missing colon) to 'https://example.com'.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL with proper scheme
        """
        if not url:
            return url

        # Already has proper scheme
        if url.startswith('https://') or url.startswith('http://'):
            return url

        # Fix missing colon after https
        if url.startswith('https//'):
            return 'https://' + url[7:]

        # Fix missing colon after http
        if url.startswith('http//'):
            return 'http://' + url[6:]

        # Default: prepend https://
        return 'https://' + url

    def _sync_to_database(
        self,
        project_data: Dict,
        milestones: List[Dict],
        user_stories: List[Dict],
        tasks: List[Dict],
        config: TaigaConfig
    ) -> Dict[str, Any]:
        """
        Map and upsert Taiga data to local models.

        Returns:
            Summary of sync operations
        """
        summary = {
            'project_synced': False,
            'sprints_created': 0,
            'sprints_updated': 0,
            'user_stories_created': 0,
            'user_stories_updated': 0,
            'tasks_created': 0,
            'tasks_updated': 0
        }

        # Sync Project
        local_project = self._upsert_project(project_data)
        config.local_project_id = local_project.id
        summary['project_synced'] = True

        # Build milestone ID -> local Sprint ID map
        sprint_map: Dict[int, str] = {}
        for milestone in milestones:
            sprint, created = self._upsert_sprint(milestone, local_project.id)
            sprint_map[milestone['id']] = sprint.id
            if created:
                summary['sprints_created'] += 1
            else:
                summary['sprints_updated'] += 1

        # Create a backlog sprint for unassigned stories
        backlog_sprint_id = self._get_backlog_sprint_id(local_project.id)

        # Build user story ID -> local UserStory ID map
        us_map: Dict[int, str] = {}
        for us in user_stories:
            # User stories without milestone go to backlog
            milestone_id = us.get('milestone')
            sprint_id = sprint_map.get(milestone_id, backlog_sprint_id) if milestone_id else backlog_sprint_id

            local_us, created = self._upsert_user_story(us, sprint_id)
            us_map[us['id']] = local_us.id
            if created:
                summary['user_stories_created'] += 1
            else:
                summary['user_stories_updated'] += 1

        # Sync tasks
        tasks_skipped = 0
        for task in tasks:
            taiga_us_id = self._extract_user_story_id(task)
            local_us_id = us_map.get(taiga_us_id) if taiga_us_id else None
            if local_us_id:
                _, created = self._upsert_task(task, local_us_id)
                if created:
                    summary['tasks_created'] += 1
                else:
                    summary['tasks_updated'] += 1
            else:
                tasks_skipped += 1
                logger.debug(f"Skipped task {task.get('id')}: user_story={task.get('user_story')}")

        if tasks_skipped > 0:
            logger.info(f"Skipped {tasks_skipped} tasks not linked to synced user stories")

        db.session.commit()
        return summary

    def _upsert_project(self, data: Dict) -> Project:
        """Create or update project from Taiga data."""
        project = Project.query.filter_by(taiga_id=data['id']).first()

        if not project:
            project = Project(
                name=data['name'],
                description=(data.get('description') or '')[:500],
                taiga_id=data['id'],
                taiga_slug=data.get('slug')
            )
            db.session.add(project)
            db.session.flush()
            logger.info(f"Created project: {project.name}")
        else:
            project.name = data['name']
            project.description = (data.get('description') or '')[:500]
            project.taiga_slug = data.get('slug')
            logger.info(f"Updated project: {project.name}")

        return project

    def _upsert_sprint(self, data: Dict, project_id: str) -> Tuple[Sprint, bool]:
        """Create or update sprint from Taiga milestone data."""
        sprint = Sprint.query.filter_by(taiga_id=data['id']).first()
        created = False

        if not sprint:
            sprint = Sprint(
                name=data['name'],
                project_id=project_id,
                taiga_id=data['id']
            )
            db.session.add(sprint)
            created = True

        sprint.name = data['name']
        sprint.project_id = project_id
        sprint.start_date = self._parse_date(data.get('estimated_start'))
        sprint.end_date = self._parse_date(data.get('estimated_finish'))
        sprint.status = 'completed' if data.get('closed', False) else 'active'

        db.session.flush()
        return sprint, created

    def _upsert_user_story(self, data: Dict, sprint_id: str) -> Tuple[UserStory, bool]:
        """Create or update user story from Taiga data."""
        us = UserStory.query.filter_by(taiga_id=data['id']).first()
        created = False

        if not us:
            us = UserStory(
                title=data['subject'][:200],
                sprint_id=sprint_id,
                taiga_id=data['id'],
                taiga_ref=data.get('ref')
            )
            db.session.add(us)
            created = True

        us.title = data['subject'][:200]
        us.description = (data.get('description') or '')[:1000] if data.get('description') else None
        us.sprint_id = sprint_id
        us.status = 'completed' if data.get('is_closed', False) else 'in_progress'
        us.priority = self._map_priority(data.get('total_points'))
        us.taiga_ref = data.get('ref')

        db.session.flush()
        return us, created

    def _upsert_task(self, data: Dict, user_story_id: str) -> Tuple[Task, bool]:
        """Create or update task from Taiga data."""
        task = Task.query.filter_by(taiga_id=data['id']).first()
        created = False

        if not task:
            task = Task(
                title=data['subject'][:100],
                user_story_id=user_story_id,
                taiga_id=data['id'],
                taiga_ref=data.get('ref')
            )
            db.session.add(task)
            created = True

        task.title = data['subject'][:100]
        task.description = (data.get('description') or '')[:500] if data.get('description') else None
        task.user_story_id = user_story_id
        task.status = 'completed' if data.get('is_closed', False) else 'new'
        task.taiga_ref = data.get('ref')

        db.session.flush()
        return task, created

    def _get_backlog_sprint_id(self, project_id: str) -> str:
        """Get or create a 'Backlog' sprint for unassigned stories."""
        backlog = Sprint.query.filter_by(
            project_id=project_id,
            name='Backlog'
        ).first()

        if not backlog:
            backlog = Sprint(
                name='Backlog',
                project_id=project_id,
                status='active'
            )
            db.session.add(backlog)
            db.session.flush()

        return backlog.id

    def _map_priority(self, total_points: Optional[float]) -> str:
        """Map Taiga story points to priority."""
        if total_points is None:
            return 'P2'
        if total_points >= 8:
            return 'P0'
        if total_points >= 3:
            return 'P1'
        return 'P2'

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string from Taiga."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except (ValueError, AttributeError):
            return None

    def _extract_user_story_id(self, task: Dict) -> Optional[int]:
        """
        Extract user story ID from task data, handling different API formats.

        The Taiga API may return user story reference in different formats:
        - Integer: task['user_story'] = 123
        - Nested object: task['user_story'] = {'id': 123, ...}
        - Alternative field: task['user_story_id'] = 123
        - None: task has no user story

        Args:
            task: Task data dict from Taiga API

        Returns:
            User story ID as integer, or None if not linked
        """
        # Try 'user_story' field first (most common)
        us_ref = task.get('user_story')

        if us_ref is None:
            # Try alternative field name
            us_ref = task.get('user_story_id')

        if us_ref is None:
            return None

        # Handle integer ID (expected format)
        if isinstance(us_ref, int):
            return us_ref

        # Handle nested object format
        if isinstance(us_ref, dict):
            return us_ref.get('id')

        # Handle string ID (unlikely but possible)
        if isinstance(us_ref, str) and us_ref.isdigit():
            return int(us_ref)

        return None

    def get_my_projects(self) -> Dict[str, Any]:
        """
        Get all projects the user is a member of.

        Returns:
            Dict with list of projects
        """
        config = self.get_config()
        if not config or not config.auth_token or not config.taiga_user_id:
            raise TaigaAuthError('Not authenticated. Please login first.')

        self._ensure_client(config)

        projects = self.client.get_my_projects(config.taiga_user_id)

        # Simplify the project data for frontend
        # Normalize base URL to ensure proper https:// scheme
        base_url = self._normalize_url(config.base_url.replace('/api/v1', ''))

        return {
            'success': True,
            'projects': [
                {
                    'id': p['id'],
                    'name': p['name'],
                    'slug': p['slug'],
                    'is_private': p.get('is_private', False),
                    'description': p.get('description', '')[:200] if p.get('description') else '',
                    'url': f"{base_url}/project/{p['slug']}/"
                }
                for p in projects
            ]
        }

    def get_pending_memberships(self) -> Dict[str, Any]:
        """
        Get user's pending membership invitations and requests.

        Returns:
            Dict with invitations and requests
        """
        config = self.get_config()
        if not config or not config.auth_token or not config.taiga_user_id:
            raise TaigaAuthError('Not authenticated. Please login first.')

        self._ensure_client(config)

        # Get invitations
        invitations = self.client.get_membership_invitations(config.taiga_user_id)

        # Get pending membership requests (if supported)
        try:
            requests_list = self.client.get_my_membership_requests(config.taiga_user_id)
        except Exception:
            requests_list = []

        return {
            'success': True,
            'invitations': [
                {
                    'id': inv.get('id'),
                    'project_name': inv.get('project_name', 'Unknown'),
                    'project_slug': inv.get('project_slug'),
                    'role_name': inv.get('role_name', 'Member'),
                    'created_date': inv.get('created_date')
                }
                for inv in invitations
            ],
            'requests': [
                {
                    'id': req.get('id'),
                    'project_name': req.get('project_name', 'Unknown'),
                    'project_slug': req.get('project_slug'),
                    'status': req.get('status', 'pending'),
                    'created_date': req.get('created_date')
                }
                for req in requests_list
            ]
        }

    def accept_invitation(self, invitation_id: int) -> Dict[str, Any]:
        """
        Accept a membership invitation.

        Args:
            invitation_id: ID of invitation to accept

        Returns:
            Dict with result
        """
        config = self.get_config()
        if not config or not config.auth_token:
            raise TaigaAuthError('Not authenticated. Please login first.')

        self._ensure_client(config)
        self.client.accept_invitation(invitation_id)

        return {
            'success': True,
            'message': 'Invitation accepted'
        }

    def join_project_by_slug(self, slug: str) -> Dict[str, Any]:
        """
        Try to access a project by slug. If user isn't a member,
        return info about whether they can join.

        Args:
            slug: Project slug from URL

        Returns:
            Dict with project info and membership status
        """
        config = self.get_config()
        if not config or not config.auth_token:
            raise TaigaAuthError('Not authenticated. Please login first.')

        self._ensure_client(config)

        # First try to get project info
        try:
            project = self.client.get_project_by_slug(slug)
            # User has access
            return {
                'success': True,
                'has_access': True,
                'project': {
                    'id': project['id'],
                    'name': project['name'],
                    'slug': project['slug'],
                    'is_private': project.get('is_private', False)
                }
            }
        except TaigaNotFoundError:
            # Project doesn't exist or user has no access
            return {
                'success': True,
                'has_access': False,
                'error': 'Project not found or you do not have access',
                'can_request': True  # User can try to request membership
            }
        except TaigaPermissionError:
            # User doesn't have permission - private project
            return {
                'success': True,
                'has_access': False,
                'error': 'This is a private project. You need to request access.',
                'can_request': True
            }
