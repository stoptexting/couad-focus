"""Taiga integration API routes."""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import hmac
import hashlib

from app.extensions import db
from app.services.taiga_sync_service import TaigaSyncService
from app.services.taiga_client import (
    TaigaAuthError,
    TaigaPermissionError,
    TaigaNotFoundError,
    TaigaRateLimitError,
    TaigaClientError,
    TaigaClient
)

logger = logging.getLogger(__name__)

bp = Blueprint('taiga', __name__, url_prefix='/api/taiga')

# Singleton service instance
_sync_service = None


def get_sync_service() -> TaigaSyncService:
    """Get or create the sync service singleton."""
    global _sync_service
    if _sync_service is None:
        _sync_service = TaigaSyncService()
    return _sync_service


@bp.route('/config', methods=['GET'])
def get_config():
    """
    Get current Taiga configuration status (without sensitive data).

    Response:
        {
            "configured": bool,
            "authenticated": bool,
            "has_project": bool,
            "username": string | null,
            "project_url": string | null,
            "project_slug": string | null,
            "sync_status": string,
            "last_sync_at": string | null,
            "last_error": string | null
        }
    """
    service = get_sync_service()
    config = service.get_config()

    if not config:
        return jsonify({
            'configured': False,
            'authenticated': False,
            'has_project': False,
            'username': None,
            'project_url': None,
            'project_slug': None,
            'sync_status': 'not_configured',
            'last_sync_at': None,
            'last_error': None
        }), 200

    return jsonify(config.to_dict(include_sensitive=False)), 200


@bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate with Taiga using username and password.

    Request Body:
        {
            "username": "user@example.com",
            "password": "password123"
        }

    Response:
        {
            "success": true,
            "username": "user",
            "full_name": "User Name",
            "message": "Login successful"
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    try:
        service = get_sync_service()
        result = service.login(username, password)
        return jsonify(result), 200

    except TaigaAuthError as e:
        logger.warning(f"Taiga login failed: {e}")
        return jsonify({
            'error': 'Login failed',
            'detail': str(e)
        }), 401
    except TaigaClientError as e:
        logger.error(f"Taiga client error: {e}")
        return jsonify({
            'error': 'Connection failed',
            'detail': str(e)
        }), 503
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        return jsonify({
            'error': 'Login failed',
            'detail': str(e)
        }), 500


@bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout from Taiga (clears credentials and project config).

    Response:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    service = get_sync_service()
    result = service.logout()
    return jsonify(result), 200


@bp.route('/project', methods=['POST'])
def set_project():
    """
    Set the Taiga project to sync from.

    Request Body:
        {
            "project_url": "https://taiga.imt-atlantique.fr/project/my-project/"
        }

    Response:
        {
            "success": true,
            "project_name": "My Project",
            "project_slug": "my-project",
            "message": "Connected to project: My Project"
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    project_url = data.get('project_url', '').strip()
    if not project_url:
        return jsonify({'error': 'project_url is required'}), 400

    try:
        service = get_sync_service()
        result = service.set_project(project_url)
        return jsonify(result), 200

    except TaigaAuthError as e:
        return jsonify({
            'error': 'Not authenticated',
            'detail': str(e),
            'action_required': 'login'
        }), 401
    except TaigaPermissionError as e:
        return jsonify({
            'error': 'Permission denied',
            'detail': str(e)
        }), 403
    except TaigaNotFoundError as e:
        return jsonify({
            'error': 'Project not found',
            'detail': str(e)
        }), 404
    except ValueError as e:
        return jsonify({
            'error': 'Invalid URL',
            'detail': str(e)
        }), 400
    except TaigaClientError as e:
        return jsonify({
            'error': 'Connection failed',
            'detail': str(e)
        }), 503
    except Exception as e:
        logger.exception(f"Unexpected error setting project: {e}")
        return jsonify({
            'error': 'Failed to set project',
            'detail': str(e)
        }), 500


@bp.route('/project', methods=['DELETE'])
def disconnect_project():
    """
    Disconnect from current project (keeps authentication).

    Response:
        {
            "success": true,
            "message": "Project disconnected"
        }
    """
    service = get_sync_service()
    result = service.disconnect_project()
    return jsonify(result), 200


@bp.route('/sync', methods=['POST'])
def sync():
    """
    Trigger synchronization with Taiga (force refresh).

    Response:
        {
            "success": true,
            "summary": {
                "project_synced": true,
                "sprints_created": 2,
                "sprints_updated": 1,
                "user_stories_created": 10,
                "user_stories_updated": 5,
                "tasks_created": 25,
                "tasks_updated": 12
            },
            "last_sync_at": "2024-01-15T10:30:00"
        }
    """
    try:
        service = get_sync_service()
        result = service.sync()

        # Update LED display after sync
        try:
            config = service.get_config()
            if config.local_project_id:
                from app.services.project_service import ProjectService
                project_service = ProjectService()
                project = project_service.get_project_by_id(config.local_project_id)
                if project:
                    project_service._update_leds_after_change(project)
                    logger.info("LED display updated after manual sync")
        except Exception as e:
            logger.warning(f"LED sync after manual sync failed: {e}")

        return jsonify(result), 200

    except TaigaAuthError as e:
        return jsonify({
            'error': 'Authentication expired',
            'detail': str(e),
            'action_required': 'login'
        }), 401
    except TaigaPermissionError as e:
        return jsonify({
            'error': 'Permission denied',
            'detail': str(e)
        }), 403
    except TaigaRateLimitError as e:
        return jsonify({
            'error': 'Rate limit exceeded',
            'detail': str(e),
            'retry_after': 60
        }), 429
    except ValueError as e:
        return jsonify({
            'error': 'Not configured',
            'detail': str(e)
        }), 400
    except TaigaClientError as e:
        return jsonify({
            'error': 'Sync failed',
            'detail': str(e)
        }), 503
    except Exception as e:
        logger.exception(f"Unexpected error during sync: {e}")
        return jsonify({
            'error': 'Sync failed',
            'detail': str(e)
        }), 500


@bp.route('/init-led', methods=['POST'])
def init_led():
    """
    Initialize LED display with current project state.
    Called by frontend on first page load.
    """
    try:
        service = get_sync_service()
        config = service.get_config()

        if not config or not config.local_project_id:
            return jsonify({'initialized': False, 'reason': 'No project configured'}), 200

        from app.services.project_service import ProjectService
        project_service = ProjectService()
        project = project_service.get_project_by_id(config.local_project_id)

        if not project:
            return jsonify({'initialized': False, 'reason': 'Project not found'}), 200

        project_service._update_leds_after_change(project)
        logger.info("LED display initialized on frontend request")
        return jsonify({'initialized': True}), 200

    except Exception as e:
        logger.warning(f"LED initialization failed: {e}")
        return jsonify({'initialized': False, 'reason': str(e)}), 200


@bp.route('/tree', methods=['GET'])
def get_tree():
    """
    Get the full project tree with progress for display.

    Response:
        {
            "project": {
                "id": "...",
                "name": "Project Name",
                "progress": 75
            },
            "sprints": [
                {
                    "id": "...",
                    "name": "Sprint 1",
                    "status": "active",
                    "progress": 80,
                    "user_stories": [...]
                }
            ],
            "has_data": true,
            "last_sync_at": "2024-01-15T10:30:00"
        }
    """
    service = get_sync_service()
    result = service.get_tree()
    return jsonify(result), 200


@bp.route('/validate-url', methods=['POST'])
def validate_url():
    """
    Validate a Taiga project URL format (no authentication required).

    Request Body:
        {"url": "https://taiga.imt-atlantique.fr/project/my-project/"}

    Response:
        {"valid": true, "slug": "my-project"}
    """
    data = request.get_json()
    url = data.get('url', '') if data else ''

    slug = TaigaClient.parse_project_url(url)

    return jsonify({
        'valid': slug is not None,
        'slug': slug
    }), 200


@bp.route('/my-projects', methods=['GET'])
def get_my_projects():
    """
    List all projects the authenticated user is a member of.

    Response:
        {
            "success": true,
            "projects": [
                {
                    "id": 123,
                    "name": "My Project",
                    "slug": "my-project",
                    "is_private": false,
                    "description": "...",
                    "url": "https://..."
                }
            ]
        }
    """
    try:
        service = get_sync_service()
        result = service.get_my_projects()
        return jsonify(result), 200

    except TaigaAuthError as e:
        return jsonify({
            'error': 'Not authenticated',
            'detail': str(e),
            'action_required': 'login'
        }), 401
    except TaigaClientError as e:
        return jsonify({
            'error': 'Failed to fetch projects',
            'detail': str(e)
        }), 503
    except Exception as e:
        logger.exception(f"Error fetching projects: {e}")
        return jsonify({
            'error': 'Failed to fetch projects',
            'detail': str(e)
        }), 500


@bp.route('/pending-memberships', methods=['GET'])
def get_pending_memberships():
    """
    List user's pending membership invitations and requests.

    Response:
        {
            "success": true,
            "invitations": [...],
            "requests": [...]
        }
    """
    try:
        service = get_sync_service()
        result = service.get_pending_memberships()
        return jsonify(result), 200

    except TaigaAuthError as e:
        return jsonify({
            'error': 'Not authenticated',
            'detail': str(e),
            'action_required': 'login'
        }), 401
    except TaigaClientError as e:
        return jsonify({
            'error': 'Failed to fetch memberships',
            'detail': str(e)
        }), 503
    except Exception as e:
        logger.exception(f"Error fetching memberships: {e}")
        return jsonify({
            'error': 'Failed to fetch memberships',
            'detail': str(e)
        }), 500


@bp.route('/accept-invitation', methods=['POST'])
def accept_invitation():
    """
    Accept a membership invitation.

    Request Body:
        {"invitation_id": 123}

    Response:
        {"success": true, "message": "Invitation accepted"}
    """
    data = request.get_json()
    if not data or 'invitation_id' not in data:
        return jsonify({'error': 'invitation_id is required'}), 400

    try:
        service = get_sync_service()
        result = service.accept_invitation(data['invitation_id'])
        return jsonify(result), 200

    except TaigaAuthError as e:
        return jsonify({
            'error': 'Not authenticated',
            'detail': str(e),
            'action_required': 'login'
        }), 401
    except TaigaNotFoundError as e:
        return jsonify({
            'error': 'Invitation not found',
            'detail': str(e)
        }), 404
    except TaigaClientError as e:
        return jsonify({
            'error': 'Failed to accept invitation',
            'detail': str(e)
        }), 503
    except Exception as e:
        logger.exception(f"Error accepting invitation: {e}")
        return jsonify({
            'error': 'Failed to accept invitation',
            'detail': str(e)
        }), 500


@bp.route('/check-project', methods=['POST'])
def check_project():
    """
    Check if user has access to a project by URL.

    Request Body:
        {"project_url": "https://taiga.imt-atlantique.fr/project/my-project/"}

    Response:
        {
            "success": true,
            "has_access": true/false,
            "project": {...} (if has_access),
            "can_request": true/false (if !has_access)
        }
    """
    data = request.get_json()
    if not data or not data.get('project_url'):
        return jsonify({'error': 'project_url is required'}), 400

    slug = TaigaClient.parse_project_url(data['project_url'])
    if not slug:
        return jsonify({'error': 'Invalid project URL format'}), 400

    try:
        service = get_sync_service()
        result = service.join_project_by_slug(slug)
        return jsonify(result), 200

    except TaigaAuthError as e:
        return jsonify({
            'error': 'Not authenticated',
            'detail': str(e),
            'action_required': 'login'
        }), 401
    except TaigaClientError as e:
        return jsonify({
            'error': 'Failed to check project',
            'detail': str(e)
        }), 503
    except Exception as e:
        logger.exception(f"Error checking project: {e}")
        return jsonify({
            'error': 'Failed to check project',
            'detail': str(e)
        }), 500


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Receive Taiga webhook notifications.

    Verifies HMAC-SHA1 signature and triggers sync.

    Headers:
        X-TAIGA-WEBHOOK-SIGNATURE: HMAC-SHA1 signature of the body

    Body: Taiga webhook payload (JSON)
        {
            "action": "create" | "change" | "delete",
            "type": "milestone" | "userstory" | "task" | "issue",
            "by": {...},
            "date": "...",
            "data": {...}
        }

    Response:
        {"status": "ok", "version": 42}
    """
    service = get_sync_service()
    config = service.get_config()

    if not config:
        logger.warning("Webhook received but Taiga not configured")
        return jsonify({'error': 'Taiga not configured'}), 400

    if not config.webhook_secret:
        logger.warning("Webhook received but no webhook secret configured")
        return jsonify({'error': 'Webhook secret not configured'}), 400

    # Get signature from header
    signature = request.headers.get('X-TAIGA-WEBHOOK-SIGNATURE', '')

    # Get raw body for signature verification
    raw_body = request.get_data()

    # Verify HMAC-SHA1 signature
    expected_signature = hmac.new(
        config.webhook_secret.encode('utf-8'),
        raw_body,
        hashlib.sha1
    ).hexdigest()

    # Debug logging
    logger.info(f"Webhook received - Signature: {signature}")
    logger.info(f"Webhook expected - Signature: {expected_signature}")
    logger.info(f"Webhook secret length: {len(config.webhook_secret)}")

    if not hmac.compare_digest(signature, expected_signature):
        logger.warning(f"Webhook signature verification failed. Received: {signature}, Expected: {expected_signature}")
        return jsonify({'error': 'Invalid signature', 'received': signature, 'expected': expected_signature}), 401

    # Parse payload
    try:
        payload = request.get_json()
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400

    if not payload:
        return jsonify({'error': 'Empty payload'}), 400

    action = payload.get('action', 'unknown')
    entity_type = payload.get('type', 'unknown')
    data = payload.get('data', {})

    logger.info(f"Received Taiga webhook: {action} {entity_type}")

    # Check if this is for our project
    project_id = data.get('project')
    if project_id and config.taiga_project_id and project_id != config.taiga_project_id:
        logger.info(f"Webhook for different project {project_id}, ignoring")
        return jsonify({
            'status': 'ignored',
            'reason': 'different_project'
        }), 200

    # Trigger full sync (simple approach - sync everything)
    sync_success = True
    try:
        service.sync()
        logger.info(f"Sync completed after webhook: {action} {entity_type}")
    except Exception as e:
        logger.error(f"Sync failed after webhook: {e}")
        sync_success = False
        # Don't fail the webhook response - Taiga would retry

    # After sync completes successfully, update LEDs
    if sync_success:
        try:
            # Get the local project and trigger LED update
            if config.local_project_id:
                from app.services.project_service import ProjectService
                project_service = ProjectService()
                project = project_service.get_project_by_id(config.local_project_id)
                if project:
                    project_service._update_leds_after_change(project)
                    logger.info("LED display updated after webhook sync")
        except Exception as e:
            logger.warning(f"LED sync after webhook failed: {e}")
            # Don't fail the webhook response for LED sync failures

    # Record webhook in history
    webhook_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'entity_type': entity_type,
        'entity_ref': data.get('ref'),
        'entity_name': data.get('name') or data.get('subject'),
        'payload': payload,
        'success': sync_success
    }

    # Prepend new entry, keep only last 5
    history = config.webhook_history or []
    history = [webhook_entry] + history[:4]
    config.webhook_history = history

    # Increment data version
    config.data_version = (config.data_version or 0) + 1
    config.last_webhook_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'status': 'ok',
        'action': action,
        'type': entity_type,
        'version': config.data_version
    }), 200


