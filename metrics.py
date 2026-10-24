"""
metrics.py
----------
All metric calculations for the "Performance ROI & Conversion Drop-off Analyzer".
Only Pandas and NumPy are used, so these functions are easy to test without Streamlit.

Golden rule used everywhere: first ADD UP the raw counts (spend, clicks, purchases...),
THEN divide. Averaging ratios (e.g. the mean of campaign ROIs) would give wrong totals.

Zero or missing denominators return NaN (shown as "N/A" in the dashboard)
instead of crashing or producing infinity.
"""

import numpy as np
import pandas as pd

# (display label, column name) in funnel order
FUNNEL_STAGES = [
    ("Landing Page Visitors", "landing_page_visitors"),
    ("Product Interactions", "product_interactions"),
    ("Add to Cart", "add_to_cart"),
    ("Checkout Started", "checkout_started"),
    ("Purchases", "purchases"),
]

CAMPAIGN_SUM_COLUMNS = [
    "marketing_spend", "attributed_revenue", "impressions", "clicks",
    "landing_page_visitors", "product_interactions", "add_to_cart",
    "checkout_started", "purchases",
]
PAYMENT_SUM_COLUMNS = [
    "checkout_attempts", "successful_payments", "failed_payments", "completed_orders",
]


# ---------------------------------------------------------------------------
# Safe division
# ---------------------------------------------------------------------------

def safe_divide(numerator, denominator, multiplier=1.0):
    """Divide two single numbers. Returns NaN if either is missing or the denominator is 0."""
    if numerator is None or denominator is None:
        return np.nan
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return float(numerator) / float(denominator) * multiplier


def ratio_series(numerator, denominator, multiplier=1.0):
    """Same idea for whole columns: zero denominators become NaN, never inf."""
    safe_den = denominator.astype("float64").replace(0, np.nan)
    return numerator.astype("float64") / safe_den * multiplier


# ---------------------------------------------------------------------------
# Campaign metrics
# ---------------------------------------------------------------------------

def add_campaign_ratios(summary):
    """Add ROI, CPA, CTR and conversion-rate columns to a table of summed counts."""
    out = summary.copy()
    out["roi_pct"] = ratio_series(out["attributed_revenue"] - out["marketing_spend"],
                                  out["marketing_spend"], 100)
    out["cpa"] = ratio_series(out["marketing_spend"], out["purchases"])
    out["ctr_pct"] = ratio_series(out["clicks"], out["impressions"], 100)
    out["conversion_rate_pct"] = ratio_series(out["purchases"], out["landing_page_visitors"], 100)
    return out


def summarize_campaigns(df, group_col=None):
    """
    Sum campaign counts and calculate ratios.
    group_col=None  -> a single-row table of overall totals
    group_col="marketing_channel" (or any column / list of columns) -> one row per group
    """
    if group_col is None:
        totals = df[CAMPAIGN_SUM_COLUMNS].sum().to_frame().T
    else:
        totals = df.groupby(group_col, as_index=False)[CAMPAIGN_SUM_COLUMNS].sum()
    return add_campaign_ratios(totals)


def campaign_kpis(df):
    """Overall KPIs as a plain dictionary."""
    row = summarize_campaigns(df).iloc[0]
    return {
        "marketing_spend": row["marketing_spend"],
        "attributed_revenue": row["attributed_revenue"],
        "roi_pct": row["roi_pct"],
        "purchases": row["purchases"],
        "cpa": row["cpa"],
        "conversion_rate_pct": row["conversion_rate_pct"],
        "ctr_pct": row["ctr_pct"],
    }


# ---------------------------------------------------------------------------
# Funnel
# ---------------------------------------------------------------------------

def funnel_table(df):
    """
    One row per funnel stage with:
      count, pct_of_first_stage, step_conversion_pct (vs previous stage),
      step_dropoff_pct (100 - step conversion), lost_from_previous (people lost).
    """
    counts = [df[col].sum() for _, col in FUNNEL_STAGES]
    rows = []
    for i, ((label, _), count) in enumerate(zip(FUNNEL_STAGES, counts)):
        if i == 0:
            step_conv = np.nan
            dropoff = np.nan
            lost = np.nan
        else:
            step_conv = safe_divide(count, counts[i - 1], 100)
            dropoff = 100 - step_conv if not np.isnan(step_conv) else np.nan
            lost = counts[i - 1] - count
        rows.append({
            "stage": label,
            "count": count,
            "pct_of_first_stage": safe_divide(count, counts[0], 100),
            "step_conversion_pct": step_conv,
            "step_dropoff_pct": dropoff,
            "lost_from_previous": lost,
            "step": f"{FUNNEL_STAGES[i - 1][0]} -> {label}" if i > 0 else "",
        })
    return pd.DataFrame(rows)


def largest_dropoff(funnel):
    """Return the funnel row with the biggest percentage drop-off, or None if undefined."""
    steps = funnel.dropna(subset=["step_dropoff_pct"])
    if steps.empty:
        return None
    return steps.loc[steps["step_dropoff_pct"].idxmax()]


def dropoff_by_group(df, group_col):
    """
    Table of step drop-off percentages: one row per group (e.g. market),
    one column per funnel step.
    """
    rows = {}
    for group_value, part in df.groupby(group_col):
        f = funnel_table(part)
        rows[group_value] = dict(zip(f["step"][1:], f["step_dropoff_pct"][1:]))
    return pd.DataFrame.from_dict(rows, orient="index")


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

def summarize_payments(df, group_col=None):
    """Sum payment counts and calculate completion and failure rates."""
    if group_col is None:
        totals = df[PAYMENT_SUM_COLUMNS].sum().to_frame().T
    else:
        totals = df.groupby(group_col, as_index=False)[PAYMENT_SUM_COLUMNS].sum()
    totals["checkout_completion_rate_pct"] = ratio_series(
        totals["successful_payments"], totals["checkout_attempts"], 100)
    totals["payment_failure_rate_pct"] = ratio_series(
        totals["failed_payments"], totals["checkout_attempts"], 100)
    return totals


# ---------------------------------------------------------------------------
# Display helpers (NaN -> "N/A")
# ---------------------------------------------------------------------------

def fmt_money(value, decimals=0):
    return "N/A" if pd.isna(value) else f"${value:,.{decimals}f}"


def fmt_pct(value, decimals=1):
    return "N/A" if pd.isna(value) else f"{value:,.{decimals}f}%"


def fmt_int(value):
    return "N/A" if pd.isna(value) else f"{int(round(value)):,}"
