"""Tests for quiz.py."""

import pytest
from quiz import Quiz


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MCQ_Q = {
    "type": "mcq",
    "question": "What does CPU stand for?",
    "options": [
        "Central Processing Unit",
        "Computer Personal Unit",
        "Central Program Utility",
        "Core Processing Unit",
    ],
    "answer": "Central Processing Unit",
}

TF_Q = {
    "type": "truefalse",
    "question": "Python is an interpreted language.",
    "options": ["True", "False"],
    "answer": "True",
}

SAMPLE_QUESTIONS = [MCQ_Q, TF_Q]


@pytest.fixture
def quiz():
    return Quiz(list(SAMPLE_QUESTIONS))


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestQuizInit:
    def test_requires_at_least_one_question(self):
        with pytest.raises(ValueError):
            Quiz([])

    def test_total_matches_question_count(self, quiz):
        assert quiz.total == 2

    def test_questions_are_accessible(self, quiz):
        assert len(quiz.questions) == 2


# ---------------------------------------------------------------------------
# check_answer
# ---------------------------------------------------------------------------

class TestCheckAnswer:
    def test_correct_mcq_answer(self, quiz):
        assert quiz.check_answer(0, "Central Processing Unit") is True

    def test_wrong_mcq_answer(self, quiz):
        assert quiz.check_answer(0, "Computer Personal Unit") is False

    def test_correct_truefalse(self, quiz):
        assert quiz.check_answer(1, "True") is True

    def test_wrong_truefalse(self, quiz):
        assert quiz.check_answer(1, "False") is False

    def test_case_insensitive(self, quiz):
        assert quiz.check_answer(0, "central processing unit") is True

    def test_strips_whitespace(self, quiz):
        assert quiz.check_answer(0, "  Central Processing Unit  ") is True

    def test_invalid_index_raises(self, quiz):
        with pytest.raises(IndexError):
            quiz.check_answer(99, "anything")


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

class TestScore:
    def test_all_correct(self):
        q = Quiz(list(SAMPLE_QUESTIONS))
        q.set_answer(0, "Central Processing Unit")
        q.set_answer(1, "True")
        result = q.score()
        assert result["correct"] == 2
        assert result["total"] == 2
        assert result["percentage"] == 100.0

    def test_all_wrong(self):
        q = Quiz(list(SAMPLE_QUESTIONS))
        q.set_answer(0, "Core Processing Unit")
        q.set_answer(1, "False")
        result = q.score()
        assert result["correct"] == 0
        assert result["total"] == 2
        assert result["percentage"] == 0.0

    def test_partial_score(self):
        q = Quiz(list(SAMPLE_QUESTIONS))
        q.set_answer(0, "Central Processing Unit")  # correct
        q.set_answer(1, "False")                    # wrong
        result = q.score()
        assert result["correct"] == 1
        assert result["total"] == 2
        assert result["percentage"] == 50.0

    def test_unanswered_counts_as_wrong(self):
        q = Quiz(list(SAMPLE_QUESTIONS))
        # No answers set — unanswered treated as wrong
        result = q.score()
        assert result["correct"] == 0


# ---------------------------------------------------------------------------
# feedback
# ---------------------------------------------------------------------------

class TestFeedback:
    def test_feedback_length_matches_questions(self, quiz):
        fb = quiz.feedback()
        assert len(fb) == 2

    def test_feedback_keys(self, quiz):
        fb = quiz.feedback()
        for item in fb:
            assert "question" in item
            assert "user_answer" in item
            assert "correct_answer" in item
            assert "is_correct" in item

    def test_correct_answer_reflected(self):
        q = Quiz([MCQ_Q])
        q.set_answer(0, "Central Processing Unit")
        fb = q.feedback()
        assert fb[0]["is_correct"] is True

    def test_wrong_answer_reflected(self):
        q = Quiz([MCQ_Q])
        q.set_answer(0, "Wrong")
        fb = q.feedback()
        assert fb[0]["is_correct"] is False
