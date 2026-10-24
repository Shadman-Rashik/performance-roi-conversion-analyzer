"""
test_project.py
---------------
Simple automated checks. No extra libraries needed.

Run:  python test_project.py
"""

import math
import sqlite3

import numpy as np
import pandas as pd

import metrics as m
import recommendations as rec
import validate_data as vd


def approx(a, b, tol=1e-6):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def test_safe_division():
    assert math.isnan(m.safe_divide(10, 0))
    assert math.isnan(m.safe_divide(None, 5))
    assert math.isnan(m.safe_divide(5, np.nan))
    assert approx(m.safe_divide(1, 4, 100), 25.0)
    s = m.ratio_series(pd.Series([1, 2]), pd.Series([0, 4]))
    assert math.isnan(s.iloc[0]) and approx(s.iloc[1], 0.5)


def test_metric_formulas():
    df = pd.DataFrame([{
        "marketing_spend": 100.0, "attributed_revenue": 250.0, "impressions": 10000,
        "clicks": 200, "landing_page_visitors": 150, "product_interactions": 100,
        "add_to_cart": 40, "checkout_started": 20, "purchases": 10,
    }])
    k = m.campaign_kpis(df)
    assert approx(k["roi_pct"], 150.0)            # (250-100)/100*100
    assert approx(k["cpa"], 10.0)                 # 100/10
    assert approx(k["ctr_pct"], 2.0)              # 200/10000*100
    assert approx(k["conversion_rate_pct"], 10 / 150 * 100)
    f = m.funnel_table(df)
    assert approx(f.loc[1, "step_dropoff_pct"], 100 - 100 / 150 * 100)
    big = m.largest_dropoff(f)
    assert big["stage"] == "Add to Cart"          # 100 -> 40 is the largest % drop


def test_zero_purchases_and_zero_spend():
    df = pd.DataFrame([{
        "marketing_spend": 50.0, "attributed_revenue": 0.0, "impressions": 100,
        "clicks": 10, "landing_page_visitors": 5, "product_interactions": 2,
        "add_to_cart": 1, "checkout_started": 1, "purchases": 0,
    }])
    k = m.campaign_kpis(df)
    assert math.isnan(k["cpa"])                   # no purchases -> CPA undefined
    assert approx(k["roi_pct"], -100.0)
    df["marketing_spend"] = 0.0
    assert math.isnan(m.campaign_kpis(df)["roi_pct"])   # no spend -> ROI undefined


def test_payment_rates():
    df = pd.DataFrame([
        {"market": "A", "payment_method": "X", "checkout_attempts": 100,
         "successful_payments": 90, "failed_payments": 10, "completed_orders": 88},
        {"market": "B", "payment_method": "X", "checkout_attempts": 0,
         "successful_payments": 0, "failed_payments": 0, "completed_orders": 0},
    ])
    by_market = m.summarize_payments(df, "market").set_index("market")
    assert approx(by_market.loc["A", "payment_failure_rate_pct"], 10.0)
    assert approx(by_market.loc["A", "checkout_completion_rate_pct"], 90.0)
    assert math.isnan(by_market.loc["B", "payment_failure_rate_pct"])


def test_database_matches_pandas():
    campaigns, payments = vd.load_tables()
    assert vd.validate_campaigns(campaigns) == []
    assert vd.validate_payments(payments) == []

    conn = sqlite3.connect(vd.DB_PATH)
    sql_row = conn.execute(
        "SELECT SUM(marketing_spend), SUM(attributed_revenue), SUM(purchases), "
        "(SUM(attributed_revenue)-SUM(marketing_spend))*100.0/SUM(marketing_spend) FROM campaigns"
    ).fetchone()
    sql_fail = conn.execute(
        "SELECT SUM(failed_payments)*100.0/SUM(checkout_attempts) FROM payments").fetchone()[0]
    conn.close()

    k = m.campaign_kpis(campaigns)
    assert approx(k["marketing_spend"], sql_row[0])
    assert approx(k["attributed_revenue"], sql_row[1])
    assert approx(k["purchases"], sql_row[2])
    assert approx(k["roi_pct"], sql_row[3])
    assert approx(m.summarize_payments(payments).iloc[0]["payment_failure_rate_pct"], sql_fail)


def test_validation_catches_bad_data():
    campaigns, payments = vd.load_tables()
    bad = campaigns.copy()
    bad.loc[0, "purchases"] = bad.loc[0, "checkout_started"] + 5
    assert any("purchases" in p for p in vd.validate_campaigns(bad))
    bad_pay = payments.copy()
    bad_pay.loc[0, "failed_payments"] += 1
    assert any("successful + failed" in p for p in vd.validate_payments(bad_pay))


def test_filters_change_results_and_recommendations():
    campaigns, payments = vd.load_tables()
    all_k = m.campaign_kpis(campaigns)
    one_market = campaigns[campaigns["market"] == "Bangladesh"]
    assert m.campaign_kpis(one_market)["marketing_spend"] < all_k["marketing_spend"]

    # Recommendation text must come from the selected data, not fixed names.
    subset = campaigns[campaigns["marketing_channel"].isin(["Email", "Google Search"])]
    items = rec.campaign_recommendations(subset)
    text = " ".join(i["observation"] for i in items)
    assert items
    for other in set(campaigns["marketing_channel"]) - {"Email", "Google Search"}:
        assert other not in text, f"{other} should not appear for this selection"
    pay_items = rec.payment_recommendations(payments[payments["market"] == "Bangladesh"])
    pay_text = " ".join(i["observation"] for i in pay_items)
    for other_market in set(payments["market"]) - {"Bangladesh"}:
        assert other_market not in pay_text
    # Empty selections must not crash.
    assert rec.build_recommendations(campaigns.iloc[0:0], payments.iloc[0:0])


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\nAll {len(tests)} tests passed.")


if __name__ == "__main__":
    main()
