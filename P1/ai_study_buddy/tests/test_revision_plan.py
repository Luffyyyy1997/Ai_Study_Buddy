"""Tests for revision_plan.py."""

import pytest
from revision_plan import RevisionPlan


SAMPLE_STEPS = [
    "Read the introduction carefully.",
    "Note down key terms.",
    "Attempt practice problems.",
]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestRevisionPlanInit:
    def test_valid_creation(self):
        plan = RevisionPlan(topic="Loops", steps=SAMPLE_STEPS)
        assert plan.topic == "Loops"
        assert len(plan.steps) == 3

    def test_empty_topic_raises(self):
        with pytest.raises(ValueError):
            RevisionPlan(topic="", steps=SAMPLE_STEPS)

    def test_whitespace_topic_raises(self):
        with pytest.raises(ValueError):
            RevisionPlan(topic="   ", steps=SAMPLE_STEPS)

    def test_empty_steps_raises(self):
        with pytest.raises(ValueError):
            RevisionPlan(topic="Loops", steps=[])

    def test_blank_steps_are_filtered(self):
        plan = RevisionPlan(topic="Loops", steps=["Step 1", "   ", "Step 3"])
        assert len(plan.steps) == 2

    def test_topic_is_stripped(self):
        plan = RevisionPlan(topic="  Loops  ", steps=SAMPLE_STEPS)
        assert plan.topic == "Loops"


# ---------------------------------------------------------------------------
# to_dict / from_dict
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict_structure(self):
        plan = RevisionPlan(topic="Loops", steps=SAMPLE_STEPS)
        d = plan.to_dict()
        assert d["topic"] == "Loops"
        assert d["steps"] == SAMPLE_STEPS

    def test_round_trip(self):
        original = RevisionPlan(topic="Loops", steps=SAMPLE_STEPS)
        restored = RevisionPlan.from_dict(original.to_dict())
        assert restored.topic == original.topic
        assert restored.steps == original.steps


# ---------------------------------------------------------------------------
# formatted_steps
# ---------------------------------------------------------------------------

class TestFormattedSteps:
    def test_numbered_output(self):
        plan = RevisionPlan(topic="Test", steps=["Alpha", "Beta"])
        text = plan.formatted_steps()
        assert "1. Alpha" in text
        assert "2. Beta" in text
