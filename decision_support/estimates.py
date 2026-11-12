"""Illustrative impact estimates for decision options, based on entered data and visible assumptions.

These are comparison aids, not forecasts. An estimate is marked unavailable when its required
inputs are missing rather than silently filling gaps with invented values.
"""
import math
from typing import Dict

from config import ASSUMPTIONS, WEEKDAYS_PER_MONTH, WEEKEND_DAYS_PER_MONTH


def _need(ctx: dict, keys):
    """Find each needed value in raw inputs, latest monthly history, then derived facts."""
    raw, latest = ctx.get("raw", {}), ctx.get("latest", {})
    vals, missing = {}, []
    for k in keys:
        v = raw.get(k, latest.get(k, ctx.get("facts", {}).get(k)))
        if v is None:
            missing.append(k.replace("_", " "))
        vals[k] = v
    return vals, missing


def _na(missing):
    """Use one consistent result shape when required information is unavailable."""
    return {"available": False, "monthly_net": None, "one_time_cash": None, "notes": [], "missing": missing}


def _ok(net=None, one_time=None, notes=None):
    """Return an available estimate while distinguishing recurring and one-time effects."""
    return {"available": True, "monthly_net": None if net is None else round(net), "one_time_cash": None if one_time is None else round(one_time),
            "notes": notes or [], "missing": []}


def _cm_ratio(ctx):
    r, f = ctx.get("latest", {}).get("revenue"), ctx.get("latest", {}).get("food_cost")
    return (1 - f / r) if r and f is not None and r > 0 else 0.6


def estimate(option_id: str, ctx: dict, A: Dict[str, float] = None) -> dict:
    """Dispatch an option ID to its estimator, merging user edits over documented defaults."""
    A = {**ASSUMPTIONS, **(A or {})}
    f = _ESTIMATORS.get(option_id)
    return f(ctx, A) if f else _ok(0, None, ["Baseline: no change in cost or revenue."])


def _staffing_base(ctx, A):
    """Estimate weekday/weekend staffing needs from customer load and the editable service target."""
    v, miss = _need(ctx, ["weekday_customers_per_day", "weekend_customers_per_day", "weekday_staff", "weekend_staff", "avg_daily_wage"])
    if miss:
        return None, miss
    tgt = A["target_customers_per_staff"]
    v["req_wd"] = max(1, math.ceil(v["weekday_customers_per_day"] / tgt))
    v["req_we"] = max(1, math.ceil(v["weekend_customers_per_day"] / tgt))
    return v, []


def _implied_labour(v):
    """Translate daily wages and weekday/weekend staffing into monthly labour cost."""
    return v["avg_daily_wage"] * (v["weekday_staff"] * WEEKDAYS_PER_MONTH + v["weekend_staff"] * WEEKEND_DAYS_PER_MONTH)


def _wage_check(ctx, v):
    """Sanity check: wage x staff x days should be roughly the labour cost the owner reported."""
    reported = ctx.get("raw", {}).get("labour_cost")
    implied = _implied_labour(v)
    if reported and implied > 1.5 * reported:
        return reported, [f"Warning: your daily wage figure implies about Rs {implied:,.0f} of labour per month, but you reported Rs {reported:,.0f}. "
                          "Savings are capped at the reported labour cost. Please check the wage or staff numbers."]
    return None, []


def _st1(ctx, A):
    v, miss = _staffing_base(ctx, A)
    if miss:
        return _na(miss)
    save = max(0, v["weekday_staff"] - v["req_wd"]) * v["avg_daily_wage"] * WEEKDAYS_PER_MONTH
    cap, warn = _wage_check(ctx, v)
    if cap is not None:
        save = min(save, cap)
    extra = max(0, v["req_we"] - v["weekend_staff"]) * v["avg_daily_wage"] * WEEKEND_DAYS_PER_MONTH
    return _ok(save - extra, None, [f"Weekday staff {v['weekday_staff']:.0f} -> {min(v['weekday_staff'], v['req_wd']):.0f}; weekend staff {v['weekend_staff']:.0f} -> {max(v['weekend_staff'], v['req_we']):.0f}.",
                                     f"Saving Rs {save:,.0f}/month on weekdays, extra cost Rs {extra:,.0f}/month on weekends.",
                                     "Assumes surplus weekday workers are daily-wage staff who can be rostered flexibly."] + warn)


def _st2(ctx, A):
    v, miss = _staffing_base(ctx, A)
    if miss:
        return _na(miss)
    cost = max(0, v["req_we"] - v["weekend_staff"]) * v["avg_daily_wage"] * WEEKEND_DAYS_PER_MONTH
    rev = ctx.get("latest", {}).get("revenue") or 0
    wd, we = v["weekday_customers_per_day"] * WEEKDAYS_PER_MONTH, v["weekend_customers_per_day"] * WEEKEND_DAYS_PER_MONTH
    we_rev = rev * we / (wd + we) if (wd + we) else 0
    overloaded = v["weekend_customers_per_day"] / max(v["weekend_staff"], 1) > 25
    benefit = we_rev * A["lost_sales_pct_overloaded"] / 100 * _cm_ratio(ctx) if overloaded else 0
    return _ok(benefit - cost, None, [f"Extra weekend payroll Rs {cost:,.0f}/month.",
                                       f"Recovered sales margin Rs {benefit:,.0f}/month" + ("" if overloaded else " (weekend load is not high, so no recovery assumed)") + "."])


