"""Tests for ai_service.py — using the Mock backend to avoid any live AI call."""

import json
import os

import pytest

# Force mock mode for all tests in this file
os.environ["AI_MOCK"] = "1"

from ai_service import AIService  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ai():
    """AIService configured with mock backend."""
    return AIService(model="test-model")


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

class TestBackendDetection:
    def test_mock_backend_when_env_set(self, ai):
        assert ai.backend == "mock"

    def test_ibm_bob_detected(self, monkeypatch):
        monkeypatch.delenv("AI_MOCK", raising=False)
        monkeypatch.setenv("IBM_BOB_API_KEY", "fake-key")
        svc = AIService()
        assert svc.backend == "ibm_bob"
        monkeypatch.delenv("IBM_BOB_API_KEY")

    def test_ollama_fallback(self, monkeypatch):
        monkeypatch.delenv("AI_MOCK", raising=False)
        monkeypatch.delenv("IBM_BOB_API_KEY", raising=False)
        svc = AIService()
        assert svc.backend == "ollama"


# ---------------------------------------------------------------------------
# explain
# ---------------------------------------------------------------------------

class TestExplain:
    def test_returns_string(self, ai):
        result = ai.explain(topic="Variables", material="x" * 100)
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# generate_quiz
# ---------------------------------------------------------------------------

class TestGenerateQuiz:
    def test_returns_list(self, ai):
        result = ai.generate_quiz(material="x" * 100)
        assert isinstance(result, list)

    def test_default_five_questions(self, ai):
        result = ai.generate_quiz(material="x" * 100)
        assert len(result) == 5

    def test_respects_num_questions(self, ai):
        result = ai.generate_quiz(material="x" * 100, num_questions=3)
        assert len(result) == 3

    def test_question_dict_shape(self, ai):
        questions = ai.generate_quiz(material="x" * 100)
        for q in questions:
            assert "type" in q
            assert "question" in q
            assert "options" in q
            assert "answer" in q
            assert q["type"] in ("mcq", "truefalse")


# ---------------------------------------------------------------------------
# solve_doubt
# ---------------------------------------------------------------------------

class TestSolveDoubt:
    def test_returns_string(self, ai):
        result = ai.solve_doubt(doubt="What is a variable?", material="x" * 100)
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# generate_revision_plan
# ---------------------------------------------------------------------------

class TestGenerateRevisionPlan:
    def test_returns_list_of_strings(self, ai):
        result = ai.generate_revision_plan(topic="Python", material="x" * 100)
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)

    def test_non_empty(self, ai):
        result = ai.generate_revision_plan(topic="Python", material="x" * 100)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# AIService._parse_quiz_json (static helper)
# ---------------------------------------------------------------------------

class TestParseQuizJson:
    def test_plain_json_array(self):
        raw = json.dumps([{"type": "mcq", "question": "Q?", "options": ["A"], "answer": "A"}])
        result = AIService._parse_quiz_json(raw)
        assert isinstance(result, list)
        assert result[0]["type"] == "mcq"

    def test_strips_markdown_fences(self):
        inner = json.dumps([{"type": "truefalse", "question": "Q?", "options": ["True", "False"], "answer": "True"}])
        raw = f"```json\n{inner}\n```"
        result = AIService._parse_quiz_json(raw)
        assert result[0]["type"] == "truefalse"

    def test_raises_on_no_array(self):
        with pytest.raises(ValueError):
            AIService._parse_quiz_json("This is just text with no JSON array.")

    def test_raises_on_invalid_json(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            AIService._parse_quiz_json("[{broken json}")
