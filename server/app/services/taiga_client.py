"""Taiga API client for communicating with Taiga project management."""
import re
import requests
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class TaigaClientError(Exception):
    """Base exception for Taiga client errors."""
    pass


class TaigaAuthError(TaigaClientError):
    """Authentication failed or token expired."""
    pass


class TaigaPermissionError(TaigaClientError):
    """Insufficient permissions to access resource."""
    pass


class TaigaRateLimitError(TaigaClientError):
    """Rate limit exceeded."""
    pass


class TaigaNotFoundError(TaigaClientError):
    """Resource not found."""
    pass


class TaigaClient:
    """HTTP client for Taiga API communication."""

    DEFAULT_BASE_URL = 'https://taiga.imt-atlantique.fr/api/v1'

    def __init__(self, base_url: str = None):
        """
        Initialize Taiga client.

        Args:
            base_url: Taiga API base URL (defaults to IMT Atlantique instance)
        """
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.auth_token: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def set_auth_token(self, token: str) -> None:
        """
        Set authentication token for API calls.

        Args:
            token: Taiga auth token from login
        """
        self.auth_token = token
        self.session.headers['Authorization'] = f'Bearer {token}'

    def clear_auth_token(self) -> None:
        """Clear authentication token."""
        self.auth_token = None
        self.session.headers.pop('Authorization', None)

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Taiga and obtain auth token.

        POST /api/v1/auth

        Args:
            username: Taiga username or email
            password: Taiga password

        Returns:
            Dict with auth_token, id, username, full_name, etc.

        Raises:
            TaigaAuthError: Invalid credentials
        """
        try:
            response = self.session.post(
                f'{self.base_url}/auth',
                json={
                    'type': 'normal',
                    'username': username,
                    'password': password
                },
                timeout=30
            )

            if response.status_code == 400:
                error_detail = response.json().get('_error_message', 'Invalid credentials')
                raise TaigaAuthError(f'Authentication failed: {error_detail}')

            response.raise_for_status()
            data = response.json()

            # Set the token for subsequent requests
            self.set_auth_token(data['auth_token'])
            logger.info(f"Authenticated as {data.get('username', username)}")

            return data

        except requests.exceptions.Timeout:
            raise TaigaClientError('Connection to Taiga timed out')
        except requests.exceptions.ConnectionError:
            raise TaigaClientError('Cannot connect to Taiga server')
        except TaigaAuthError:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise TaigaClientError(f'Authentication failed: {str(e)}')

    def get_project_by_slug(self, slug: str) -> Dict[str, Any]:
        """
        Get project details by slug.

        GET /api/v1/projects/by_slug?slug={slug}

        Args:
            slug: Project slug from URL

        Returns:
            Project data dict

        Raises:
            TaigaNotFoundError: Project not found
            TaigaPermissionError: No access to project
        """
        response = self._request('GET', '/projects/by_slug', params={'slug': slug})
        return response.json()

    def get_project(self, project_id: int) -> Dict[str, Any]:
        """
        Get project details by ID.

        GET /api/v1/projects/{id}

        Args:
            project_id: Taiga project ID

        Returns:
            Project data dict
        """
        response = self._request('GET', f'/projects/{project_id}')
        return response.json()

    def get_milestones(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all sprints/milestones for a project.

        GET /api/v1/milestones?project={id}

        Args:
            project_id: Taiga project ID

        Returns:
            List of milestone dicts
        """
        return self._request_paginated('/milestones', params={'project': project_id})

    def get_user_stories(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all user stories for a project.

        GET /api/v1/userstories?project={id}

        Args:
            project_id: Taiga project ID

        Returns:
            List of user story dicts
        """
        return self._request_paginated('/userstories', params={'project': project_id})

    def get_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all tasks for a project.

        GET /api/v1/tasks?project={id}

        Args:
            project_id: Taiga project ID

        Returns:
            List of task dicts
        """
        return self._request_paginated('/tasks', params={'project': project_id})

    def get_my_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all projects the user is a member of.

        GET /api/v1/projects?member={user_id}

        Args:
            user_id: Taiga user ID

        Returns:
            List of project dicts
        """
        response = self._request('GET', '/projects', params={'member': user_id})
        return response.json()

    def get_memberships(self, project_id: int = None, user_id: int = None) -> List[Dict[str, Any]]:
        """
        Get memberships filtered by project or user.

        GET /api/v1/memberships?project={id} or ?user={id}

        Args:
            project_id: Filter by project ID
            user_id: Filter by user ID

        Returns:
            List of membership dicts
        """
        params = {}
        if project_id:
            params['project'] = project_id
        if user_id:
            params['user'] = user_id
        response = self._request('GET', '/memberships', params=params)
        return response.json()

    def get_membership_invitations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get pending membership invitations for a user.

        GET /api/v1/invitations?user={id}

        Args:
            user_id: Taiga user ID

        Returns:
            List of invitation dicts
        """
        try:
            response = self._request('GET', '/invitations', params={'user': user_id})
            return response.json()
        except TaigaNotFoundError:
            return []

    def create_membership(self, project_id: int, role_id: int, user_email: str) -> Dict[str, Any]:
        """
        Create a membership (join project).

        POST /api/v1/memberships

        Args:
            project_id: Project to join
            role_id: Role ID in the project
            user_email: Email of user to add

        Returns:
            Created membership dict
        """
        response = self._request('POST', '/memberships', json={
            'project': project_id,
            'role': role_id,
            'email': user_email
        })
        return response.json()

    def accept_invitation(self, invitation_id: int) -> Dict[str, Any]:
        """
        Accept a membership invitation.

        POST /api/v1/invitations/{id}/accept

        Args:
            invitation_id: Invitation ID

        Returns:
            Result dict
        """
        response = self._request('POST', f'/invitations/{invitation_id}/accept')
        return response.json()

    def request_membership(self, project_id: int, reason: str = '') -> Dict[str, Any]:
        """
        Request to join a project (for private projects).

        POST /api/v1/membership-requests

        Args:
            project_id: Project to request access to
            reason: Optional reason for joining

        Returns:
            Membership request dict
        """
        response = self._request('POST', '/membership-requests', json={
            'project': project_id,
            'reason': reason
        })
        return response.json()

    def get_my_membership_requests(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's pending membership requests.

        GET /api/v1/membership-requests?user={id}

        Args:
            user_id: User ID

        Returns:
            List of membership request dicts
        """
        try:
            response = self._request('GET', '/membership-requests', params={'user': user_id})
            return response.json()
        except TaigaNotFoundError:
            return []

    def get_project_by_slug_public(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Try to get project info by slug, handling permission errors gracefully.

        Returns None if user doesn't have access (useful for checking before join).

        Args:
            slug: Project slug

        Returns:
            Project dict or None if not accessible
        """
        try:
            return self.get_project_by_slug(slug)
        except (TaigaNotFoundError, TaigaPermissionError):
            return None

    def _request_paginated(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        page_size: int = 100,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Make paginated GET request and return all results.

        Taiga API uses X-Pagination-Count header to indicate total items.
        This method fetches all pages and combines the results.

        Args:
            endpoint: API endpoint path
            params: Query parameters (excluding pagination params)
            page_size: Number of items per page (max 100 recommended)
            timeout: Request timeout in seconds

        Returns:
            Combined list of all items from all pages
        """
        all_results = []
        page = 1

        params = params.copy() if params else {}
        params['page_size'] = page_size

        while True:
            params['page'] = page
            response = self._request('GET', endpoint, params=params, timeout=timeout)

            data = response.json()
            if not isinstance(data, list):
                # Single object response, not paginated
                return [data] if data else []

            all_results.extend(data)

            # Check pagination headers
            total_count = response.headers.get('X-Pagination-Count')
            if total_count:
                total_count = int(total_count)
                if len(all_results) >= total_count:
                    break

            # If we got fewer items than page_size, we're on the last page
            if len(data) < page_size:
                break

            page += 1

            # Safety limit to prevent infinite loops
            if page > 100:
                logger.warning(f"Pagination safety limit reached for {endpoint}")
                break

        logger.debug(f"Fetched {len(all_results)} items from {endpoint} ({page} pages)")
        return all_results

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        timeout: int = 30
    ) -> requests.Response:
        """
        Make authenticated API request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            TaigaAuthError: Token invalid or expired
            TaigaPermissionError: Insufficient permissions
            TaigaNotFoundError: Resource not found
            TaigaRateLimitError: Rate limit exceeded
            TaigaClientError: Other errors
        """
        if not self.auth_token:
            raise TaigaAuthError('No authentication token set. Please login first.')

        url = f'{self.base_url}{endpoint}'

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json,
                timeout=timeout
            )

            if response.status_code == 401:
                raise TaigaAuthError('Authentication token expired or invalid. Please login again.')
            elif response.status_code == 403:
                raise TaigaPermissionError(
                    'Permission denied. Make sure your account has access to this project.'
                )
            elif response.status_code == 404:
                raise TaigaNotFoundError('Resource not found. Please check the project URL.')
            elif response.status_code == 429:
                raise TaigaRateLimitError('Rate limit exceeded. Please try again later.')

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            raise TaigaClientError('Request to Taiga timed out')
        except requests.exceptions.ConnectionError:
            raise TaigaClientError('Cannot connect to Taiga server')
        except (TaigaAuthError, TaigaPermissionError, TaigaNotFoundError, TaigaRateLimitError):
            raise
        except Exception as e:
            logger.error(f"Taiga API error: {e}")
            raise TaigaClientError(f'API request failed: {str(e)}')

    @staticmethod
    def parse_project_url(url: str) -> Optional[str]:
        """
        Extract project slug from Taiga project URL.

        Examples:
            https://taiga.imt-atlantique.fr/project/my-project-slug/ -> my-project-slug
            https://taiga.imt-atlantique.fr/project/my-project-slug/backlog -> my-project-slug
            https://taiga.imt-atlantique.fr/project/my-project-slug/kanban -> my-project-slug

        Args:
            url: Full Taiga project URL

        Returns:
            Project slug or None if URL format is invalid
        """
        if not url:
            return None

        # Match /project/{slug} pattern
        pattern = r'/project/([a-zA-Z0-9_-]+)'
        match = re.search(pattern, url)

        if match:
            return match.group(1)

        return None

    @staticmethod
    def extract_base_url(url: str) -> Optional[str]:
        """
        Extract API base URL from a Taiga project URL.

        Args:
            url: Full Taiga project URL

        Returns:
            API base URL (e.g., https://taiga.imt-atlantique.fr/api/v1)
        """
        if not url:
            return None

        # Match the domain part
        pattern = r'(https?://[^/]+)'
        match = re.search(pattern, url)

        if match:
            return f"{match.group(1)}/api/v1"

        return None
