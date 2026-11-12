"""Shared dark visual theme and responsive CSS for desktop and phone layouts."""
import streamlit as st

P = dict(bg="#0B1220", side="#101B2D", card="#162337", card2="#1C2B40", border="#2A3B54", accent="#20B99A", accent2="#7C83F6",
         ok="#43C59E", warn="#F2BD65", bad="#F07883", text="#EDF3FA", muted="#9AABC0")

CSS = """
<style>
.stApp{background:%(bg)s;color:%(text)s;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
.block-container{padding-top:1.6rem;padding-bottom:4rem;max-width:1220px}
h1,h2,h3,h4,h5{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important;letter-spacing:-.01em}
[data-testid="stSidebar"]{background:%(side)s;border-right:1px solid %(border)s}
[data-testid="stHeader"]{background:transparent}
[data-testid="stPageLink-NavLink"]{border-radius:10px}
[data-testid="stPageLink-NavLink"][aria-current="page"]{background:%(card2)s;border:1px solid %(border)s}
.bs-id{display:flex;gap:1.2rem;flex-wrap:wrap;align-items:center;justify-content:space-between;background:%(card)s;border:1px solid %(border)s;border-radius:12px;padding:.55rem 1rem;margin-bottom:1rem;font-size:.82rem;color:%(muted)s}
.bs-id b{color:%(text)s}
.bs-brand{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-weight:800;font-size:1.35rem;letter-spacing:.02em;color:%(text)s}
.bs-brand i{font-style:normal;color:%(accent)s}
.bs-tag{font-size:.68rem;letter-spacing:.16em;color:%(muted)s;text-transform:uppercase}
.bs-title{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.9rem;font-weight:800;letter-spacing:-.02em;color:%(text)s;line-height:1.15}
.bs-sub{color:%(muted)s;margin:.25rem 0 1.2rem}
.bs-card{background:%(card)s;border:1px solid %(border)s;border-radius:14px;padding:1rem 1.2rem;margin-bottom:.8rem;min-width:0}
.bs-card h4{margin:0 0 .35rem;font-size:1rem;color:%(text)s}
.bs-card p,.bs-muted{color:%(muted)s;font-size:.9rem;margin:.15rem 0}
.bs-finding-head,.bs-live-finding-head{display:flex;align-items:flex-start;justify-content:space-between;gap:.45rem;flex-wrap:wrap;min-width:0}
.bs-finding-head h4{flex:1 1 11rem;min-width:0;overflow-wrap:anywhere}
.bs-badges{display:flex;flex:0 1 auto;flex-wrap:wrap;gap:.15rem;min-width:0}
.bs-kpi .l{color:%(muted)s;font-size:.74rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.bs-kpi .v{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.9rem;font-weight:800;font-variant-numeric:tabular-nums;color:%(text)s;line-height:1.15}
.bs-kpi .h{color:%(muted)s;font-size:.78rem}
.bs-badge{display:inline-block;padding:.25rem .6rem;border-radius:999px;font-size:.74rem;font-weight:600;margin:.1rem .15rem .1rem 0;border:1px solid transparent;white-space:normal;overflow-wrap:anywhere;line-height:1.35}
.t-success{color:%(ok)s;background:rgba(67,197,158,.13);border-color:rgba(67,197,158,.4)}
.t-warn{color:%(warn)s;background:rgba(242,189,101,.13);border-color:rgba(242,189,101,.4)}
.t-danger{color:%(bad)s;background:rgba(240,120,131,.13);border-color:rgba(240,120,131,.4)}
.t-info{color:%(accent2)s;background:rgba(124,131,246,.14);border-color:rgba(124,131,246,.4)}
.t-neutral{color:%(muted)s;background:%(card2)s;border-color:%(border)s}
.bs-bar{height:8px;background:%(card2)s;border-radius:99px;overflow:hidden;margin:.3rem 0}
.bs-bar>div{height:100%%;border-radius:99px;background:linear-gradient(90deg,%(accent)s,%(accent2)s)}
.bs-bar.bad>div{background:linear-gradient(90deg,%(bad)s,%(warn)s)}
.bs-hero{background:radial-gradient(700px 300px at 0%% 0%%,rgba(32,185,154,.18),transparent 60%%),radial-gradient(600px 300px at 100%% 0%%,rgba(124,131,246,.18),transparent 60%%),%(card)s;border:1px solid %(border)s;border-radius:18px;padding:1.4rem 1.6rem;margin-bottom:1rem}
.bs-note{border-left:4px solid %(accent)s;background:%(card2)s;border-radius:10px;padding:.7rem 1rem;margin:.3rem 0 1rem;font-size:.9rem}
.bs-q{background:%(card)s;border:1px solid %(accent)s;border-radius:16px;padding:1.1rem 1.3rem;margin-bottom:.8rem}
.bs-q .n{color:%(accent)s;font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700}
.bs-q .t{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.25rem;font-weight:700;margin:.3rem 0}
.bs-table{width:100%%;border-collapse:collapse;font-size:.86rem}
.bs-table th{text-align:left;color:%(muted)s;font-weight:600;font-size:.74rem;padding:.5rem .6rem;border-bottom:1px solid %(border)s}
.bs-table td{padding:.55rem .6rem;border-bottom:1px solid %(border)s;vertical-align:top}
[data-testid="stBaseButton-primary"]{background:linear-gradient(90deg,%(accent)s,#18A085)!important;border:none!important;color:#06231D!important;font-weight:700}
.stButton>button,.stDownloadButton>button{border-radius:10px;font-weight:600}
@media (max-width:768px){
  .bs-title{font-size:1.45rem}
  .bs-kpi .v{font-size:1.5rem}
  .block-container{padding-left:.8rem;padding-right:.8rem}
  [data-testid="stHorizontalBlock"]{flex-direction:column!important;gap:.5rem!important}
  [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{width:100%%!important;min-width:100%%!important;flex:1 1 100%%!important}
  .st-key-bs-kpi-row [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem!important}
  .st-key-bs-kpi-row [data-testid="stColumn"]{width:auto!important;min-width:0!important;flex:initial!important}
  [data-testid="stTabs"] [role="tablist"]{overflow-x:auto;flex-wrap:nowrap}
  [data-testid="stTabs"] [role="tab"]{white-space:nowrap;flex-shrink:0}
  .bs-id{align-items:flex-start;gap:.45rem}
  .bs-card{padding:.85rem}
}
</style>
"""


def inject_css() -> None:
    """Interpolate palette values into the CSS template and inject it into Streamlit."""
    # Literal CSS percentages are doubled in CSS so Python's %-formatting leaves them intact.
    st.markdown(CSS % P, unsafe_allow_html=True)
