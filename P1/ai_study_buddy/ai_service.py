"""ai_service.py — AI backend integration.

Supports three backends, chosen automatically at runtime:

1. **IBM Bob** — when ``IBM_BOB_API_KEY`` (and optionally ``IBM_BOB_URL``)
   environment variables are set.
2. **Ollama** — when IBM Bob is not configured and Ollama is reachable at
   ``OLLAMA_URL`` (default http://localhost:11434).
3. **Mock** — built-in fallback when neither backend is available, or when
   ``AI_MOCK=1`` is set. Returns canned sample responses so the UI can be
   tested without any AI service.

No API keys or secrets are hard-coded here. All credentials are read from
environment variables.
"""

from __future__ import annotations

import json
import os
import re


# ---------------------------------------------------------------------------
# Backend detection helpers
# ---------------------------------------------------------------------------

def _ibm_bob_configured() -> bool:
    return bool(os.environ.get("IBM_BOB_API_KEY", "").strip())


def _mock_forced() -> bool:
    return os.environ.get("AI_MOCK", "").strip() == "1"


# ---------------------------------------------------------------------------
# Mock responses (used for testing / offline development)
# ---------------------------------------------------------------------------

_MOCK_EXPLANATION = (
    "This is a mock explanation. "
    "In a real session the AI would explain the topic in simple language "
    "tailored for a beginner."
)

_MOCK_QUIZ: list[dict] = [
    {
        "type": "mcq",
        "question": "Which of the following best describes a variable?",
        "options": [
            "A fixed constant value",
            "A named storage location in memory",
            "A type of loop",
            "A function parameter",
        ],
        "answer": "A named storage location in memory",
    },
    {
        "type": "truefalse",
        "question": "Python is a compiled language.",
        "options": ["True", "False"],
        "answer": "False",
    },
    {
        "type": "mcq",
        "question": "What does OOP stand for?",
        "options": [
            "Object-Oriented Programming",
            "Open Output Processing",
            "Operational Order Protocol",
            "None of the above",
        ],
        "answer": "Object-Oriented Programming",
    },
    {
        "type": "truefalse",
        "question": "A function can return multiple values in Python.",
        "options": ["True", "False"],
        "answer": "True",
    },
    {
        "type": "mcq",
        "question": "Which keyword is used to define a function in Python?",
        "options": ["func", "define", "def", "function"],
        "answer": "def",
    },
]

_MOCK_REVISION_STEPS = [
    "Read through all study material once without taking notes.",
    "Write down the key terms and their meanings in your own words.",
    "Review any diagrams or examples in the material.",
    "Attempt the practice quiz to test your understanding.",
    "Revisit topics where you scored below 70%.",
    "Summarise the entire topic in 5 bullet points.",
    "Do a final review 24 hours later to strengthen memory.",
]

_MOCK_DOUBT_ANSWER = (
    "This is a mock answer. "
    "In a real session the AI would provide a concise, beginner-friendly "
    "explanation of your specific question based on the study material."
)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

def _explain_prompt(topic: str, material: str) -> str:
    return (
        "You are a friendly tutor helping a first-year computer science student. "
        f"Explain the topic '{topic}' in simple, beginner-friendly language "
        "using the following study material as context. "
        "Keep the explanation under 200 words and avoid jargon.\n\n"
        f"Study material:\n{material}"
    )


def _quiz_prompt(material: str, num_questions: int) -> str:
    schema_example = json.dumps(
        [
            {
                "type": "mcq",
                "question": "Sample question?",
                "options": ["A", "B", "C", "D"],
                "answer": "B",
            }
        ],
        indent=2,
    )
    return (
        f"Generate exactly {num_questions} quiz questions from the study material below. "
        "Mix multiple-choice (MCQ) and True/False questions. "
        "For MCQ questions provide exactly 4 options. "
        "For True/False questions the options must be exactly [\"True\", \"False\"]. "
        "Return ONLY a valid JSON array — no extra text, no markdown, no code fences. "
        f"Use this exact schema for each element:\n{schema_example}\n\n"
        f"Study material:\n{material}"
    )


def _doubt_prompt(doubt: str, material: str) -> str:
    return (
        "You are a helpful study assistant. "
        "A student has the following study material:\n"
        f"{material}\n\n"
        f"The student's question is: {doubt}\n\n"
        "Answer briefly and simply in 3–5 sentences suitable for a beginner."
    )


