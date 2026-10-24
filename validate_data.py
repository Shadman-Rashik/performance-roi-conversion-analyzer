"""
validate_data.py
----------------
Data-quality checks for the two tables. Used in two ways:

1. From the terminal:   python validate_data.py
2. Imported by app.py so the dashboard can show a data-quality status.

Each check function returns a list of problem messages. An empty list = all good.
"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "analytics.db"

CAMPAIGN_COLUMNS = [
    "campaign_id", "campaign_name", "market", "marketing_channel", "campaign_objective",
    "reporting_currency", "marketing_spend", "impressions", "clicks",
    "landing_page_visitors", "product_interactions", "add_to_cart",
    "checkout_started", "purchases", "attributed_revenue",
]
PAYMENT_COLUMNS = [
    "market", "payment_method", "checkout_attempts", "successful_payments",
    "failed_payments", "completed_orders",
]
# Funnel columns in order. Each value must be <= the one before it.
FUNNEL_ORDER = [
    "impressions", "clicks", "landing_page_visitors", "product_interactions",
    "add_to_cart", "checkout_started", "purchases",
]


def validate_campaigns(df):
    problems = []

    missing_cols = [c for c in CAMPAIGN_COLUMNS if c not in df.columns]
    if missing_cols:
        return [f"campaigns: missing columns {missing_cols}"]

    if df.empty:
        return ["campaigns: table is empty"]

    nulls = df[CAMPAIGN_COLUMNS].isna().sum()
    for col, count in nulls[nulls > 0].items():
        problems.append(f"campaigns: {count} missing value(s) in '{col}'")

    if df["campaign_id"].duplicated().any():
        problems.append("campaigns: duplicate campaign_id values")

    if df["reporting_currency"].nunique() != 1:
        problems.append("campaigns: more than one reporting currency found "
                        f"({sorted(df['reporting_currency'].dropna().unique())})")

    numeric_cols = ["marketing_spend", "attributed_revenue"] + FUNNEL_ORDER
    for col in numeric_cols:
        if (df[col] < 0).any():
            problems.append(f"campaigns: negative values in '{col}'")

    # The funnel must never grow from one stage to the next.
    for earlier, later in zip(FUNNEL_ORDER[:-1], FUNNEL_ORDER[1:]):
        bad = int((df[later] > df[earlier]).sum())
        if bad:
            problems.append(f"campaigns: {bad} row(s) where '{later}' > '{earlier}'")

    return problems


def validate_payments(df):
    problems = []

    missing_cols = [c for c in PAYMENT_COLUMNS if c not in df.columns]
    if missing_cols:
        return [f"payments: missing columns {missing_cols}"]

    if df.empty:
        return ["payments: table is empty"]

    nulls = df[PAYMENT_COLUMNS].isna().sum()
    for col, count in nulls[nulls > 0].items():
        problems.append(f"payments: {count} missing value(s) in '{col}'")

    if df.duplicated(subset=["market", "payment_method"]).any():
        problems.append("payments: duplicate market + payment_method rows")

    count_cols = ["checkout_attempts", "successful_payments", "failed_payments", "completed_orders"]
    for col in count_cols:
        if (df[col] < 0).any():
            problems.append(f"payments: negative values in '{col}'")

    mismatch = int((df["successful_payments"] + df["failed_payments"] != df["checkout_attempts"]).sum())
    if mismatch:
        problems.append(f"payments: {mismatch} row(s) where successful + failed != attempts")

    too_many = int((df["completed_orders"] > df["successful_payments"]).sum())
    if too_many:
        problems.append(f"payments: {too_many} row(s) where completed_orders > successful_payments")

    return problems


def load_tables(db_path=DB_PATH):
    """Read both tables from the SQLite file into Pandas DataFrames."""
    conn = sqlite3.connect(db_path)
    try:
        campaigns = pd.read_sql_query("SELECT * FROM campaigns", conn)
        payments = pd.read_sql_query("SELECT * FROM payments", conn)
    finally:
        conn.close()
    return campaigns, payments


def main():
    if not DB_PATH.exists():
        raise SystemExit("Database not found. Run:  python build_database.py  first.")

    campaigns, payments = load_tables()
    problems = validate_campaigns(campaigns) + validate_payments(payments)

    print(f"Checked {len(campaigns)} campaign rows and {len(payments)} payment rows.")
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print("  - " + p)
        raise SystemExit(1)
    print("All validation checks passed.")


if __name__ == "__main__":
    main()
