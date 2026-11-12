"""Adaptive question-and-answer flow with live hypothesis updates and a reasoning timeline."""
import streamlit as st

from expert_system import hypothesis_manager
from expert_system.input_parser import BOOLEAN_CHOICES, parse_numeric_answer
from expert_system.knowledge_loader import load_kb
from config import MAX_QUESTIONS, MIN_QUESTIONS_TO_VIEW_RESULTS
from ui.components import badge, bar, esc, go, header, html, table
from ui.state import required_answers_remaining, require_data, rs

kb = load_kb()


def _answer_widget(s, fid, key):
    """Renders the right input for the question type and records the answer when submitted."""
    spec = kb.facts[fid]
    kind = spec["type"]
    if kind == "boolean":
        choice = st.radio("Your answer", [c[0] for c in BOOLEAN_CHOICES], index=None, key=f"ans_{key}")
        if st.button("Submit answer", type="primary", key=f"sub_{key}"):
            if choice is None:
                st.warning("Please choose an answer, or pick 'Not sure / don't know'.")
                return
            _, value, cert = next(c for c in BOOLEAN_CHOICES if c[0] == choice)
            s.answer(fid, value, cert, choice)
            st.rerun()
    elif kind == "ordinal":
        choice = st.radio("Your answer", spec["options"] + ["Not sure / don't know"], index=None, key=f"ans_{key}")
        if st.button("Submit answer", type="primary", key=f"sub_{key}"):
            if choice is None:
                st.warning("Please choose an answer.")
                return
            s.answer(fid, None if choice.startswith("Not sure") else choice, 1.0, choice)
            st.rerun()
    else:
        text = st.text_input("Your answer (a number e.g. 15 or 15%)", key=f"ans_{key}")
        c1, c2, _ = st.columns([1, 1.4, 3])
        if c1.button("Submit answer", type="primary", key=f"sub_{key}"):
            value, cert, status = parse_numeric_answer(text, spec.get("qualitative"))
            if status == "invalid":
                st.warning("I did not understand that. Type a number (e.g. 15 or 15%).")
                return
            if status == "unknown":
                s.answer(fid, None, 1.0, "Don't know")
            else:
                s.answer(fid, value, cert, text + (" (approximate)" if status == "approximate" else ""))
            st.rerun()
        if c2.button("Skip: I don't know", key=f"skip_{key}"):
            s.answer(fid, None, 1.0, "Don't know")
            st.rerun()


def _question_card(s, q):
    """Render either the next evidence-seeking question or a disputed-answer clarification."""
    spec = kb.facts[q["fact"]]
    n = len(s.asked) + 1
    if q["type"] == "clarify":
        html(f'<div class="bs-q"><div class="n">Please clarify</div><div class="t">{esc(spec.get("question", spec["label"]))}</div></div>')
        st.warning(q["reason"])
        mine = s.answers.get(q["fact"], {}).get("text") or s.raw.get(q["fact"])
        st.write(f"Your current answer: **{mine}**")
        keep = st.radio("What would you like to do?", ["I want to change my answer", "Keep my answer (it is correct)"], index=None, key=f"clar_{q['fact']}_{n}")
        if keep and keep.startswith("Keep"):
            if st.button("Confirm my answer", type="primary", key=f"conf_{q['fact']}_{n}"):
                s.confirm(q["fact"])
                st.rerun()
        elif keep:
            _answer_widget(s, q["fact"], f"{q['fact']}_{n}_re")
        return
    html(f'<div class="bs-q"><div class="n">Question {n} of up to {MAX_QUESTIONS} · {MIN_QUESTIONS_TO_VIEW_RESULTS} answers unlock findings</div><div class="t">{esc(spec["question"])}</div></div>')
    with st.expander("Why am I being asked this?"):
        st.write(q["why"])
    _answer_widget(s, q["fact"], f"{q['fact']}_{n}")


def _live_panel(s):
    """Keep current evidence visible beside the question so reasoning is not a black box."""
    st.markdown("##### Live reasoning")
    top = [h for h in hypothesis_manager.ranked(s.state["hypotheses"]) if h.net is not None][:6]
    for h in top:
        html(f'<div class="bs-card bs-live-finding"><div class="bs-live-finding-head"><b style="font-size:.85rem;min-width:0;overflow-wrap:anywhere">{esc(h.name)}</b>{badge(h.label, h.tone)}</div>{bar(max(h.score, 0) * 100, h.score < 0)}</div>')
    st.caption("Bars update after every answer. Red bars mean the evidence is against that cause.")


def _timeline(s):
    """Summarize how each answer moved the hypotheses, newest change first."""
    if not s.steps:
        return
    st.markdown("##### Reasoning timeline (newest first)")
    rows = []
    for step in reversed(s.steps):
        changes = ""
        for c in step["changes"][:5]:
            b = "new" if c["before"] is None else f"{c['before'] * 100:+.0f}"
            a = "-" if c["after"] is None else f"{c['after'] * 100:+.0f}"
            tone = {"up": "success", "down": "warn", "new": "info"}[c["direction"]]
            changes += badge(f"{c['hypothesis'][:34]}: {b} to {a}", tone)
        rows.append([str(step["n"]), esc(step["question"]), esc(step["answer"]), changes or '<span class="bs-muted">no change</span>'])
    table(rows, ["#", "Question", "Your answer", "How the findings changed (score -100..+100)"])


def render():
    """Coordinate the investigation state, question, progress, and live findings."""
    header("Investigation", "BizSage asks only the questions that help separate possible causes. Answer honestly; 'not sure' is always allowed.")
    require_data()
    s = rs()
    left, right = st.columns([2, 1], gap="large")
    with left:
        reason = s.termination()
        if reason:
            html(f'<div class="bs-card"><h4>Investigation complete {badge("done", "success")}</h4><p>{esc(reason)}</p><p>{esc(s.summary_text())}</p></div>')
            c1, c2, c3 = st.columns(3)
            with c1:
                remaining = required_answers_remaining(s)
                go(
                    "results",
                    "Review findings and options" if remaining == 0 else "Answer more investigation questions",
                    primary=True,
                    disabled=remaining > 0,
                )
                if remaining:
                    st.caption(f"Answer {remaining} more question(s) to unlock findings and options.")
            with c2:
                go("business", "Update business information")
            with c3:
                if st.button("Start the questions again"):
                    s.reset_investigation()
                    st.rerun()
        else:
            q = s.current_question()
            if q is None:
                st.info("No question is available yet. Add more details on the Business information page.")
            else:
                _question_card(s, q)
                if len(s.asked) >= MIN_QUESTIONS_TO_VIEW_RESULTS and st.button("Finish the investigation now", key="finish_now"):
                    s.finish()
                    st.rerun()
                elif len(s.asked) < MIN_QUESTIONS_TO_VIEW_RESULTS:
                    st.caption(
                        f"Answer at least {MIN_QUESTIONS_TO_VIEW_RESULTS} questions to unlock findings "
                        f"({len(s.asked)} answered so far)."
                    )
        if s.steps:
            with st.expander("How answers changed the findings"):
                _timeline(s)
    with right:
        _live_panel(s)
        comp = s.state["completeness"]["completeness_pct"]
        html(f'<div class="bs-card"><h4>Progress</h4><p>Questions answered: <b>{len(s.asked)}</b> of up to {MAX_QUESTIONS}</p></div>')
