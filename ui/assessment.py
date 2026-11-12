"""Collect this month's numeric or qualitative business measures and show data readiness."""
import streamlit as st

from expert_system.input_parser import parse_numeric_answer
from expert_system.knowledge_loader import load_kb
from ui.components import go, header, kpi_row, note
from ui.state import rs

kb = load_kb()


def _fmt(v):
    """Keep unknown values blank instead of displaying them as zero."""
    return "" if v is None else f"{v:g}"


def render(show_header=True):
    """Render the assessment form and pass valid values to the reasoning session."""
    if show_header:
        header("Financial assessment", "Enter this month's figures. You can type numbers (450000, 4.5 lac, 18%) or, where allowed, words like low, medium or high.")
    s = rs()
    sections = []
    for fid, spec in kb.inputs.items():
        if spec["section"] not in sections:
            sections.append(spec["section"])
    with st.form("assessment_form"):
        tabs = st.tabs(sections)
        for tab, sec in zip(tabs, sections):
            with tab:
                cols = st.columns(2)
                n = 0
                for fid, spec in kb.inputs.items():
                    if spec["section"] != sec:
                        continue
                    label = spec["label"] + (" (optional)" if spec.get("optional") else "") + (f" [{spec['unit']}]" if spec.get("unit") else "")
                    hint = "Numbers or words (low / medium / high)" if spec.get("qualitative") else None
                    cols[n % 2].text_input(label, value=_fmt(s.raw.get(fid)), key=f"in_{fid}", help=hint)
                    n += 1
        submitted = st.form_submit_button("Save this month's figures", type="primary")
    if submitted:
        # Parse each field independently so one invalid answer does not discard the others.
        raw, cert, errors = {}, {}, []
        for fid, spec in kb.inputs.items():
            text = st.session_state.get(f"in_{fid}", "")
            if not text.strip():
                continue
            value, c, status = parse_numeric_answer(text, spec.get("qualitative"))
            if status in ("ok", "approximate"):
                raw[fid], cert[fid] = value, c
            elif status == "invalid":
                errors.append(f"'{spec['label']}': \"{text}\" is not a number I understand, so it was left unknown.")
        s.set_inputs(raw=raw)
        s.raw_certainty.update(cert)
        s.analyze()
        st.success("Figures saved and checked.")
        for e in errors:
            st.warning(e)
        for i in s.state["issues"]:
            (st.warning if i.severity in ("error", "warning") else st.info)(i.message)
    if s.state:
        comp = s.state["completeness"]
        kpi_row([{"label": "Data completeness", "value": f"{comp['completeness_pct']}%", "hint": "Higher means fewer rules are skipped"},
                 {"label": "Required fields missing", "value": len(comp["missing_required"])},
                 {"label": "Rules waiting for data", "value": s.state["result"].counts()["UNKNOWN"]}])
        if comp["missing_required"]:
            with st.expander("What is still missing?"):
                st.write(", ".join(comp["missing_required"]))
        go("investigation", "Go to the investigation", primary=True)
    note("Leave optional boxes empty if you do not know the figure. BizSage will not guess: rules that need it simply wait, and the Investigation Centre may ask you about it.", "Missing data")
