"""app.py — Streamlit UI entry point.

This file contains ONLY UI code.  All business logic lives in the other
modules (ai_service, quiz, revision_plan, storage, validator).

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import os
import sys

import streamlit as st

# Allow running from the project root or from within ai_study_buddy/
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from ai_service import AIService
from quiz import Quiz
from revision_plan import RevisionPlan
from storage import Storage
from validator import (
    validate_doubt,
    validate_material,
    validate_study_time,
    validate_topic,
)

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults: dict = {
        "quiz_obj": None,          # Quiz instance
        "quiz_submitted": False,   # whether the user has submitted answers
        "quiz_user_answers": {},   # {question_index: selected_option}
        "material": "",            # last entered study material
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ Settings")

    backend_info = st.empty()

    model_name = st.text_input(
        "Ollama model",
        value="llama3",
        help="Only used when the Ollama backend is active.",
    )

    st.markdown("---")
    st.markdown("**AI Backend**")

    use_mock = st.checkbox(
        "Use Mock (offline / testing)",
        value=os.environ.get("AI_MOCK", "") == "1",
        help="Enable to run without any AI service — returns sample responses.",
    )
    if use_mock:
        os.environ["AI_MOCK"] = "1"
    else:
        os.environ.pop("AI_MOCK", None)

    ai = AIService(model=model_name)
    storage = Storage(os.path.join(_HERE, "data", "storage.json"))

    backend_label = {"mock": "🟡 Mock", "ibm_bob": "🔵 IBM Bob", "ollama": "🟢 Ollama"}
    st.info(f"Active backend: **{backend_label.get(ai.backend, ai.backend)}**")

    if ai.backend == "ibm_bob":
        st.success("IBM Bob credentials detected from environment variables.")
    elif ai.backend == "ollama":
        st.caption(
            f"Connecting to Ollama at `{os.environ.get('OLLAMA_URL', 'http://localhost:11434')}`"
        )

    st.markdown("---")
    st.markdown(
        "📖 [README & Setup](https://github.com/) · Made for B.Tech CSE students"
    )

# ---------------------------------------------------------------------------
# Main content — tabs
# ---------------------------------------------------------------------------

st.title("📚 AI Study Buddy")
st.caption("Your personal AI-powered learning assistant")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📖 Explain Topic", "🧪 Quiz", "📅 Revision Plan", "🙋 Ask a Doubt", "📊 History"]
)

# ===========================================================================
# Tab 1 — Explain Topic
# ===========================================================================

with tab1:
    st.header("Explain a Topic")
    st.write(
        "Paste your study material below, enter a topic, and get a simple explanation."
    )

    material_1 = st.text_area(
        "Study material",
        height=200,
        placeholder="Paste your notes, textbook paragraph, or any study text here…",
        key="material_tab1",
    )
    topic_1 = st.text_input(
        "Topic to explain",
        placeholder="e.g. Recursion, Photosynthesis, Newton's First Law…",
        key="topic_tab1",
    )

    if st.button("💡 Get Explanation", key="btn_explain"):
        err_m = validate_material(material_1)
        err_t = validate_topic(topic_1)
        if err_m:
            st.warning(err_m)
        elif err_t:
            st.warning(err_t)
        else:
            with st.spinner("Generating explanation…"):
                try:
                    explanation = ai.explain(topic=topic_1, material=material_1)
                    st.session_state["material"] = material_1
                    st.success("Here is your explanation:")
                    st.markdown(explanation)
                except Exception as exc:
                    st.error(f"Could not get explanation: {exc}")

# ===========================================================================
# Tab 2 — Quiz
# ===========================================================================

with tab2:
    st.header("Practice Quiz")
    st.write(
        "Generate quiz questions from your study material, answer them, "
        "and see your score with feedback."
    )

    material_2 = st.text_area(
        "Study material",
        height=180,
        placeholder="Paste your study text here…",
        key="material_tab2",
    )

    num_q = st.slider("Number of questions", min_value=3, max_value=10, value=5)

    col_gen, col_reset = st.columns([1, 1])
    with col_gen:
        if st.button("🎯 Generate Quiz", key="btn_gen_quiz"):
            err_m = validate_material(material_2)
            if err_m:
                st.warning(err_m)
            else:
                with st.spinner("Generating quiz questions…"):
                    try:
                        questions = ai.generate_quiz(material_2, num_questions=num_q)
                        st.session_state["quiz_obj"] = Quiz(questions)
                        st.session_state["quiz_submitted"] = False
                        st.session_state["quiz_user_answers"] = {}
                        st.session_state["material"] = material_2
                    except ValueError as exc:
                        st.error(
                            f"Could not parse quiz from AI response: {exc}\n\n"
                            "Try again — the AI occasionally returns malformed output."
                        )
                    except Exception as exc:
                        st.error(f"Could not generate quiz: {exc}")

    with col_reset:
        if st.button("🔄 Clear Quiz", key="btn_clear_quiz"):
            st.session_state["quiz_obj"] = None
            st.session_state["quiz_submitted"] = False
            st.session_state["quiz_user_answers"] = {}

    quiz: Quiz | None = st.session_state["quiz_obj"]

    if quiz is not None:
        st.markdown("---")
        st.subheader("Answer the Questions")

        with st.form("quiz_form"):
            for i, q in enumerate(quiz.questions):
                st.markdown(f"**Q{i + 1}. {q['question']}**")
                selected = st.radio(
                    label=f"q{i}",
                    options=q["options"],
                    index=None,
                    key=f"q_radio_{i}",
                    label_visibility="collapsed",
                )
                st.session_state["quiz_user_answers"][i] = selected

            submitted = st.form_submit_button("✅ Submit Answers")

        if submitted:
            # Validate all questions are answered
            unanswered = [
                i
                for i, ans in st.session_state["quiz_user_answers"].items()
                if ans is None
            ]
            if unanswered:
                st.warning(
                    f"Please answer all questions. "
                    f"Question(s) {[u + 1 for u in unanswered]} are unanswered."
                )
            else:
                for i, ans in st.session_state["quiz_user_answers"].items():
                    quiz.set_answer(i, ans)
                st.session_state["quiz_submitted"] = True

        if st.session_state["quiz_submitted"]:
            result = quiz.score()
            st.markdown("---")
            st.subheader("📊 Your Score")
            st.metric(
                "Score",
                f"{result['correct']} / {result['total']}",
                f"{result['percentage']}%",
            )

            # Save to storage
            try:
                storage.save_quiz_score(result)
            except Exception:
                pass  # non-critical

            # Per-question feedback
            st.subheader("📝 Feedback")
            for fb in quiz.feedback():
                icon = "✅" if fb["is_correct"] else "❌"
                with st.expander(f"{icon} {fb['question']}"):
                    if fb["is_correct"]:
                        st.success(f"Correct! Your answer: **{fb['user_answer']}**")
                    else:
                        st.error(
                            f"Your answer: **{fb['user_answer']}**  \n"
                            f"Correct answer: **{fb['correct_answer']}**"
                        )

# ===========================================================================
# Tab 3 — Revision Plan
# ===========================================================================

with tab3:
    st.header("Revision Plan")
    st.write("Generate a personalised study plan from your material.")

    material_3 = st.text_area(
        "Study material",
        height=180,
        placeholder="Paste your study text here…",
        key="material_tab3",
    )
    topic_3 = st.text_input(
        "Topic name (used to save and label the plan)",
        placeholder="e.g. Data Structures, Organic Chemistry…",
        key="topic_tab3",
    )
    hours_3 = st.number_input(
        "Study hours available",
        min_value=0.5,
        max_value=24.0,
        value=2.0,
        step=0.5,
    )

    if st.button("📅 Generate Revision Plan", key="btn_revision"):
        err_m = validate_material(material_3)
        err_t = validate_topic(topic_3)
        err_h = validate_study_time(hours_3)
        if err_m:
            st.warning(err_m)
        elif err_t:
            st.warning(err_t)
        elif err_h:
            st.warning(err_h)
        else:
            with st.spinner("Generating revision plan…"):
                try:
                    steps = ai.generate_revision_plan(
                        topic=topic_3, material=material_3, hours=hours_3
                    )
                    plan = RevisionPlan(topic=topic_3, steps=steps)
                    storage.save_revision_plan(plan)
                    st.success(f"Revision plan for **{topic_3}** saved!")
                    st.subheader("Your Study Plan")
                    for i, step in enumerate(plan.steps, start=1):
                        st.write(f"{i}. {step}")
                except Exception as exc:
                    st.error(f"Could not generate revision plan: {exc}")

    # Saved plans expander
    with st.expander("📂 View Saved Revision Plans"):
        saved_plans = storage.load_revision_plans()
        if not saved_plans:
            st.info("No revision plans saved yet.")
        else:
            for p in saved_plans:
                st.markdown(f"**{p['topic']}** — saved {p.get('timestamp', '')}")
                for j, step in enumerate(p.get("steps", []), start=1):
                    st.write(f"  {j}. {step}")
                st.markdown("---")

# ===========================================================================
# Tab 4 — Ask a Doubt
# ===========================================================================

with tab4:
    st.header("Ask a Doubt")
    st.write(
        "Have a question about your study material? "
        "Type it below and get a simple explanation."
    )

    material_4 = st.text_area(
        "Study material (optional — paste for better answers)",
        height=140,
        placeholder="Paste your study text here for context (optional)…",
        key="material_tab4",
    )
    doubt_4 = st.text_input(
        "Your question",
        placeholder="e.g. What is the difference between a list and a tuple in Python?",
        key="doubt_tab4",
    )

    if st.button("🙋 Ask", key="btn_ask"):
        err_d = validate_doubt(doubt_4)
        if err_d:
            st.warning(err_d)
        else:
            context = material_4.strip() or "No specific study material provided."
            with st.spinner("Finding an answer…"):
                try:
                    answer = ai.solve_doubt(doubt=doubt_4, material=context)
                    st.success("Here is the answer:")
                    st.markdown(answer)
                except Exception as exc:
                    st.error(f"Could not get an answer: {exc}")

# ===========================================================================
# Tab 5 — History
# ===========================================================================

with tab5:
    st.header("Quiz Score History")
    st.write("All your past quiz results are shown here.")

    scores = storage.load_quiz_scores()
    if not scores:
        st.info("No quiz scores saved yet. Take a quiz in the **Quiz** tab!")
    else:
        for entry in scores:
            col1, col2, col3 = st.columns(3)
            col1.metric("Score", f"{entry.get('correct', '?')} / {entry.get('total', '?')}")
            col2.metric("Percentage", f"{entry.get('percentage', '?')}%")
            col3.caption(f"🕐 {entry.get('timestamp', 'unknown')}")
            st.markdown("---")

    if st.button("🗑️ Clear History", key="btn_clear_history"):
        try:
            s = Storage(os.path.join(_HERE, "data", "storage.json"))
            data = s._read()
            data["scores"] = []
            s._write(data)
            st.success("Quiz history cleared.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not clear history: {exc}")
