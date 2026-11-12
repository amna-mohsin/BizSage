"""Generate a human-readable rule listing from the validated JSON knowledge base.

Run ``python tools/generate_kb_doc.py`` after changing rule data; generated output is
for review and viva preparation, while the JSON remains the source of truth.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from expert_system.knowledge_loader import load_kb  # noqa: E402
from expert_system.rule_tools import describe_condition  # noqa: E402

# Use the same loader and condition formatter as the runtime to avoid documentation drift.
kb = load_kb()
names = {k: v["name"] for k, v in kb.hypotheses.items()}
out = ["# Knowledge Base listing", "",
       "Generated automatically from `knowledge_base/*.json`. Thresholds are expert-assigned starting values (see `knowledge_base/thresholds.json`), "
       "not universal standards; they must be validated with a restaurant owner or accountant.", "",
       f"- Total rules: **{len(kb.rules)}** ({len(kb.diagnostic_rules)} unique diagnostic conditions, "
       f"{sum(r['kind'] == 'exclusion' for r in kb.rules)} exclusion rules, {sum(r['kind'] == 'chained' for r in kb.rules)} chained rules)",
       f"- Hypotheses: {len(kb.hypotheses)}; askable questions: {len(kb.askable_facts())}; consistency checks: {len(kb.consistency)}", "",
       "## Hypotheses", ""]
for hid, h in kb.hypotheses.items():
    out.append(f"- **{hid}** {h['name']} ({h['category']}): {h['investigate']}")
order = []
for r in kb.rules:
    if r["category"] not in order:
        order.append(r["category"])
for cat in order:
    out += ["", f"## {cat}", "", "| ID | Condition | Fires when | Effect on hypotheses |", "|---|---|---|---|"]
    for r in [x for x in kb.rules if x["category"] == cat]:
        when = " AND ".join(describe_condition(c, kb.facts) for c in r["conditions"])
        eff = "; ".join(f"{names[e['hypothesis']]} ({e['cf']:+.2f}{', group ' + e['group'] if e.get('group') else ''})" for e in r["effects"])
        out.append(f"| {r['id']} | {r['name']} | {when} | {eff} |")
out += ["", "## Consistency checks (contradiction detection)", "", "| ID | Severity | Fires when |", "|---|---|---|"]
for ck in kb.consistency:
    out.append(f"| {ck['id']} | {ck['severity']} | " + " AND ".join(describe_condition(c, kb.facts) for c in ck["conditions"]) + " |")
(ROOT / "docs" / "knowledge_base.md").write_text("\n".join(out), encoding="utf-8")
print("written docs/knowledge_base.md")
