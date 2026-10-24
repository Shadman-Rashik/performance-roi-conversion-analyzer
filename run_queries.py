"""
run_queries.py
--------------
Runs every query in sql/queries.sql against data/analytics.db and prints the results.

Run:  python run_queries.py
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "analytics.db"
QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"


def split_queries(sql_text):
    """Cut the SQL file into (title, sql) pairs using the '-- name:' markers."""
    parts = re.split(r"^-- name:\s*", sql_text, flags=re.MULTILINE)
    queries = []
    for part in parts[1:]:                       # parts[0] is the file header
        title, _, body = part.partition("\n")
        queries.append((title.strip(), body.strip()))
    return queries


def main():
    if not DB_PATH.exists():
        raise SystemExit("Database not found. Run:  python build_database.py  first.")

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)

    queries = split_queries(QUERIES_PATH.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    try:
        for title, sql in queries:
            print("=" * 100)
            print(title)
            print("=" * 100)
            result = pd.read_sql_query(sql, conn)
            print(result.to_string(index=False))
            print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
