"""Reusable Plotly charts for trends, decision-option scores, and branch comparisons."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.theme import P


def style(fig, h=320):
    """Apply the shared theme and disable interactions that are awkward on small screens."""
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=42, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=P["text"], family="system-ui, sans-serif"), title=dict(font=dict(size=15)), dragmode=False,
                      legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.2), legend_itemclick=False, legend_itemdoubleclick=False)
    fig.update_xaxes(gridcolor=P["border"], zerolinecolor=P["border"], fixedrange=True)
    fig.update_yaxes(gridcolor=P["border"], zerolinecolor=P["border"], fixedrange=True)
    return fig


def show(fig):
    """Render a chart without the Plotly toolbar, using Streamlit's responsive width."""
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})


def revenue_expenses(labels, hist):
    """Compare monthly sales and expenses so owners can see profitability trends."""
    df = pd.DataFrame({"Month": labels, "Revenue": [r.get("revenue") for r in hist], "Expenses": [r.get("expenses") for r in hist]})
    fig = go.Figure()
    fig.add_scatter(x=df["Month"], y=df["Revenue"], name="Revenue", mode="lines+markers", line=dict(color=P["accent"], width=3))
    fig.add_scatter(x=df["Month"], y=df["Expenses"], name="Expenses", mode="lines+markers", line=dict(color=P["bad"], width=3))
    fig.update_layout(title="Revenue vs expenses (Rs)")
    return style(fig)


def dss_scores(options):
    """Display the overall weighted suitability ranking for each action."""
    df = pd.DataFrame([{"Option": o["name"], "Score": o["weighted"]} for o in options]).sort_values("Score")
    fig = px.bar(df, x="Score", y="Option", orientation="h", title="Weighted suitability score (0-100)", color_discrete_sequence=[P["accent"]], text="Score")
    fig.update_xaxes(range=[0, 100])
    return style(fig, 60 + 50 * len(df))


def criteria_chart(options, labels):
    """Expose criterion-level trade-offs instead of hiding them in one aggregate score."""
    fig = go.Figure()
    for o in options:
        fig.add_bar(name=o["name"][:34], x=[labels[c] for c in o["scores"]], y=list(o["scores"].values()))
    fig.update_layout(title="How each option scores on each criterion (0-10)", barmode="group")
    return style(fig, 340)


def branch_lines(branches):
    """Normalize branch revenues to their own first month for trend-only comparison."""
    fig = go.Figure()
    for b in branches:
        base = next((x for x in b["revenue"] if x), None)
        if base:
            fig.add_scatter(x=list(range(1, len(b["revenue"]) + 1)), y=[(x / base * 100) if x else None for x in b["revenue"]], name=b["name"], mode="lines+markers")
    fig.update_layout(title="Revenue trend of each branch (first month = 100)")
    fig.update_xaxes(title="Month")
    return style(fig, 340)


def corr_heatmap(corr):
    """Visualize whether branch revenues move together across the observed months."""
    names = list(corr)
    z = [[corr[a][b] if corr[a][b] is not None else 0 for b in names] for a in names]
    fig = px.imshow(z, x=names, y=names, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale=[P["bad"], P["card2"], P["accent"]],
                    title="Do branches move together? (1 = identical pattern)")
    fig.update_coloraxes(showscale=False)
    return style(fig, 320)
