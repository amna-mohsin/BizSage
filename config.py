"""Project-wide settings, expert-system thresholds, and decision-support assumptions.

Keep visible assumptions centralized here so the UI and reasoning code use one
consistent value and users can inspect what drives estimates.
"""

IDENTITY = {
    "project": "BizSage",
    "subtitle": "SME Financial & Operational Diagnostic Expert System",
}

WEEKDAYS_PER_MONTH = 22      # assumed working weekdays per month
WEEKEND_DAYS_PER_MONTH = 8   # assumed weekend days per month
MAX_QUESTIONS = 20           # safe termination: stop asking after this many questions
APPROX_CERTAINTY = 0.8       # certainty multiplier when the owner answers with a word instead of a number
REDUNDANT_WEIGHT = 0.3       # weight of the 2nd, 3rd... evidence in the same evidence group (avoids double counting)

# Support bands for the evidence-based confidence score (net certainty factor, -1 .. +1)
BANDS = [
    (0.95, "Definitely", "success"),
    (0.70, "Quite possible", "success"),
    (0.40, "Possible (maybe)", "info"),
    (0.15, "Weak signal (not sure)", "warn"),
    (-0.15, "Not enough evidence", "neutral"),
    (-0.50, "Weakened (unlikely)", "warn"),
    (-9.99, "Ruled out", "danger"),
]
PRIMARY_MIN = 0.40           # below this the system answers "insufficient evidence"

# Illustrative assumptions used by the Decision Support estimates (all shown to the user and editable in the UI)
ASSUMPTIONS = {
    "target_customers_per_staff": 15,   # customers one staff member can comfortably serve per day
    "lost_sales_pct_overloaded": 5,     # % of weekend sales lost when staff are overloaded
    "workforce_cut_pct": 15,            # % of labour cost saved by a workforce reduction
    "revenue_loss_after_cut_pct": 2,    # % of revenue lost after a workforce reduction
    "target_wastage_pct": 8,            # wastage level the owner aims for
    "wastage_capture_pct": 70,          # % of avoidable waste that is actually saved
    "supplier_saving_pct": 4,           # % of food cost saved by renegotiation
    "menu_margin_gain_pct": 3,          # % of revenue gained as margin from menu re-engineering
    "discount_cut_pct": 40,             # % of discounts removed by a discount reform
    "discount_volume_loss_pct": 25,     # % of the recovered discount value lost as lower volume
    "receivable_recovery_pct": 60,      # % of overdue receivables collected
    "supplier_extra_days": 15,          # extra supplier credit days negotiated
    "installment_relief_pct": 30,       # % reduction of the monthly instalment after rescheduling
    "utility_saving_pct": 15,           # % of utilities saved by trimming usage
    "branch_transfer_pct": 30,          # % of a closed branch's customers who move to another branch
    "branch_close_cost_pct": 10,        # % of the closed branch's expenses that cannot be avoided
    "branch_delivery_cost_cut_pct": 25, # % of a branch's expenses saved when it becomes delivery-only
    "branch_delivery_revenue_loss_pct": 35,  # % of a branch's revenue lost when dine-in stops
}
