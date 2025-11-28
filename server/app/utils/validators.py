"""Input validation utilities."""
from typing import Dict, List


def validate_task_input(data: Dict) -> List[str]:
    """
    Validate task creation/update input.

    Args:
        data: Input data dictionary

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if 'title' in data:
        if not data['title'] or not data['title'].strip():
            errors.append('Title is required')
        elif len(data['title']) > 100:
            errors.append('Title max 100 characters')

    if 'description' in data and data.get('description'):
        if len(data['description']) > 500:
            errors.append('Description max 500 characters')

    if 'status' in data:
        if data['status'] not in ['new', 'completed']:
            errors.append('Status must be "new" or "completed"')

    return errors


def validate_percentage(percentage: int) -> List[str]:
    """
    Validate percentage value.

    Args:
        percentage: Percentage value to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not isinstance(percentage, int):
        errors.append('Percentage must be an integer')
    elif percentage < 0 or percentage > 100:
        errors.append('Percentage must be between 0 and 100')

    return errors
