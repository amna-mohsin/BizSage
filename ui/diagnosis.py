"""Explain supported and unsupported causes, show evidence, and report data-quality limitations."""
import streamlit as st

from expert_system import hypothesis_manager
from expert_system.explanation import DISCLAIMER, hypothesis_lines
from ui.components import badge, bar, esc, go, header, html, kpi_row, note, table
from ui.state import require_data, rs


def render(show_header=True):
    """Present inference results with traceable evidence and the fired-rule audit trail."""
    if show_header:
        header("Expert diagnosis", "Every possible cause, how strongly the evidence supports it, and exactly why.")
    require_data()
    s = rs()
    stt = s.state
    hyps, concl = stt["hypotheses"], stt["conclusion"]
    tone = "warn" if concl["inconclusive"] else "success"
    html(f'<div class="bs-card"><h4>Conclusion {badge("Inconclusive" if concl["inconclusive"] else "Most supported finding found", tone)}</h4><p>{esc(s.summary_text())}</p></div>')
    note(esc(DISCLAIMER), "Please note")
    counts = stt["result"].counts()
    kpi_row([{"label": "Rules that fired", "value": counts["TRUE"], "hint": f"of {len(s.kb.rules)} rules in the knowledge base"},
             {"label": "Rules waiting for data", "value": counts["UNKNOWN"]},
             {"label": "Reasoning cycles", "value": stt["result"].cycles, "hint": "forward-chaining passes"},
             {"label": "Questions answered", "value": len(s.asked)}])
    st.markdown("##### Possible causes")
    # Causes without evidence appear separately as unexamined, not as zero-confidence diagnoses.
    shown = [h for h in hypothesis_manager.ranked(hyps) if h.net is not None]
    for h in shown:
        pct = f"{h.percent}/100" if h.score >= 0 else "against"
        html(f'<div class="bs-card"><div class="bs-finding-head"><h4>{esc(h.name)}</h4>'
             f'<div class="bs-badges">{badge(h.label, h.tone)}{badge("support " + pct, "neutral")}</div></div>{bar(max(h.score, 0) * 100, h.score < 0)}'
             f'<p>{esc(h.category)}</p></div>')
        with st.expander(f"Evidence and reasoning: {h.name}"):
            lines = hypothesis_lines(h)
            if lines["for"]:
                st.markdown("**Evidence for**")
                for t in lines["for"]:
                    st.markdown(f"- {t}")
            if lines["against"]:
                st.markdown("**Evidence against**")
                for t in lines["against"]:
                    st.markdown(f"- {t}")
            for n in lines["notes"]:
                st.caption("Redundancy handling: " + n)
            miss = stt["missing"].get(h.id)
            if miss:
                st.markdown("**Missing information that could still change this finding**")
                st.write(", ".join(miss[:8]))
            st.markdown(f"**Where to investigate:** {h.investigate}")
    if concl["unexamined"]:
        with st.expander(f"Not yet examined ({len(concl['unexamined'])})"):
            st.write(", ".join(h.name for h in concl["unexamined"]))
            st.caption("No rule has had enough data to say anything about these causes yet.")

    st.markdown("##### Data quality")
    if not stt["issues"] and not stt["conflicts"] and not stt["redundant_answers"]:
        st.success("No data problems detected.")
    for i in stt["issues"]:
        (st.error if i.severity == "error" else st.warning if i.severity == "warning" else st.info)(i.message)
    for c in stt["conflicts"]:
        confirmed = any(d in s.confirmed for d in c["disputes"]) and c["disputes"]
        st.warning(c["message"] + (" (you confirmed your answer)" if confirmed else ""))
    for fid in stt["redundant_answers"]:
        st.info(f"'{s.kb.facts[fid]['label']}' was both calculated from your figures and answered by you. The calculated value is used; your answer is kept as a duplicate.")
    comp = stt["completeness"]
    st.caption(f"Data completeness: {comp['completeness_pct']}%. Missing optional items: {len(comp['missing_optional'])}.")

    with st.expander("Rule trace: which rules fired and in which reasoning cycle"):
        rows = [[f.rule_id, esc(f.kind), esc(f.rule_name), str(f.cycle), f"{f.certainty:.2f}", esc(f.explanation)] for f in stt["result"].firings]
        table(rows, ["Rule", "Type", "Condition", "Cycle", "Certainty", "Explanation"])
    go("investigation", "Answer more questions")
