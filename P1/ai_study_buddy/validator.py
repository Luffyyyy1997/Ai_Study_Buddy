"""validator.py — input validation helpers.

All functions are pure (no side effects). They return an error string when
validation fails, or None when the input is valid.
"""

_MIN_MATERIAL_CHARS = 50


def validate_material(text: str) -> str | None:
    """Return an error message if *text* is not acceptable study material.

    Rules:
    - Must not be empty or whitespace-only.
    - Must be at least 50 characters long.

    Returns None when the input passes validation.
    """
    if not text or not text.strip():
        return "Study material cannot be empty. Please paste or type some text."
    if len(text.strip()) < _MIN_MATERIAL_CHARS:
        return (
            f"Study material is too short "
            f"(minimum {_MIN_MATERIAL_CHARS} characters). "
            "Please provide more detail."
        )
    return None


def validate_topic(text: str) -> str | None:
    """Return an error message if *text* is not an acceptable topic name.

    Rules:
    - Must not be empty or whitespace-only.

    Returns None when the input passes validation.
    """
    if not text or not text.strip():
        return "Topic cannot be empty. Please enter a topic name."
    return None


def validate_doubt(text: str) -> str | None:
    """Return an error message if *text* is not an acceptable doubt/question.

    Rules:
    - Must not be empty or whitespace-only.

    Returns None when the input passes validation.
    """
    if not text or not text.strip():
        return "Please type your question before clicking Ask."
    return None


def validate_study_time(hours: float | int | None) -> str | None:
    """Return an error message if *hours* is not a valid study-time value.

    Rules:
    - Must be a positive number greater than zero.

    Returns None when the input passes validation.
    """
    if hours is None:
        return "Please enter the number of study hours available."
    try:
        value = float(hours)
    except (TypeError, ValueError):
        return "Study time must be a number (e.g. 2 or 1.5)."
    if value <= 0:
        return "Study time must be greater than zero."
    return None
