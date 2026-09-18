# AI Study Buddy — Implementation Plan

## Top-Level Overview

Build a beginner-friendly **AI Study Buddy** web app using Python, OOP, and Streamlit.
The app lets a student paste study material, then get:

- A plain-English AI explanation of the topic
- A mixed MCQ + True/False quiz generated from the material
- Scored quiz results with per-question feedback
- A numbered revision plan saved locally
- A simple doubt-solver chat box

**AI backend:** Ollama (local, free, no API key).  
**Persistence:** A single `data/storage.json` file for revision plans and quiz scores.  
**Scope constraint:** Small enough for a beginner to finish in one day. No database, no auth, no streaming.

---

## Recommended Project Structure

```
ai_study_buddy/
├── app.py                  # Streamlit entry point — UI only
├── ai_service.py           # All Ollama calls and prompt building
├── quiz.py                 # Quiz data model and scoring logic
├── revision_plan.py        # Revision plan data model
├── storage.py              # Read/write storage.json
├── validator.py            # Input validation helpers
├── data/
│   └── storage.json        # Persisted quiz scores and revision plans
└── requirements.txt
```

---

## Classes and Their Responsibilities

### `AIService` — `ai_service.py`
Owns every interaction with Ollama.

| Method | What it does |
|---|---|
| `__init__(model: str)` | Stores the chosen model name |
| `explain(topic: str, material: str) -> str` | Returns a plain-English explanation |
| `generate_quiz(material: str, num_questions: int) -> list[dict]` | Returns a list of question dicts |
| `solve_doubt(doubt: str, material: str) -> str` | Returns a short answer to a doubt |
| `generate_revision_plan(material: str) -> list[str]` | Returns a numbered list of study steps |
| `_call(prompt: str) -> str` | Private — sends the raw prompt to Ollama and returns the text |

### `Quiz` — `quiz.py`
Holds one quiz session.

| Method | What it does |
|---|---|
| `__init__(questions: list[dict])` | Stores the list of question dicts |
| `check_answer(index: int, user_answer: str) -> bool` | Returns True if correct |
| `score() -> dict` | Returns `{correct, total, percentage}` |

A question dict has the shape:
```
{
  "type": "mcq" | "truefalse",
  "question": str,
  "options": list[str],      # 4 items for MCQ, ["True","False"] for T/F
  "answer": str              # the correct option text
}
```

### `RevisionPlan` — `revision_plan.py`
Simple container for one revision plan.

| Method | What it does |
|---|---|
| `__init__(topic: str, steps: list[str])` | Stores topic and steps |
| `to_dict() -> dict` | Serialises to a plain dict for JSON storage |
| `from_dict(d: dict) -> RevisionPlan` | Class method — deserialises from dict |

### `Storage` — `storage.py`
Handles `data/storage.json`.

| Method | What it does |
|---|---|
| `__init__(path: str)` | Stores file path, creates file if missing |
| `save_quiz_score(score: dict)` | Appends a score entry with a timestamp |
| `save_revision_plan(plan: RevisionPlan)` | Appends or overwrites the plan for that topic |
| `load_quiz_scores() -> list[dict]` | Returns all saved scores |
| `load_revision_plans() -> list[dict]` | Returns all saved plans |

### `Validator` — `validator.py`
Stateless helper class (or plain functions if preferred).

| Function | What it does |
|---|---|
| `validate_material(text: str) -> str \| None` | Returns an error message or None |
| `validate_doubt(text: str) -> str \| None` | Returns an error message or None |

---

## Modules and Their Responsibilities

| Module | Role |
|---|---|
| `app.py` | Builds the Streamlit UI, reads user inputs, calls business classes, displays results. No AI or file logic here. |
| `ai_service.py` | All prompts and Ollama HTTP calls. No Streamlit imports. |
| `quiz.py` | Quiz state and scoring. No Streamlit or Ollama imports. |
| `revision_plan.py` | RevisionPlan model. No Streamlit or Ollama imports. |
| `storage.py` | JSON read/write only. |
| `validator.py` | Pure validation functions. |

---

