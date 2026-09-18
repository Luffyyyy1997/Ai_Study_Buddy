"""revision_plan.py — RevisionPlan data model.

A RevisionPlan is a simple container: a topic name and an ordered list of
study steps (plain strings).
"""

from __future__ import annotations


class RevisionPlan:
    """Stores a revision plan for a given topic."""

    def __init__(self, topic: str, steps: list[str]) -> None:
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty.")
        if not steps:
            raise ValueError("Revision plan must have at least one step.")
        self.topic: str = topic.strip()
        self.steps: list[str] = [s for s in steps if s.strip()]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON storage."""
        return {"topic": self.topic, "steps": self.steps}

    @classmethod
    def from_dict(cls, d: dict) -> "RevisionPlan":
        """Deserialise from a plain dict (as stored in JSON)."""
        return cls(topic=d["topic"], steps=d["steps"])

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def formatted_steps(self) -> str:
        """Return the steps as a numbered plain-text list."""
        return "\n".join(f"{i + 1}. {step}" for i, step in enumerate(self.steps))

    def __repr__(self) -> str:  # pragma: no cover
        return f"RevisionPlan(topic={self.topic!r}, steps={len(self.steps)})"