@bp.route('/version', methods=['GET'])
def get_version():
    """
    Get current data version for smart polling.

    Lightweight endpoint that returns version info for cache invalidation.

    Response:
        {
            "version": 42,
            "last_sync_at": "2024-01-15T10:30:00",
            "last_webhook_at": "2024-01-15T10:35:00"
        }
    """
    service = get_sync_service()
    config = service.get_config()

    if not config:
        return jsonify({
            'version': 0,
            'last_sync_at': None,
            'last_webhook_at': None
        }), 200

    return jsonify({
        'version': config.data_version or 0,
        'last_sync_at': config.last_sync_at.isoformat() if config.last_sync_at else None,
        'last_webhook_at': config.last_webhook_at.isoformat() if config.last_webhook_at else None
    }), 200


@bp.route('/webhook-config', methods=['POST'])
def set_webhook_config():
    """
    Set the webhook secret for signature verification.

    Request Body:
        {"secret": "your-webhook-secret"}

    Response:
        {
            "success": true,
            "message": "Webhook configured",
            "webhook_url": "/api/taiga/webhook"
        }
    """
    data = request.get_json()
    if not data or not data.get('secret'):
        return jsonify({'error': 'secret is required'}), 400

    secret = data['secret'].strip()
    if len(secret) < 8:
        return jsonify({'error': 'Secret must be at least 8 characters'}), 400

    service = get_sync_service()
    config = service.get_or_create_config()

    config.webhook_secret = secret
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Webhook secret configured',
        'webhook_url': '/api/taiga/webhook'
    }), 200


@bp.route('/webhook-config', methods=['DELETE'])
def clear_webhook_config():
    """
    Clear the webhook secret (disable webhooks).

    Response:
        {"success": true, "message": "Webhook configuration cleared"}
    """
    service = get_sync_service()
    config = service.get_config()

    if config and config.webhook_secret:
        config.webhook_secret = None
        db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Webhook configuration cleared'
    }), 200
