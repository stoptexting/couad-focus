"""UserStory model for database."""
from app.extensions import db
from datetime import datetime
import uuid


class UserStory(db.Model):
    """UserStory model representing a user story within a sprint."""

    __tablename__ = 'user_stories'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    sprint_id = db.Column(
        db.String(36),
        db.ForeignKey('sprints.id', ondelete='CASCADE'),
        nullable=False
    )
    priority = db.Column(db.String(10), nullable=False, default='P2')
    status = db.Column(db.String(20), nullable=False, default='new')

    # Taiga integration fields
    taiga_id = db.Column(db.Integer, nullable=True, index=True)
    taiga_ref = db.Column(db.Integer, nullable=True)  # Taiga reference number (#123)

    # Relationships
    tasks = db.relationship(
        'Task',
        backref='user_story',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def to_dict(self, include_tasks: bool = False, include_progress: bool = True) -> dict:
        """
        Convert user story to dictionary representation.

        Args:
            include_tasks: Whether to include nested tasks data
            include_progress: Whether to include progress calculation (default True)

        Returns:
            Dictionary representation of user story
        """
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'sprint_id': self.sprint_id,
            'priority': self.priority,
            'status': self.status,
            'taiga_id': self.taiga_id,
            'taiga_ref': self.taiga_ref
        }

        if include_tasks:
            data['tasks'] = [task.to_dict() for task in self.tasks]

        if include_progress:
            # Import here to avoid circular dependency
            from app.services.progress_calculator import ProgressCalculator
            data['progress'] = ProgressCalculator.calculate_user_story_progress(self)

        return data

    @staticmethod
    def validate_priority(priority: str) -> bool:
        """Validate user story priority value."""
        return priority in ['P0', 'P1', 'P2']

    @staticmethod
    def validate_status(status: str) -> bool:
        """Validate user story status value."""
        return status in ['new', 'in_progress', 'completed']

    def __repr__(self) -> str:
        """String representation of UserStory."""
        return f'<UserStory {self.title}>'
