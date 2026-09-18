# AI Study Buddy

A beginner-friendly AI-powered study assistant built with Python and Streamlit.

## Features

- **Explain Topic** — paste study material and get a simple AI explanation
- **Generate Quiz** — auto-generate MCQ + True/False questions from your material
- **Revision Plan** — get a numbered study plan saved between sessions
- **Doubt Solver** — ask any question about your material
- **History** — view past quiz scores

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) running locally (default), **or** IBM Bob environment variable set

## Installation

```bash
cd ai_study_buddy
pip install -r requirements.txt
```

## AI Configuration

### Option A — Ollama (local, free)
1. Install Ollama from https://ollama.com/
2. Pull a model: `ollama pull llama3`
3. Start Ollama: `ollama serve`
4. In the app sidebar, select model `llama3` (or any model you pulled)

### Option B — IBM Bob (workshop / cloud)
Set the environment variable before running:
```bash
# Windows
set IBM_BOB_API_KEY=your_key_here
set IBM_BOB_URL=https://your-bob-endpoint

# Linux / macOS
export IBM_BOB_API_KEY=your_key_here
export IBM_BOB_URL=https://your-bob-endpoint
```
The app auto-detects IBM Bob when `IBM_BOB_API_KEY` is present and uses it instead of Ollama.

### Option C — Mock / Offline mode
If neither Ollama nor IBM Bob is available, the app falls back to a built-in mock that returns
pre-written sample responses — useful for UI testing without any AI backend.

## Run

```bash
cd ai_study_buddy
streamlit run app.py
```

## Run Tests

```bash
cd ai_study_buddy
pytest tests/ -v
```

## Project Structure

```
ai_study_buddy/
├── app.py            # Streamlit UI (no AI/file logic here)
├── ai_service.py     # All AI calls and prompt templates
├── quiz.py           # Quiz data model and scoring
├── revision_plan.py  # RevisionPlan data model
├── storage.py        # JSON persistence
├── validator.py      # Input validation helpers
├── data/
│   └── storage.json  # Persisted scores and revision plans
├── tests/
│   ├── test_validator.py
│   ├── test_quiz.py
│   ├── test_revision_plan.py
│   ├── test_storage.py
│   └── test_ai_service.py
└── requirements.txt
```
