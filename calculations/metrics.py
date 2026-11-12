"""Financial Calculation Engine: turns the numbers the owner entered into the facts the rules reason about.
Every metric returns None (unknown) when its inputs are missing or a denominator is zero. Missing is never treated as zero."""
import statistics
from typing import Dict, List, Optional

from config import WEEKDAYS_PER_MONTH, WEEKEND_DAYS_PER_MONTH


def _num(x):
    """Accept real numeric inputs only; bool is excluded because it subclasses int in Python."""
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def div(a, b) -> Optional[float]:
    """Return a ratio only when both values are known and the denominator is non-zero."""
    a, b = _num(a), _num(b)
    if a is None or b is None or b == 0:
        return None
    return a / b


def pct_change(new, old) -> Optional[float]:
    """Calculate percentage change safely; an absent or zero baseline has no defined change."""
    new, old = _num(new), _num(old)
    if new is None or old is None or old == 0:
        return None
    return (new - old) / abs(old) * 100


def _col(history: List[dict], key: str) -> List[Optional[float]]:
    """Read one monthly measure while preserving unknown cells as None."""
    return [_num(row.get(key)) for row in history]


def derive(raw: dict, history: List[dict], profile: Optional[dict] = None) -> Dict[str, object]:
    """raw = single-value inputs; history = monthly rows oldest -> newest with revenue, expenses, customers, food_cost."""
    profile = profile or {}
    g = lambda k: _num(raw.get(k))
    d: Dict[str, object] = {}
    rev, exp, cust, food = (_col(history, k) for k in ("revenue", "expenses", "customers", "food_cost"))
    n = len(history)
    r_now = rev[-1] if n else None
    r_prev = rev[-2] if n > 1 else None
    e_now = exp[-1] if n else None
    c_now = cust[-1] if n else None
    c_prev = cust[-2] if n > 1 else None
    f_now = food[-1] if n else None
    f_prev = food[-2] if n > 1 else None
    r_3 = rev[-4] if n > 3 else None
    e_3 = exp[-4] if n > 3 else None
    f_3 = food[-4] if n > 3 else None
    c_3 = cust[-4] if n > 3 else None

    # ---- revenue & demand ----
    streak = 0
    for i in range(n - 1, 0, -1):
        if rev[i] is not None and rev[i - 1] is not None and rev[i] < rev[i - 1]:
            streak += 1
        else:
            break
    d["revenue_decline_streak"] = streak if n >= 2 and r_now is not None else None
    d["revenue_change_pct"] = pct_change(r_now, r_prev)
    vals = [v for v in rev if v is not None]
    # Require four known months before reporting variation; fewer points can overstate volatility.
    d["revenue_cv_pct"] = (statistics.pstdev(vals) / statistics.mean(vals) * 100) if len(vals) >= 4 and statistics.mean(vals) > 0 else None
    d["customers_change_pct"] = pct_change(c_now, c_prev)
    t_now, t_prev = div(r_now, c_now), div(r_prev, c_prev)
    d["avg_ticket_change_pct"] = pct_change(t_now, t_prev)
    d["weekend_weekday_ratio"] = div(g("weekend_customers_per_day"), g("weekday_customers_per_day"))

    # ---- expenses & profitability ----
    d["food_cost_ratio"] = (div(f_now, r_now) or 0) * 100 if div(f_now, r_now) is not None else None
    d["labour_cost_ratio"] = div(g("labour_cost"), r_now) * 100 if div(g("labour_cost"), r_now) is not None else None
    d["rent_ratio"] = div(g("rent"), r_now) * 100 if div(g("rent"), r_now) is not None else None
    d["utilities_change_pct"] = pct_change(g("utilities"), g("utilities_prev"))
    d["food_cost_per_customer_change_pct"] = pct_change(div(f_now, c_now), div(f_prev, c_prev))
    gm_now = div(r_now - f_now, r_now) * 100 if (r_now is not None and f_now is not None and r_now) else None
    gm_3 = div(r_3 - f_3, r_3) * 100 if (r_3 is not None and f_3 is not None and r_3) else None
    d["gross_margin_pct"] = gm_now
    d["gross_margin_change_pts"] = gm_now - gm_3 if gm_now is not None and gm_3 is not None else None
    eg, rg = pct_change(e_now, e_3), pct_change(r_now, r_3)
    d["expense_growth_gap_pts"] = eg - rg if eg is not None and rg is not None else None
    profit = r_now - e_now if r_now is not None and e_now is not None else None
    d["net_profit"] = profit
    d["net_margin_pct"] = div(profit, r_now) * 100 if div(profit, r_now) is not None else None
    loss = 0
    for i in range(n - 1, -1, -1):
        if rev[i] is not None and exp[i] is not None and exp[i] > rev[i]:
            loss += 1
        else:
            break
    d["loss_months_count"] = loss if r_now is not None and e_now is not None else None
    # Break-even revenue solves revenue minus variable food cost minus other expenses = zero.
    be = None
    if None not in (r_now, e_now, f_now) and r_now > 0 and (1 - f_now / r_now) > 0.05:
        be = (e_now - f_now) / (1 - f_now / r_now)
    d["breakeven_gap_pct"] = (r_now - be) / be * 100 if be else None

    # ---- cash flow & liquidity ----
    # Cash-conversion metrics remain unavailable unless every component is supplied.
    cash = g("cash_on_hand")
    d["cash_buffer_months"] = div(cash, e_now)
    cur_assets = cash + g("receivables_total") + g("inventory_value") if None not in (cash, g("receivables_total"), g("inventory_value")) else None
    cur_liab = g("payables_total") + g("short_term_debt") if None not in (g("payables_total"), g("short_term_debt")) else None
    d["current_ratio"] = div(cur_assets, cur_liab)
    d["cash_change_pct"] = pct_change(cash, g("cash_last_month"))
    d["receivables_overdue_ratio"] = div(g("receivables_overdue"), r_now) * 100 if div(g("receivables_overdue"), r_now) is not None else None
    d["payables_overdue_ratio"] = div(g("payables_overdue"), f_now) * 100 if div(g("payables_overdue"), f_now) is not None else None
    inst = g("monthly_installment")
    d["debt_service_burden_pct"] = div(inst, r_now) * 100 if div(inst, r_now) is not None else None
    interest = g("interest_expense")
    d["dscr"] = div(profit + interest, inst) if profit is not None and interest is not None and inst else None
    inv_days = div(g("inventory_value"), f_now / 30 if f_now else None)
    d["inventory_days"] = inv_days
    rec_days = div(g("receivables_total"), r_now / 30 if r_now else None)
    pay_days = div(g("payables_total"), f_now / 30 if f_now else None)
    d["cash_conversion_days"] = inv_days + rec_days - pay_days if None not in (inv_days, rec_days, pay_days) else None
    cc = d["cash_change_pct"]
    d["profit_but_cash_falling"] = (profit > 0 and cc <= -10) if profit is not None and cc is not None else None

    # ---- inventory ----
    d["food_cost_variance_pct"] = pct_change(f_now, g("expected_food_cost"))

    # ---- staffing ----
    wd_c, we_c, wd_s, we_s = g("weekday_customers_per_day"), g("weekend_customers_per_day"), g("weekday_staff"), g("weekend_staff")
    d["weekday_customers_per_staff"] = div(wd_c, wd_s)
    d["weekend_customers_per_staff"] = div(we_c, we_s)
    d["labour_hours_per_customer"] = div(g("labour_hours_month"), c_now)
    sr, dr = div(wd_s, we_s), div(wd_c, we_c)
    d["schedule_alignment_index"] = div(sr, dr)
    d["sales_per_labour_hour_change_pct"] = pct_change(div(r_now, g("labour_hours_month")), div(r_prev, g("labour_hours_prev")))
    dn, dp = g("delivery_orders_now"), g("delivery_orders_prev")
    ch = pct_change(dn, dp)
    d["delivery_declining"] = (ch <= -10) if ch is not None else None

    # ---- debt & stability ----
    debt, eq = g("total_debt"), g("equity")
    d["debt_to_equity"] = div(debt, eq) if eq and eq > 0 else None
    d["interest_change_pct"] = pct_change(interest, g("interest_expense_prev"))
    d["short_term_debt_share_pct"] = div(g("short_term_debt"), debt) * 100 if div(g("short_term_debt"), debt) is not None else None
    rc = d["revenue_change_pct"]
    d["debt_up_revenue_down"] = (debt > g("total_debt_prev") and rc < 0) if None not in (debt, g("total_debt_prev"), rc) else None
    d["equity_buffer_months"] = div(eq, e_now)

    # ---- data-quality facts used by consistency checks ----
    rp = g("reported_net_profit")
    if rp is not None and profit is not None and r_now:
        d["profit_report_mismatch"] = (rp * profit < 0) or abs(rp - profit) > 0.10 * r_now
    else:
        d["profit_report_mismatch"] = None
    if None not in (wd_c, we_c, c_now) and c_now > 0:
        est = wd_c * WEEKDAYS_PER_MONTH + we_c * WEEKEND_DAYS_PER_MONTH
        d["monthly_customers_mismatch"] = abs(est - c_now) / c_now > 0.35
    else:
        d["monthly_customers_mismatch"] = None
    tot = _num(profile.get("employees_total"))
    d["staff_exceeds_employees"] = (max(wd_s or 0, we_s or 0) > tot) if tot and (wd_s is not None or we_s is not None) else None
    return {k: v for k, v in d.items() if v is not None}
