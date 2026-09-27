# NSE Portfolio Risk & Performance Analytics

> 🚧 Work in progress: this README is finished at the end of the project with findings and a live dashboard link.

Automated analytics on **10 years of daily prices for 27 large NSE stocks** across 11 sectors, benchmarked against the **Nifty 50**:
returns, risk (volatility, drawdown, beta, VaR), risk-adjusted performance (Sharpe, Sortino), diversification and portfolio optimisation
with an honest out-of-sample backtest.

## Business questions
1. Which stocks and sectors delivered the best returns, and did they beat the Nifty 50?
2. How risky were they? How deep were the drawdowns, and how did they behave in the COVID crash?
3. Were the returns worth the risk (risk-adjusted performance)?
4. Can diversification and optimisation build a better portfolio, and does it hold up on unseen data?

## Tech stack
Python (yfinance, pandas, NumPy, SciPy) · SQL (DuckDB) · Matplotlib / Plotly · Streamlit · Git & GitHub

## Pipeline
```
config/universe.csv → src/fetch_prices.py (Yahoo Finance API) → data/raw/prices.parquet + DuckDB raw
                    → src/build_models.py → staging.clean_prices → marts.daily_returns / annual_returns (+ tests)
                    → analysis notebooks → Streamlit dashboard
```

## Project structure
```
config/        stock universe (edit to analyse different stocks)
data/raw/      price snapshot (Parquet), committed for reproducibility
sql/           cleaning models, analysis tables and data tests
src/           pipeline scripts + shared chart style
notebooks/     analysis notebooks
reports/       written findings and charts
```

## How to run
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/fetch_prices.py      # downloads fresh prices into DuckDB
python src/build_models.py      # cleans prices, builds returns tables, runs 6 data tests
```
Then open the notebooks in `notebooks/` in order.

## Progress
- [x] Data pipeline and data quality checks ([report](reports/data_quality_report.md))
- [x] Returns and performance vs Nifty 50 ([notebook](notebooks/02_returns_performance.ipynb))
- [ ] Risk metrics and COVID crash case study
- [ ] Diversification, optimisation and out-of-sample backtest
- [ ] Interactive dashboard
- [ ] Final findings and recommendations

*Data: Yahoo Finance via yfinance, for educational purposes only. Not investment advice.*