def _revision_prompt(topic: str, material: str, hours: float) -> str:
    return (
        f"Create a practical revision plan for the topic '{topic}'. "
        f"The student has {hours} hour(s) available. "
        "Return a plain numbered list of study steps — no headers, no markdown, "
        "no extra commentary. Each step on its own line.\n\n"
        f"Study material:\n{material}"
    )


# ---------------------------------------------------------------------------
# IBM Bob backend
# ---------------------------------------------------------------------------

def _call_ibm_bob(prompt: str, model: str) -> str:
    """Call the IBM Bob API. Reads credentials from environment variables."""
    import requests  # local import keeps the module importable without requests

    api_key = os.environ["IBM_BOB_API_KEY"]
    base_url = os.environ.get(
        "IBM_BOB_URL", "https://us-south.ml.cloud.ibm.com"
    ).rstrip("/")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model_id": model,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 1024,
            "temperature": 0.7,
        },
    }
    response = requests.post(
        f"{base_url}/ml/v1/text/generation",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    # IBM watsonx.ai / Bob response shape
    return data["results"][0]["generated_text"].strip()


# ---------------------------------------------------------------------------
# Ollama backend
# ---------------------------------------------------------------------------

def _call_ollama(prompt: str, model: str, base_url: str) -> str:
    """Call the local Ollama API."""
    import requests

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    response = requests.post(
        f"{base_url}/api/generate",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


# ---------------------------------------------------------------------------
# AIService class
# ---------------------------------------------------------------------------

class AIService:
    """Unified AI service that wraps IBM Bob, Ollama, or a Mock backend.

    Parameters
    ----------
    model:
        Model name.  For Ollama this is e.g. ``"llama3"``.
        For IBM Bob this is e.g. ``"ibm/granite-13b-instruct-v2"``.
        Ignored when using the Mock backend.
    ollama_url:
        Base URL for Ollama.  Defaults to ``OLLAMA_URL`` env var or
        ``http://localhost:11434``.
    """

    def __init__(
        self,
        model: str = "llama3",
        ollama_url: str | None = None,
    ) -> None:
        self._model = model
        self._ollama_url = (
            ollama_url
            or os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        )

        if _mock_forced():
            self._backend = "mock"
        elif _ibm_bob_configured():
            self._backend = "ibm_bob"
        else:
            self._backend = "ollama"

    @property
    def backend(self) -> str:
        """Name of the active backend: ``"mock"``, ``"ibm_bob"``, or ``"ollama"``."""
        return self._backend

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call(self, prompt: str) -> str:
        """Dispatch to the configured backend and return the raw text response."""
        if self._backend == "mock":
            return "[MOCK RESPONSE]"
        if self._backend == "ibm_bob":
            return _call_ibm_bob(prompt, self._model)
        return _call_ollama(prompt, self._model, self._ollama_url)

    @staticmethod
    def _parse_quiz_json(raw: str) -> list[dict]:
        """Extract a JSON array from *raw*, stripping markdown fences if present."""
        # Strip code fences like ```json ... ```
        clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        # Find the first '[' and last ']'
        start = clean.find("[")
        end = clean.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("No JSON array found in AI response.")
        return json.loads(clean[start : end + 1])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(self, topic: str, material: str) -> str:
        """Return a plain-English explanation of *topic* using *material*."""
        if self._backend == "mock":
            return _MOCK_EXPLANATION
        prompt = _explain_prompt(topic, material)
        return self._call(prompt)

    def generate_quiz(
        self, material: str, num_questions: int = 5
    ) -> list[dict]:
        """Return a list of question dicts generated from *material*.

        Raises ``ValueError`` if the AI response cannot be parsed as JSON.
        """
        if self._backend == "mock":
            return _MOCK_QUIZ[:num_questions]
        prompt = _quiz_prompt(material, num_questions)
        raw = self._call(prompt)
        return self._parse_quiz_json(raw)

    def solve_doubt(self, doubt: str, material: str) -> str:
        """Return a short answer to *doubt* using *material* as context."""
        if self._backend == "mock":
            return _MOCK_DOUBT_ANSWER
        prompt = _doubt_prompt(doubt, material)
        return self._call(prompt)

    def generate_revision_plan(
        self, topic: str, material: str, hours: float = 2.0
    ) -> list[str]:
        """Return an ordered list of study steps for *topic*.

        Each element is one plain-text step.
        """
        if self._backend == "mock":
            return _MOCK_REVISION_STEPS
        prompt = _revision_prompt(topic, material, hours)
        raw = self._call(prompt)
        steps = [line.strip() for line in raw.splitlines() if line.strip()]
        return steps
