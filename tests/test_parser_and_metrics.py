"""Regression tests for tolerant input parsing and safe financial-metric derivation."""
from calculations import metrics
from expert_system.input_parser import parse_boolean_text, parse_number, parse_numeric_answer


def test_numbers_in_many_formats():
    assert parse_number("450000") == (450000.0, "ok")
    assert parse_number("Rs. 4.5 lac")[0] == 450000.0
    assert parse_number("450k")[0] == 450000.0
    assert parse_number("18%")[0] == 18.0
    assert parse_number("1,250")[0] == 1250.0
    assert parse_number("pata nahi")[1] == "unknown" and parse_number("abc")[1] == "invalid"


def test_words_and_urdu_english_words_are_accepted():
    q = {"low": 4, "medium": 9, "high": 16, "very high": 25}
    assert parse_numeric_answer("high", q) == (16.0, 0.8, "approximate")
    assert parse_numeric_answer("zyada", q)[0] == 16.0
    assert parse_numeric_answer("bohat zyada", q)[0] == 25.0
    assert parse_numeric_answer("15", q) == (15.0, 1.0, "ok")


def test_boolean_text():
    assert parse_boolean_text("yes") == (True, 1.0) and parse_boolean_text("nahi") == (False, 1.0)
    assert parse_boolean_text("maybe") == (True, 0.7) and parse_boolean_text("hmm")[0] is None


def test_metrics_basic_and_safe():
    hist = [dict(revenue=100, expenses=90, customers=10, food_cost=30), dict(revenue=90, expenses=95, customers=9, food_cost=30)]
    d = metrics.derive({"labour_cost": 27}, hist)
    assert round(d["revenue_change_pct"], 1) == -10.0 and round(d["labour_cost_ratio"], 1) == 30.0 and d["loss_months_count"] == 1
    assert "current_ratio" not in d and metrics.derive({}, []) == {}
    assert metrics.div(5, 0) is None and metrics.pct_change(5, None) is None
