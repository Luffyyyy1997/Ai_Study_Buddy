"""quiz.py — Quiz data model and answer-scoring logic.

A question dict has the following shape:

    {
        "type":     "mcq" | "truefalse",
        "question": str,
        "options":  list[str],   # 4 items for MCQ, ["True","False"] for T/F
        "answer":   str          # the correct option text (exact match)
    }
"""

from __future__ import annotations


class Quiz:
    """Holds one quiz session and tracks user answers."""

    def __init__(self, questions: list[dict]) -> None:
        if not questions:
            raise ValueError("A quiz must have at least one question.")
        self._questions: list[dict] = questions
        # user_answers is a list of the same length; None means unanswered.
        self._user_answers: list[str | None] = [None] * len(questions)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def questions(self) -> list[dict]:
        """Read-only view of the question list."""
        return self._questions

    @property
    def total(self) -> int:
        """Total number of questions."""
        return len(self._questions)

    # ------------------------------------------------------------------
    # Answering
    # ------------------------------------------------------------------

    def set_answer(self, index: int, answer: str) -> None:
        """Record *answer* for question at *index*."""
        if index < 0 or index >= self.total:
            raise IndexError(f"Question index {index} is out of range.")
        self._user_answers[index] = answer

    def check_answer(self, index: int, user_answer: str) -> bool:
        """Return True if *user_answer* matches the correct answer.

        Comparison is case-insensitive and strips surrounding whitespace.
        """
        if index < 0 or index >= self.total:
            raise IndexError(f"Question index {index} is out of range.")
        correct = self._questions[index]["answer"].strip().lower()
        return user_answer.strip().lower() == correct

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score(self) -> dict:
        """Return a summary dict: {correct, total, percentage}.

        Only counts questions where an answer has been recorded.
        """
        correct = sum(
            1
            for i, ans in enumerate(self._user_answers)
            if ans is not None and self.check_answer(i, ans)
        )
        return {
            "correct": correct,
            "total": self.total,
            "percentage": round(correct / self.total * 100, 1),
        }

    def feedback(self) -> list[dict]:
        """Return per-question feedback dicts.

        Each dict has: question, user_answer, correct_answer, is_correct.
        """
        result = []
        for i, q in enumerate(self._questions):
            ans = self._user_answers[i]
            result.append(
                {
                    "question": q["question"],
                    "user_answer": ans,
                    "correct_answer": q["answer"],
                    "is_correct": (
                        self.check_answer(i, ans) if ans is not None else False
                    ),
                }
            )
        return result
