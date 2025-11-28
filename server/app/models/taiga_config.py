"""TaigaConfig model for storing Taiga integration settings."""
from app.extensions import db
from datetime import datetime
import uuid


class TaigaConfig(db.Model):
    """Model for storing Taiga integration configuration and auth state."""

    __tablename__ = 'taiga_config'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Taiga API configuration
    base_url = db.Column(
        db.String(500),
        nullable=False,
        default='https://taiga.imt-atlantique.fr/api/v1'
    )

    # Authentication (token stored, password not persisted)
    username = db.Column(db.String(100), nullable=True)
    user_email = db.Column(db.String(200), nullable=True)
    taiga_user_id = db.Column(db.Integer, nullable=True)
    auth_token = db.Column(db.String(500), nullable=True)
    token_obtained_at = db.Column(db.DateTime, nullable=True)

    # Project configuration
    project_url = db.Column(db.String(500), nullable=True)
    project_slug = db.Column(db.String(200), nullable=True)
    taiga_project_id = db.Column(db.Integer, nullable=True)

    # Linked local project
    local_project_id = db.Column(
        db.String(36),
        db.ForeignKey('projects.id', ondelete='SET NULL'),
        nullable=True
    )

    # Sync state
    last_sync_at = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(50), nullable=False, default='not_configured')
    # Values: not_configured, authenticated, syncing, synced, error
    last_error = db.Column(db.String(500), nullable=True)

    # Webhook configuration
    webhook_secret = db.Column(db.String(200), nullable=True)
    data_version = db.Column(db.Integer, nullable=False, default=0)
    last_webhook_at = db.Column(db.DateTime, nullable=True)
    webhook_history = db.Column(db.JSON, nullable=True, default=list)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert config to dictionary representation.

        Args:
            include_sensitive: Whether to include auth token (default False)

        Returns:
            Dictionary representation of config
        """
        data = {
            'id': self.id,
            'base_url': self.base_url,
            'username': self.username,
            'project_url': self.project_url,
            'project_slug': self.project_slug,
            'taiga_project_id': self.taiga_project_id,
            'local_project_id': self.local_project_id,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'last_error': self.last_error,
            'configured': self.sync_status != 'not_configured',
            'authenticated': self.auth_token is not None,
            'has_project': self.taiga_project_id is not None,
            'data_version': self.data_version,
            'webhook_configured': self.webhook_secret is not None,
            'last_webhook_at': self.last_webhook_at.isoformat() if self.last_webhook_at else None,
            'webhook_history': self.webhook_history or []
        }

        if include_sensitive:
            data['auth_token'] = self.auth_token

        return data

    def __repr__(self) -> str:
        """String representation of TaigaConfig."""
        return f'<TaigaConfig {self.sync_status}>'
