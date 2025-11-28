"""Sprint model for database."""
from app.extensions import db
from datetime import datetime, date
import uuid


class Sprint(db.Model):
    """Sprint model representing a project sprint."""

    __tablename__ = 'sprints'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(
        db.String(36),
        db.ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False
    )
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='planned')

    # Taiga integration fields
    taiga_id = db.Column(db.Integer, nullable=True, index=True)

    # Relationships
    user_stories = db.relationship(
        'UserStory',
        backref='sprint',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def to_dict(self, include_user_stories: bool = False, include_progress: bool = True) -> dict:
        """
        Convert sprint to dictionary representation.

        Args:
            include_user_stories: Whether to include nested user stories data
            include_progress: Whether to include progress calculation (default True)

        Returns:
            Dictionary representation of sprint
        """
        data = {
            'id': self.id,
            'name': self.name,
            'project_id': self.project_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status
        }

        if include_user_stories:
            data['user_stories'] = [us.to_dict(include_tasks=True) for us in self.user_stories]

        if include_progress:
            # Import here to avoid circular dependency
            from app.services.progress_calculator import ProgressCalculator
            data['progress'] = ProgressCalculator.calculate_sprint_progress(self)

        return data

    @staticmethod
    def validate_status(status: str) -> bool:
        """Validate sprint status value."""
        return status in ['planned', 'active', 'completed']

    def __repr__(self) -> str:
        """String representation of Sprint."""
        return f'<Sprint {self.name}>'
