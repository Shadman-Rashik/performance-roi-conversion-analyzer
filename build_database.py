"""
build_database.py
-----------------
Builds the SQLite database file from the CSV files.

Run:    python build_database.py
Input:  data/campaigns.csv, data/payments.csv, sql/schema.sql
Output: data/analytics.db   (a single file; SQLite needs no server)
"""

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "analytics.db"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def main():
    campaigns_csv = DATA_DIR / "campaigns.csv"
    payments_csv = DATA_DIR / "payments.csv"

    if not campaigns_csv.exists() or not payments_csv.exists():
        raise SystemExit("CSV files not found. Run:  python generate_data.py  first.")

    campaigns = pd.read_csv(campaigns_csv)
    payments = pd.read_csv(payments_csv)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1) Create the empty tables (this also deletes old versions).
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        # 2) Fill them. If any row breaks a CHECK rule, SQLite raises an error.
        campaigns.to_sql("campaigns", conn, if_exists="append", index=False)
        payments.to_sql("payments", conn, if_exists="append", index=False)
        conn.commit()

        n_campaigns = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        n_payments = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    finally:
        conn.close()

    print(f"Created {DB_PATH}")
    print(f"  campaigns table: {n_campaigns} rows")
    print(f"  payments table:  {n_payments} rows")


if __name__ == "__main__":
    main()
