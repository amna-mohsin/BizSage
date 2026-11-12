"""Warm restaurant-inspired theme and responsive styling for desktop and mobile."""
import streamlit as st

# Chai-house palette: parchment, espresso, terracotta, saffron, and muted sage.
P = dict(
    bg="#F2E8D5",
    side="#3B2418",
    card="#FBF4E7",
    card2="#E9DDC7",
    border="#D5C4A8",
    accent="#A94E31",
    accent2="#D9A441",
    ok="#667A4E",
    warn="#A96C1E",
    bad="#A74435",
    text="#3B2418",
    muted="#6D5F52",
)

CSS = """
<style>
.stApp{background:%(bg)s;color:%(text)s;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:%(bg)s}
.block-container{padding-top:1.6rem;padding-bottom:4rem;max-width:1220px}
h1,h2,h3,h4,h5{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important;letter-spacing:-.01em;color:%(text)s}
p,li,label,[data-testid="stMarkdownContainer"]{color:%(text)s}
[data-testid="stHeader"]{background:transparent}

/* Deep espresso navigation contrasts with the warm parchment content area. */
[data-testid="stSidebar"]{background:%(side)s;border-right:1px solid %(border)s}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] p{color:%(bg)s}
[data-testid="stSidebar"] .bs-brand{color:%(bg)s}
[data-testid="stSidebar"] .bs-brand i{color:%(accent2)s}
[data-testid="stSidebar"] .bs-tag,[data-testid="stSidebar"] .bs-muted{color:#E4D2B4}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]{border-radius:10px;color:%(bg)s}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover{background:rgba(255,248,235,.10)}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"]{background:#5A3828;border:1px solid #8B6344}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]{
  background:%(accent2)s!important;border:1px solid %(accent2)s!important;color:%(text)s!important
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p{color:%(text)s!important}

.bs-id{display:flex;gap:1.2rem;flex-wrap:wrap;align-items:center;justify-content:space-between;background:%(card)s;border:1px solid %(border)s;border-left:4px solid %(accent)s;border-radius:12px;padding:.55rem 1rem;margin-bottom:1rem;font-size:.82rem;color:%(muted)s}
.bs-id b{color:%(text)s}
.bs-brand{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-weight:800;font-size:1.35rem;letter-spacing:.02em;color:%(text)s}
.bs-brand i{font-style:normal;color:%(accent)s}
.bs-tag{font-size:.68rem;letter-spacing:.16em;color:%(muted)s;text-transform:uppercase}
.bs-title{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.9rem;font-weight:800;letter-spacing:-.02em;color:%(text)s;line-height:1.15}
.bs-sub{color:%(muted)s;margin:.25rem 0 1.2rem}
.bs-card{background:%(card)s;border:1px solid %(border)s;border-radius:14px;padding:1rem 1.2rem;margin-bottom:.8rem;min-width:0;box-shadow:0 3px 12px rgba(59,36,24,.045)}
.bs-card h4{margin:0 0 .35rem;font-size:1rem;color:%(text)s}
.bs-card p,.bs-muted{color:%(muted)s;font-size:.9rem;margin:.15rem 0}
.bs-finding-head,.bs-live-finding-head{display:flex;align-items:flex-start;justify-content:space-between;gap:.45rem;flex-wrap:wrap;min-width:0}
.bs-finding-head h4{flex:1 1 11rem;min-width:0;overflow-wrap:anywhere}
.bs-badges{display:flex;flex:0 1 auto;flex-wrap:wrap;gap:.15rem;min-width:0}
.bs-kpi .l{color:%(muted)s;font-size:.74rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.bs-kpi .v{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.9rem;font-weight:800;font-variant-numeric:tabular-nums;color:%(text)s;line-height:1.15}
.bs-kpi .h{color:%(muted)s;font-size:.78rem}
.bs-badge{display:inline-block;padding:.25rem .6rem;border-radius:999px;font-size:.74rem;font-weight:600;margin:.1rem .15rem .1rem 0;border:1px solid transparent;white-space:normal;overflow-wrap:anywhere;line-height:1.35}
.t-success{color:#4E6338;background:#E6EBD9;border-color:#B8C69E}
.t-warn{color:#81500F;background:#F5E7C8;border-color:#E4C98C}
.t-danger{color:#87372D;background:#F2DFD7;border-color:#DDB1A3}
.t-info{color:#8B4A2F;background:#F4E0D3;border-color:#E1B7A0}
.t-neutral{color:%(muted)s;background:%(card2)s;border-color:%(border)s}
.bs-bar{height:8px;background:%(card2)s;border-radius:99px;overflow:hidden;margin:.3rem 0}
.bs-bar>div{height:100%%;border-radius:99px;background:linear-gradient(90deg,%(accent)s,%(accent2)s)}
.bs-bar.bad>div{background:linear-gradient(90deg,%(bad)s,%(warn)s)}
.bs-hero{background:radial-gradient(700px 300px at 0%% 0%%,rgba(184,92,56,.14),transparent 60%%),radial-gradient(600px 300px at 100%% 0%%,rgba(217,164,65,.16),transparent 60%%),%(card)s;border:1px solid %(border)s;border-radius:18px;padding:1.4rem 1.6rem;margin-bottom:1rem}
.bs-note{border-left:4px solid %(accent)s;background:%(card2)s;border-radius:10px;padding:.7rem 1rem;margin:.3rem 0 1rem;font-size:.9rem}
.bs-q{background:%(card)s;border:1px solid %(accent)s;border-radius:16px;padding:1.1rem 1.3rem;margin-bottom:.8rem;box-shadow:0 4px 16px rgba(59,36,24,.06)}
.bs-q .n{color:%(accent)s;font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700}
.bs-q .t{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.25rem;font-weight:700;margin:.3rem 0}
.bs-table{width:100%%;border-collapse:collapse;font-size:.86rem}
.bs-table th{text-align:left;color:%(muted)s;font-weight:600;font-size:.74rem;padding:.5rem .6rem;border-bottom:1px solid %(border)s}
.bs-table td{padding:.55rem .6rem;border-bottom:1px solid %(border)s;vertical-align:top}

/* Warm, readable form controls across text, numeric, selection, and tab widgets. */
[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] p{color:%(text)s}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] input,[data-testid="stTimeInput"] input{
  background:%(card)s!important;color:%(text)s!important;border:1px solid %(border)s!important;border-radius:9px!important
}
[data-baseweb="select"]>div,[data-testid="stMultiSelect"] [data-baseweb="select"]>div{
  background:%(card)s!important;color:%(text)s!important;border-color:%(border)s!important;border-radius:9px!important
}
[data-testid="stSelectbox"] [data-baseweb="select"] *,[data-testid="stMultiSelect"] [data-baseweb="select"] *{color:%(text)s!important}
[data-testid="stTabs"] [role="tablist"]{border-bottom:1px solid %(border)s}
[data-testid="stTabs"] [role="tab"]{color:%(muted)s}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:%(accent)s;border-bottom-color:%(accent)s}
[data-testid="stExpander"]{background:%(card)s;border:1px solid %(border)s;border-radius:12px}
[data-testid="stDataEditor"],[data-testid="stDataFrame"]{border:1px solid %(border)s;border-radius:10px;overflow:hidden}
[data-testid="stAlert"]{border-radius:10px}

[data-testid="stBaseButton-primary"]{background:linear-gradient(100deg,%(accent)s,#843C27)!important;border:0!important;color:#FFF5E7!important;font-weight:700}
[data-testid="stBaseButton-primary"]:hover{background:linear-gradient(100deg,#98472D,#843C27)!important}
[data-testid="stBaseButton-secondary"]{background:%(card)s!important;border:1px solid %(border)s!important;color:%(text)s!important}
[data-testid="stBaseButton-secondary"]:hover{border-color:%(accent)s!important;color:%(accent)s!important}
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
