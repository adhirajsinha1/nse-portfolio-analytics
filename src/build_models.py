"""
STEP 2 OF THE PIPELINE: clean the raw prices and build analysis tables.

    raw.prices ──(sql/staging)──► staging.clean_prices ──(sql/marts)──► marts.daily_returns, marts.annual_returns
                                                                           └──(sql/tests)──► data quality tests

Run after fetch_prices.py:
    python src/build_models.py
"""
from pathlib import Path
import sys
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
DB_PATH = PROJECT_ROOT / "data" / "portfolio.duckdb"

BUILD_ORDER = [
    "staging/clean_prices",
    "marts/daily_returns",
    "marts/annual_returns",
]


def main():
    if not DB_PATH.exists():
        sys.exit("Database not found. Run `python src/fetch_prices.py` first.")
    con = duckdb.connect(str(DB_PATH))
    for schema in ("staging", "marts"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    print("\n1) Building tables")
    for model in BUILD_ORDER:
        con.execute((SQL_DIR / f"{model}.sql").read_text())
        table = model.replace("/", ".")
        rows = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  ✔ {table:<28} {rows:>8,} rows")

    print("\n2) Running data tests")
    failures = 0
    for path in sorted((SQL_DIR / "tests").glob("*.sql")):
        bad = con.execute(path.read_text()).fetchall()
        print(f"  {'✘ FAIL' if bad else '✔ pass'}  {path.stem}" + (f"  ({len(bad)} bad rows, e.g. {bad[0]})" if bad else ""))
        failures += bool(bad)
    con.close()

    if failures:
        sys.exit(f"\n{failures} test(s) failed.")
    print("\nAll tests passed.")


if __name__ == "__main__":
    main()
