"""Tests for storage.py."""

import json
import os
import tempfile

import pytest
from storage import Storage
from revision_plan import RevisionPlan


# ---------------------------------------------------------------------------
# Fixture — temporary storage file
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_storage(tmp_path):
    """Return a Storage instance backed by a temp directory."""
    path = str(tmp_path / "data" / "storage.json")
    return Storage(path=path)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestStorageInit:
    def test_creates_file_if_missing(self, tmp_path):
        path = str(tmp_path / "sub" / "storage.json")
        assert not os.path.exists(path)
        Storage(path=path)
        assert os.path.exists(path)

    def test_initial_content_is_empty(self, tmp_storage):
        assert tmp_storage.load_quiz_scores() == []
        assert tmp_storage.load_revision_plans() == []

    def test_recovers_from_malformed_json(self, tmp_path):
        path = str(tmp_path / "data" / "storage.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("THIS IS NOT JSON {{{{")
        s = Storage(path=path)
        # Should not raise; instead resets
        assert s.load_quiz_scores() == []


# ---------------------------------------------------------------------------
# Quiz scores
# ---------------------------------------------------------------------------

class TestQuizScores:
    def test_save_and_load(self, tmp_storage):
        tmp_storage.save_quiz_score({"correct": 4, "total": 5, "percentage": 80.0})
        scores = tmp_storage.load_quiz_scores()
        assert len(scores) == 1
        assert scores[0]["correct"] == 4

    def test_timestamp_added(self, tmp_storage):
        tmp_storage.save_quiz_score({"correct": 3, "total": 5, "percentage": 60.0})
        scores = tmp_storage.load_quiz_scores()
        assert "timestamp" in scores[0]

    def test_multiple_scores_accumulate(self, tmp_storage):
        tmp_storage.save_quiz_score({"correct": 1, "total": 5, "percentage": 20.0})
        tmp_storage.save_quiz_score({"correct": 5, "total": 5, "percentage": 100.0})
        assert len(tmp_storage.load_quiz_scores()) == 2

    def test_newest_first(self, tmp_storage):
        tmp_storage.save_quiz_score({"correct": 1, "total": 5, "percentage": 20.0})
        tmp_storage.save_quiz_score({"correct": 5, "total": 5, "percentage": 100.0})
        scores = tmp_storage.load_quiz_scores()
        # Newest (100%) should be first
        assert scores[0]["percentage"] == 100.0


# ---------------------------------------------------------------------------
# Revision plans
# ---------------------------------------------------------------------------

class TestRevisionPlans:
    def test_save_and_load(self, tmp_storage):
        plan = RevisionPlan(topic="Loops", steps=["Step 1", "Step 2"])
        tmp_storage.save_revision_plan(plan)
        plans = tmp_storage.load_revision_plans()
        assert len(plans) == 1
        assert plans[0]["topic"] == "Loops"

    def test_overwrites_same_topic(self, tmp_storage):
        plan1 = RevisionPlan(topic="Loops", steps=["Step A"])
        plan2 = RevisionPlan(topic="Loops", steps=["Step B"])
        tmp_storage.save_revision_plan(plan1)
        tmp_storage.save_revision_plan(plan2)
        plans = tmp_storage.load_revision_plans()
        assert len(plans) == 1
        assert plans[0]["steps"] == ["Step B"]

    def test_different_topics_both_saved(self, tmp_storage):
        plan1 = RevisionPlan(topic="Loops", steps=["Step A"])
        plan2 = RevisionPlan(topic="Functions", steps=["Step B"])
        tmp_storage.save_revision_plan(plan1)
        tmp_storage.save_revision_plan(plan2)
        assert len(tmp_storage.load_revision_plans()) == 2

    def test_timestamp_added(self, tmp_storage):
        plan = RevisionPlan(topic="Test", steps=["Step 1"])
        tmp_storage.save_revision_plan(plan)
        plans = tmp_storage.load_revision_plans()
        assert "timestamp" in plans[0]
