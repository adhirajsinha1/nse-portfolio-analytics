"""
STEP 1 OF THE PIPELINE: download daily stock prices and load them into DuckDB.

    config/universe.csv  (which stocks)  ──►  Yahoo Finance (yfinance)
        ──►  data/raw/prices.parquet   (a snapshot file, committed to GitHub)
        ──►  data/portfolio.duckdb     (raw.prices, raw.universe tables)

Run from the project folder, with .venv active:
    python src/fetch_prices.py
Re-running it downloads fresh data up to today.
"""
from pathlib import Path
import sys

import duckdb
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UNIVERSE_CSV = PROJECT_ROOT / "config" / "universe.csv"
RAW_PARQUET = PROJECT_ROOT / "data" / "raw" / "prices.parquet"
DB_PATH = PROJECT_ROOT / "data" / "portfolio.duckdb"
START_DATE = "2016-01-01"   # ~10 years of history


def download_prices(tickers):
    """
    Download daily prices for all tickers in one request.

    auto_adjust=True gives ADJUSTED prices: past prices are corrected for stock
    splits, bonus issues and dividends, so returns are comparable over time.
    Without this, a 1:10 split would look like a 90% crash!
    """
    wide = yf.download(tickers, start=START_DATE, auto_adjust=True, progress=False, threads=True)
    if wide.empty:
        sys.exit("Download returned no data. Check your internet connection and try again.")

    # yfinance returns a "wide" table (one column per ticker per field).
    # We reshape it to a "long" table: one row per (date, ticker), the format databases like.
    long = (wide.stack(level="Ticker", future_stack=True)
                .reset_index()
                .rename(columns=str.lower)
                .rename(columns={"ticker": "ticker"}))
    long = long[["date", "ticker", "open", "high", "low", "close", "volume"]]
    long = long.dropna(subset=["close"])            # drop dates where a ticker didn't trade
    long["date"] = pd.to_datetime(long["date"]).dt.date
    return long


def main():
    universe = pd.read_csv(UNIVERSE_CSV)
    tickers = universe["ticker"].tolist()
    print(f"Downloading {len(tickers)} tickers from {START_DATE} to today...")
    prices = download_prices(tickers)

    missing = sorted(set(tickers) - set(prices["ticker"].unique()))
    if missing:
        print(f"  ⚠ No data returned for: {missing}")

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    # DuckDB can query a pandas DataFrame directly by its variable name
    con.execute("CREATE OR REPLACE TABLE raw.prices AS SELECT * FROM prices ORDER BY ticker, date")
    con.execute("CREATE OR REPLACE TABLE raw.universe AS SELECT * FROM universe")

    # Save a snapshot file (small, committed to GitHub so results are reproducible)
    RAW_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY raw.prices TO '{RAW_PARQUET.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")

    summary = con.execute("""
        SELECT COUNT(*) AS rows, COUNT(DISTINCT ticker) AS tickers, MIN(date) AS first_date, MAX(date) AS last_date
        FROM raw.prices
    """).fetchone()
    con.close()
    print(f"  ✔ raw.prices: {summary[0]:,} rows · {summary[1]} tickers · {summary[2]} → {summary[3]}")
    print(f"  ✔ snapshot saved to {RAW_PARQUET.relative_to(PROJECT_ROOT)} ({RAW_PARQUET.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