## Data Flow

```
User Input (Streamlit)
        |
        v
   validator.py   <-- validates before anything else
        |
        v
   ai_service.py  <-- builds prompt, calls Ollama, parses response
        |
        v
 quiz.py / revision_plan.py  <-- wraps AI output in typed objects
        |
        v
   storage.py     <-- persists scores and plans
        |
        v
   app.py         <-- displays results back to user
```

---

## How the Quiz Works

1. User pastes study material and clicks **Generate Quiz**.
2. `AIService.generate_quiz()` sends a prompt asking Ollama to return JSON — a list of 5 questions (mix of MCQ and True/False).
3. The raw JSON string from Ollama is parsed with `json.loads()`. If parsing fails, a friendly error is shown.
4. A `Quiz` object is created from the parsed list.
5. Streamlit renders each question with radio buttons (options).
6. User clicks **Submit Answers**.
7. `Quiz.check_answer()` is called for each question.
8. `Quiz.score()` returns the summary.
9. Score is saved via `Storage.save_quiz_score()`.
10. Per-question feedback is shown: ✅ correct or ❌ wrong + the correct answer.

---

## How the Revision Plan Works

1. User pastes study material and clicks **Generate Revision Plan**.
2. `AIService.generate_revision_plan()` asks Ollama for a numbered list of study topics/steps.
3. The response is split by newlines to produce `list[str]`.
4. A `RevisionPlan` object is created.
5. Saved via `Storage.save_revision_plan()`.
6. Displayed as a numbered list in the UI.
7. A **View Saved Plans** expander shows all previously saved plans.

---

## How AI Prompts Are Organised

All prompts live as private string constants or small private methods inside `AIService`.  
Each feature has its own prompt template.

| Feature | Prompt strategy |
|---|---|
| Explain | "You are a friendly tutor. Explain the following in simple language for a beginner: {material}" |
| Quiz | "Generate exactly 5 quiz questions as a JSON array from this material. Mix MCQ and True/False. Use this exact schema: [...]. Return only valid JSON." |
| Doubt | "A student is studying: {material}. Their question is: {doubt}. Answer briefly and simply." |
| Revision plan | "Create a numbered revision plan (plain list, no extra text) for a student studying: {material}" |

The quiz prompt instructs Ollama to return **only valid JSON** so that `json.loads()` can parse it directly.

---

## Validation and Error-Handling Approach

**Validation (before any AI call):**
- Study material must not be empty and must be at least 50 characters.
- Doubt input must not be empty.
- Show validation messages as `st.warning()` inline — no exceptions raised.

**Error handling (during AI calls):**
- Wrap every `AIService` call in a `try/except` block in `app.py`.
- If Ollama is unreachable, show `st.error("Could not connect to Ollama. Is it running?")`.
- If quiz JSON parsing fails, show `st.error("AI returned an unexpected format. Try again.")`.
- Do not crash the app; always return gracefully.

**Storage errors:**
- If `storage.json` is malformed, reset it to `{"scores": [], "plans": []}` automatically.

---

## Streamlit UI Layout

```
Sidebar
  └── Ollama model selector (text input, default "llama3")

Main area — Tabs
  ├── Tab 1: Study Material
  │     └── Text area (paste material)
  │     └── Button: Get Explanation  → shows explanation
  │
  ├── Tab 2: Quiz
  │     └── Button: Generate Quiz    → renders questions
  │     └── Radio buttons per question
  │     └── Button: Submit Answers   → shows score + feedback
  │
  ├── Tab 3: Revision Plan
  │     └── Button: Generate Plan    → shows numbered list
  │     └── Expander: View Saved Plans
  │
  ├── Tab 4: Ask a Doubt
  │     └── Text input for doubt
  │     └── Button: Ask             → shows answer
  │
  └── Tab 5: History
        └── Quiz score history table
```

---

## Testing Strategy

No formal test framework is required for the MVP. Instead:

