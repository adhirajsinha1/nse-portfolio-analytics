# Executive Summary: NSE Large-Cap Portfolio Analysis (Jan 2016 – Sep 2026)

**Prepared by:** Adhiraj Sinha · **Universe:** 27 large NSE stocks (11 sectors) vs the Nifty 50 · **Dashboard:** [live link](https://nse-portfolio-adhiraj.streamlit.app/)

## Bottom line
Indian large caps rewarded investors well (Nifty 50 ~10.7%/yr), but **returns were very uneven and risk came in bursts**.
**Diversification across sectors and low-beta defensives** protected investors best in the COVID crash. **Optimised "max-Sharpe" portfolios failed out of sample**, while simple equal weighting and minimum-volatility portfolios held up.

## What we found
| Area | Finding |
|---|---|
| Returns | Nifty 50 ~10.7% CAGR; 16 of 27 stocks beat it; leaders Bajaj Finance (~30%), Titan (~28%), Tata Steel (~24%); IT and pharma lagged (~10%) |
| Risk | Single stocks ~27% volatility vs ~16% for the index; extreme days 5× more frequent than a normal distribution predicts |
| Crisis | COVID: Nifty −38% in 69 days, 7.5-month recovery; defensives (HUL, Dr. Reddy's, Nestle, Cipla) fell only 17–23%; correlations rose 0.22 → 0.60 |
| Risk-adjusted | Titan best (Sharpe 0.81); Nifty 0.35; ITC, Wipro, TCS, Dr. Reddy's < 0.2 |
| Tail risk | Nifty 95% 1-day VaR 1.43% (≈ ₹14k on ₹10L); average loss beyond it (CVaR) 2.34% |
| Portfolios (out-of-sample 2019–26) | Equal-weight Sharpe 0.66 (best); min-volatility smallest drawdown (−29%); max-Sharpe promised 1.86, delivered 0.44 |

## Recommendations
1. **Diversify across sectors, not just stock count.** Same-sector stocks move together (IT pairs ~0.6 correlation); ~10–15 well-spread stocks capture most of the benefit.
2. **Hold low-beta defensives (pharma, FMCG) for crash protection.** Correlations spike in crises, so more stocks alone won't protect a portfolio.
3. **Distrust optimised portfolios built on past returns.** Validate any strategy out of sample, and prefer robust rules (equal weight, min-volatility, weight caps).
4. **Monitor tail risk, not just volatility.** Use historical VaR/CVaR and drawdown limits, because normal-distribution models understate crash risk.

## Caveats
Survivorship bias (universe = today's large caps); Nifty 50 price index excludes dividends (~1–1.5%/yr); risk-free rate assumed at 6%; daily data from Yahoo Finance. **Not investment advice.**