def _st3(ctx, A):
    v, miss = _need(ctx, ["labour_cost", "revenue"])
    if miss:
        return _na(miss)
    save = v["labour_cost"] * A["workforce_cut_pct"] / 100
    loss = v["revenue"] * A["revenue_loss_after_cut_pct"] / 100 * _cm_ratio(ctx)
    return _ok(save - loss, None, [f"Labour saving Rs {save:,.0f}/month ({A['workforce_cut_pct']:.0f}% cut).", f"Margin lost from weaker service Rs {loss:,.0f}/month."])


def _mg1(ctx, A):
    v, miss = _need(ctx, ["food_cost", "wastage_pct"])
    if miss:
        return _na(miss)
    save = v["food_cost"] * max(0, v["wastage_pct"] - A["target_wastage_pct"]) / 100 * A["wastage_capture_pct"] / 100
    return _ok(save, None, [f"Wastage {v['wastage_pct']:.0f}% -> target {A['target_wastage_pct']:.0f}%, capturing {A['wastage_capture_pct']:.0f}% of the avoidable waste."])


def _mg2(ctx, A):
    v, miss = _need(ctx, ["food_cost"])
    return _na(miss) if miss else _ok(v["food_cost"] * A["supplier_saving_pct"] / 100, None, [f"Assumes {A['supplier_saving_pct']:.0f}% saving on food purchases."])


def _mg3(ctx, A):
    v, miss = _need(ctx, ["revenue"])
    return _na(miss) if miss else _ok(v["revenue"] * A["menu_margin_gain_pct"] / 100, None, [f"Assumes menu changes add {A['menu_margin_gain_pct']:.0f}% of revenue as margin."])


def _mg4(ctx, A):
    v, miss = _need(ctx, ["revenue", "discount_pct"])
    if miss:
        return _na(miss)
    given = v["revenue"] * v["discount_pct"] / 100
    rec = given * A["discount_cut_pct"] / 100
    return _ok(rec * (1 - A["discount_volume_loss_pct"] / 100), None, [f"Discounts now about Rs {given:,.0f}/month; cutting {A['discount_cut_pct']:.0f}% recovers Rs {rec:,.0f}, minus {A['discount_volume_loss_pct']:.0f}% lost volume."])


def _cf1(ctx, A):
    v, miss = _need(ctx, ["receivables_overdue"])
    return _na(miss) if miss else _ok(None, v["receivables_overdue"] * A["receivable_recovery_pct"] / 100, [f"One-time cash if {A['receivable_recovery_pct']:.0f}% of overdue amounts are collected."])


def _cf2(ctx, A):
    v, miss = _need(ctx, ["food_cost"])
    return _na(miss) if miss else _ok(None, v["food_cost"] / 30 * A["supplier_extra_days"], [f"One-time cash timing benefit from {A['supplier_extra_days']:.0f} extra supplier credit days."])


def _cf3(ctx, A):
    v, miss = _need(ctx, ["monthly_installment"])
    return _na(miss) if miss else _ok(v["monthly_installment"] * A["installment_relief_pct"] / 100, None, [f"Monthly relief if instalments fall {A['installment_relief_pct']:.0f}%. Total interest paid will rise."])


def _cf4(ctx, A):
    v, miss = _need(ctx, ["utilities"])
    return _na(miss) if miss else _ok(v["utilities"] * A["utility_saving_pct"] / 100, None, [f"Assumes {A['utility_saving_pct']:.0f}% saving on utilities."])


def _branch(ctx, A):
    b = ctx.get("branch", {})
    return b


def _br1(ctx, A):
    b = ctx.get("branch")
    if not b:
        return _na(["branch data"])
    saved = b["expenses"] * (1 - A["branch_close_cost_pct"] / 100)
    lost = b["revenue"] * (1 - A["branch_transfer_pct"] / 100) * b["cm"]
    return _ok(saved - lost, None, [f"Saves about Rs {saved:,.0f}/month of expenses and loses Rs {lost:,.0f}/month of margin ({A['branch_transfer_pct']:.0f}% of customers assumed to move to another branch)."])


def _br2(ctx, A):
    b = ctx.get("branch")
    if not b:
        return _na(["branch data"])
    gap = max(0.0, b["expenses"] - b["revenue"])
    need = gap / b["cm"] if b["cm"] else 0
    return _ok(None, None, [f"To break even the branch needs about Rs {need:,.0f} more monthly revenue ({(need / b['revenue'] * 100 if b['revenue'] else 0):.0f}% growth)." if gap else "The branch already covers its costs.",
                            "Investment budget is for you to decide; it is not estimated."])


def _br3(ctx, A):
    b = ctx.get("branch")
    if not b:
        return _na(["branch data"])
    saved = b["expenses"] * A["branch_delivery_cost_cut_pct"] / 100
    lost = b["revenue"] * A["branch_delivery_revenue_loss_pct"] / 100 * b["cm"]
    return _ok(saved - lost, None, [f"Saves Rs {saved:,.0f}/month in running cost, loses Rs {lost:,.0f}/month of dine-in margin."])


_ESTIMATORS = {"ST1": _st1, "ST2": _st2, "ST3": _st3, "MG1": _mg1, "MG2": _mg2, "MG3": _mg3, "MG4": _mg4,
               "CF1": _cf1, "CF2": _cf2, "CF3": _cf3, "CF4": _cf4, "BR1": _br1, "BR2": _br2, "BR3": _br3}
