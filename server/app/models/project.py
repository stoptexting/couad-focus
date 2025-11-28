"""Project model for database."""
from app.extensions import db
from datetime import datetime
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.progress_calculator import ProgressCalculator


class Project(db.Model):
    """Project model representing a top-level project."""

    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    preferred_layout = db.Column(db.String(20), nullable=True, default='single')
    preferred_sprint_index = db.Column(db.Integer, nullable=True, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Taiga integration fields
    taiga_id = db.Column(db.Integer, nullable=True, unique=True, index=True)
    taiga_slug = db.Column(db.String(200), nullable=True)

    # Relationships
    sprints = db.relationship(
        'Sprint',
        backref='project',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def to_dict(self, include_sprints: bool = False, include_progress: bool = True) -> dict:
        """
        Convert project to dictionary representation.

        Args:
            include_sprints: Whether to include nested sprints data
            include_progress: Whether to include progress calculation (default True)

        Returns:
            Dictionary representation of project
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'preferred_layout': self.preferred_layout or 'single',
            'preferred_sprint_index': self.preferred_sprint_index or 0,
            'created_at': self.created_at.isoformat()
        }

        if include_sprints:
            # Import Sprint model for ordering
            from app.models.sprint import Sprint
            # Order sprints by start_date ascending, filter out Backlog
            ordered_sprints = self.sprints.order_by(Sprint.start_date.asc().nullslast())
            data['sprints'] = [
                sprint.to_dict(include_user_stories=True)
                for sprint in ordered_sprints
                if sprint.name != 'Backlog'
            ]

        if include_progress:
            # Import here to avoid circular dependency
            from app.services.progress_calculator import ProgressCalculator
            data['progress'] = ProgressCalculator.calculate_project_progress(self)

        return data

    def __repr__(self) -> str:
        """String representation of Project."""
        return f'<Project {self.name}>'
