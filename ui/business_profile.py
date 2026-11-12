"""Collect restaurant context and six months of history used for trend-based facts."""
import pandas as pd
import streamlit as st

from ui.components import header, note
from ui.state import month_labels, rs

CITIES = ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Peshawar", "Quetta", "Hyderabad", "Hyderabad (Highway)", "Sialkot", "Other"]
TYPES = ["Family dine-in restaurant", "Fast food", "Cafe", "Highway restaurant", "Takeaway / delivery kitchen", "Other"]
COLS = {"revenue": "Revenue (Rs)", "expenses": "Expenses (Rs)", "customers": "Customers", "food_cost": "Food cost (Rs)"}


def _idx(options, value):
    """Keep select boxes valid when a saved profile contains an unfamiliar value."""
    return options.index(value) if value in options else 0


def render(show_header=True):
    """Render and save the profile/history editor without assuming blank cells are zero."""
    if show_header:
        header("Business profile", "Tell BizSage about the restaurant and its last six months. Leave a cell blank if you do not know it.")
    s = rs()
    p = s.profile
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Restaurant name", value=p.get("name", ""), max_chars=80, key="prof_name")
        city = c2.selectbox("City", CITIES, index=_idx(CITIES, p.get("city")), key="prof_city")
        c1, c2, c3, c4 = st.columns(4)
        rtype = c1.selectbox("Type", TYPES, index=_idx(TYPES, p.get("type")), key="prof_type")
        employees = c2.number_input("Total employees", 0, 1000, int(p.get("employees_total", 0)), key="prof_emp")
        seats = c3.number_input("Seats", 0, 2000, int(p.get("seats", 0)), key="prof_seats")
        years = c4.number_input("Years open", 0, 100, int(p.get("years_open", 0)), key="prof_years")
        st.markdown("##### Last six months (oldest at the top, current month at the bottom)")
        df = pd.DataFrame({"Month": month_labels(s)})
        for k, label in COLS.items():
            df[label] = [r.get(k) for r in s.history]
        edited = st.data_editor(df, num_rows="fixed", hide_index=True, key="hist_editor", width="stretch",
                                column_config={"Month": st.column_config.TextColumn("Month"),
                                               **{label: st.column_config.NumberColumn(label, min_value=0, format="%d") for label in COLS.values()}})
        saved = st.form_submit_button("Save restaurant details", type="primary")
    if saved:
        # Convert pandas' missing-cell marker back to None for three-valued reasoning.
        history = []
        for _, row in edited.iterrows():
            history.append({k: (None if pd.isna(row[label]) else float(row[label])) for k, label in COLS.items()})
        profile = {"name": name, "city": city, "type": rtype, "employees_total": int(employees), "seats": int(seats), "years_open": int(years),
                   "months": [str(m) for m in edited["Month"]]}
        s.set_inputs(history=history, profile=profile)
        s.analyze()
        st.success("Restaurant details saved and checked.")
        for i in s.state["issues"]:
            (st.warning if i.severity in ("error", "warning") else st.info)(i.message)
    note("Revenue, expenses, customers and food cost for every month give BizSage the trends it needs. At least four months of revenue are best; "
         "blank cells are treated as unknown, never as zero.", "Tip")
