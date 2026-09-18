"""storage.py — simple JSON persistence for quiz scores and revision plans.

The entire state is kept in a single JSON file with the shape:

    {
        "scores": [ { "topic": str, "correct": int, "total": int,
                       "percentage": float, "timestamp": str }, ... ],
        "plans":  [ { "topic": str, "steps": [str, ...],
                       "timestamp": str }, ... ]
    }

If the file is missing or malformed it is automatically reset.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from revision_plan import RevisionPlan

_EMPTY_STATE: dict = {"scores": [], "plans": []}


class Storage:
    """Handles reading and writing the local JSON persistence file."""

    def __init__(self, path: str = "data/storage.json") -> None:
        self._path = path
        self._ensure_file()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_file(self) -> None:
        """Create the file (and parent directory) if it does not exist."""
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        if not os.path.exists(self._path):
            self._write(_EMPTY_STATE)

    def _read(self) -> dict:
        """Load JSON from disk; reset to empty state on any error."""
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Basic schema check
            if not isinstance(data.get("scores"), list) or not isinstance(
                data.get("plans"), list
            ):
                raise ValueError("Unexpected schema")
            return data
        except (json.JSONDecodeError, ValueError, KeyError, OSError):
            self._write(_EMPTY_STATE)
            return dict(_EMPTY_STATE)

    def _write(self, data: dict) -> None:
        """Persist *data* to disk as JSON."""
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    # ------------------------------------------------------------------
    # Quiz scores
    # ------------------------------------------------------------------

    def save_quiz_score(self, score: dict) -> None:
        """Append a quiz score entry.

        *score* should contain at least the keys returned by ``Quiz.score()``.
        A ``timestamp`` key is added automatically.
        """
        data = self._read()
        entry = dict(score)
        entry["timestamp"] = datetime.now().isoformat(timespec="seconds")
        data["scores"].append(entry)
        self._write(data)

    def load_quiz_scores(self) -> list[dict]:
        """Return all saved quiz score entries, newest first."""
        return list(reversed(self._read()["scores"]))

    # ------------------------------------------------------------------
    # Revision plans
    # ------------------------------------------------------------------

    def save_revision_plan(self, plan: "RevisionPlan") -> None:
        """Save (or overwrite) the revision plan for ``plan.topic``.

        Only the most recent plan per topic is kept.
        """
        data = self._read()
        plan_dict = plan.to_dict()
        plan_dict["timestamp"] = datetime.now().isoformat(timespec="seconds")
        # Overwrite existing entry for the same topic
        data["plans"] = [
            p for p in data["plans"] if p.get("topic") != plan.topic
        ]
        data["plans"].append(plan_dict)
        self._write(data)

    def load_revision_plans(self) -> list[dict]:
        """Return all saved revision plans, newest first."""
        return list(reversed(self._read()["plans"]))