- **Manual smoke test:** Run `streamlit run app.py`, paste sample text, exercise every tab.
- **Validator test:** At the Python REPL, call `validate_material("")` and `validate_material("x"*50)` and confirm outputs.
- **Quiz scoring test:** Construct a `Quiz` object with hardcoded questions at the REPL and call `check_answer()` and `score()`.
- **Storage test:** Call `Storage.save_quiz_score(...)` and open `data/storage.json` to confirm the entry.

No mocking of Ollama is needed — run it locally during development.

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding
**Intent:** Create the folder structure and empty module files so every subsequent sub-task has a home.  
**Expected Outcomes:** All files and folders listed in the project structure exist. `requirements.txt` is populated. `storage.json` is initialised.  
**Todo List:**
- [ ] Create `ai_study_buddy/` directory with all sub-files
- [ ] Write `requirements.txt` (`streamlit`, `requests`)
- [ ] Initialise `data/storage.json` with `{"scores": [], "plans": []}`
- [ ] Add a `README.md` with one-line run instructions  

**Status:** `[ ] pending`

---

### Sub-Task 2 — Validator Module
**Intent:** Implement input validation so bad inputs are caught before any AI call.  
**Expected Outcomes:** `validate_material` and `validate_doubt` return the correct error strings or None.  
**Todo List:**
- [ ] Implement `validate_material(text)` — empty check + min 50 chars
- [ ] Implement `validate_doubt(text)` — empty check  

**Relevant Context:** `validator.py`  
**Status:** `[ ] pending`

---

### Sub-Task 3 — Storage Module
**Intent:** Implement JSON persistence for quiz scores and revision plans.  
**Expected Outcomes:** Scores and plans survive a page refresh and accumulate over sessions.  
**Todo List:**
- [ ] Implement `Storage.__init__` — auto-create file if missing or malformed
- [ ] Implement `save_quiz_score` and `load_quiz_scores`
- [ ] Implement `save_revision_plan` and `load_revision_plans`  

**Relevant Context:** `storage.py`, `data/storage.json`  
**Status:** `[ ] pending`

---

### Sub-Task 4 — Quiz and RevisionPlan Models
**Intent:** Build typed, testable data models for quizzes and revision plans.  
**Expected Outcomes:** `Quiz` can score answers; `RevisionPlan` serialises/deserialises cleanly.  
**Todo List:**
- [ ] Implement `Quiz` class with `check_answer` and `score`
- [ ] Implement `RevisionPlan` class with `to_dict` and `from_dict`  

**Relevant Context:** `quiz.py`, `revision_plan.py`  
**Status:** `[ ] pending`

---

### Sub-Task 5 — AI Service
**Intent:** Implement all Ollama interactions and prompt templates.  
**Expected Outcomes:** Each `AIService` method returns a usable string or list; quiz method returns a parseable JSON list.  
**Todo List:**
- [ ] Implement `_call(prompt)` using `requests.post` to Ollama's local API
- [ ] Implement `explain`, `generate_quiz`, `solve_doubt`, `generate_revision_plan`
- [ ] Write prompt templates for all four features  

**Relevant Context:** `ai_service.py`  
**Status:** `[ ] pending`

---

### Sub-Task 6 — Streamlit UI
**Intent:** Wire all modules together into the five-tab Streamlit interface.  
**Expected Outcomes:** Every feature is reachable and functional from the browser.  
**Todo List:**
- [ ] Build sidebar model selector
- [ ] Build Tab 1 — material input + explanation
- [ ] Build Tab 2 — quiz generation, answer submission, score + feedback
- [ ] Build Tab 3 — revision plan generation + saved plans expander
- [ ] Build Tab 4 — doubt input + answer display
- [ ] Build Tab 5 — quiz score history table  

**Relevant Context:** `app.py`  
**Status:** `[ ] pending`

---

## Minimum Viable Version

To finish quickly, implement in this order:  
**Sub-Task 1 → 2 → 3 → 4 → 5 → 6**

The absolute minimum to have a working app:
- Paste material, get explanation (Tab 1)
- Generate and take a quiz (Tab 2)
- Generate and save a revision plan (Tab 3)

Doubt-solving (Tab 4) and history (Tab 5) can be added last.
