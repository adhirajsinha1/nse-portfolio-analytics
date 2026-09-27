# Data Quality Report: NSE Daily Prices

**Source:** Yahoo Finance via `yfinance` (adjusted daily OHLCV) · **Universe:** 27 NSE large caps + Nifty 50 (`^NSEI`) · **Period:** Jan 2016 onwards
**Method:** SQL checks in DuckDB, see [`notebooks/01_data_pipeline_quality.ipynb`](../notebooks/01_data_pipeline_quality.ipynb)

## Checks and results
| # | Check | Result | Decision |
|---|---|---|---|
| 1 | Corporate actions (splits, bonuses, dividends) | Unadjusted prices understate returns heavily (ITC: 1.28× price growth vs 1.88× total return since 2016) | Use **adjusted** prices (`auto_adjust=True`) |
| 2 | Missing history, duplicates, impossible OHLC (close outside high–low), non-positive prices | None found; all 27 stocks have full history since Jan 2016 | No action |
| 3 | Provider-filled holiday rows (volume = 0 and price unchanged) | A handful of dates (e.g. 18 Mar 2025 for 26 stocks) | **Drop**, since they add fake 0% return days |
| 4 | Dates where stocks have data but the index doesn't (incl. Diwali Muhurat sessions on weekends) | 11 dates | Analyse on a **common calendar** of index trading days |
| 5 | Extreme daily moves beyond ±15% | 14 cases, all real events: COVID crash (Mar 2020), SBI recapitalisation (Oct 2017), election results (Jun 2024), Infosys whistleblower (Oct 2019) | **Keep**, they're genuine shocks |
| 6 | Benchmark is the Nifty 50 *price* index (excludes dividends) | Understates benchmark return by ~1–1.5% per year | Keep; **state the caveat** in comparisons |
| 7 | Universe chosen from today's large caps | Survivorship bias flatters historical performance | State it; evaluate strategies **out-of-sample** only |

## Trading calendar
~241–250 trading days per year (vs 365 calendar days). Annualisation uses **252**, the market convention.
