"""Task model for database."""
from app.extensions import db
from datetime import datetime
import uuid


class Task(db.Model):
    """Task model representing a project task."""

    __tablename__ = 'tasks'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='new')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    user_story_id = db.Column(
        db.String(36),
        db.ForeignKey('user_stories.id', ondelete='CASCADE'),
        nullable=True  # Nullable during migration, will be required after
    )

    # Taiga integration fields
    taiga_id = db.Column(db.Integer, nullable=True, index=True)
    taiga_ref = db.Column(db.Integer, nullable=True)  # Taiga reference number

    def to_dict(self) -> dict:
        """Convert task to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'user_story_id': self.user_story_id,
            'taiga_id': self.taiga_id,
            'taiga_ref': self.taiga_ref,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def validate_status(status: str) -> bool:
        """Validate task status value."""
        return status in ['new', 'completed']
