"""
NSE Portfolio Analytics: interactive dashboard (Streamlit)

Run locally (from the project folder, .venv active):
    python -m streamlit run dashboard/app.py

The app rebuilds the analysis tables in memory from the committed price snapshot
(data/raw/prices.parquet) using the SAME SQL files and Python modules as the notebooks,
so the numbers always match the analysis.
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))
import metrics as m          # noqa: E402  (our own risk functions)
import optimize as opt       # noqa: E402  (our own optimisation & backtest functions)
from build_models import BUILD_ORDER  # noqa: E402

BLUE, ORANGE, AQUA, VIOLET, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7", "#898781"
BENCH = "Nifty 50 Index"

st.set_page_config(page_title="NSE Portfolio Analytics", page_icon="📈", layout="wide")


# ------------------------------------------------------------------ data
@st.cache_data
def load_data():
    """Rebuild clean daily returns in an in-memory DuckDB using the pipeline's SQL files."""
    con = duckdb.connect()
    con.execute("CREATE SCHEMA raw; CREATE SCHEMA staging; CREATE SCHEMA marts;")
    con.execute(f"CREATE TABLE raw.prices AS SELECT * FROM '{(ROOT / 'data/raw/prices.parquet').as_posix()}'")
    con.execute(f"CREATE TABLE raw.universe AS SELECT * FROM read_csv('{(ROOT / 'config/universe.csv').as_posix()}', header=true)")
    for model in BUILD_ORDER:
        con.execute((ROOT / "sql" / f"{model}.sql").read_text())
    df = con.execute("SELECT date, name, sector, daily_return FROM marts.daily_returns").df()
    universe = con.execute("SELECT name, sector, ticker FROM raw.universe").df().set_index("name")
    con.close()
    rets = df.pivot(index="date", columns="name", values="daily_return").iloc[1:]
    rets.index = pd.to_datetime(rets.index)
    return rets, universe


@st.cache_data
def run_backtests(_returns, key):
    stocks = _returns.drop(columns=BENCH)
    out, expected = {}, {}
    for s in ["Equal-weight", "Min-volatility", "Max-Sharpe"]:
        out[s], expected[s] = opt.walk_forward(stocks, s)
    bt = pd.DataFrame(out)
    bt[BENCH] = _returns.loc[bt.index, BENCH]
    return bt, expected


def inr(x):
    """Format rupees the Indian way: ₹53.6 L (lakh) / ₹1.24 Cr (crore)."""
    return f"₹{x / 1e7:,.2f} Cr" if x >= 1e7 else f"₹{x / 1e5:,.1f} L" if x >= 1e5 else f"₹{x:,.0f}"


def style(fig, height=400):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(size=13), title_font=dict(size=16),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, title=None),
                      hovermode="x unified")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(137,135,129,0.25)", zeroline=False)
    return fig


returns, universe = load_data()
all_stocks = sorted(c for c in returns.columns if c != BENCH)
last_date = returns.index[-1].date()

# ------------------------------------------------------------------ sidebar: portfolio builder
st.sidebar.title("Build a portfolio")
default = ["Titan Company", "HDFC Bank", "Infosys", "Reliance Industries", "Hindustan Unilever",
           "Sun Pharma", "Bharti Airtel", "Larsen & Toubro"]
chosen = st.sidebar.multiselect("Stocks", all_stocks, default=[s for s in default if s in all_stocks])
method = st.sidebar.radio("Weighting", ["Equal weight", "Custom", "Min-volatility", "Max-Sharpe"],
                          help="Min-volatility and Max-Sharpe are optimised on the selected period, which is "
                               "hindsight. See the Backtest tab for the honest version.")
max_w = st.sidebar.slider("Max weight per stock (optimisers)", 0.10, 1.0, 0.30, 0.05,
                          disabled=method not in ("Min-volatility", "Max-Sharpe"))
years = sorted(returns.index.year.unique())
start_year = st.sidebar.select_slider("Start year", options=years[:-1], value=years[0])
amount = st.sidebar.number_input("Amount invested (₹)", min_value=10_000, value=10_00_000, step=50_000)
st.sidebar.caption(f"Prices: Yahoo Finance, adjusted for splits & dividends · data to {last_date}. "
                   "Benchmark (Nifty 50) excludes dividends. For education only, not investment advice.")

st.title("📈 NSE Portfolio Risk & Performance Analytics")
st.caption("27 large NSE stocks vs the Nifty 50 · returns, risk, optimisation and an honest out-of-sample backtest · "
           "built with Python, DuckDB and Streamlit")

if len(chosen) < 2:
    st.warning("Pick at least 2 stocks in the sidebar.")
    st.stop()

period = returns[returns.index >= f"{start_year}-01-01"]
sel = period[chosen]
mu, cov = opt.annualised_inputs(sel)

if method == "Equal weight":
    weights = pd.Series(1 / len(chosen), index=chosen)
elif method == "Custom":
    with st.sidebar.expander("Set weights", expanded=True):
        raw = pd.Series({s: st.slider(s, 0, 100, 10, key=f"w_{s}") for s in chosen}, dtype=float)
    weights = raw / raw.sum() if raw.sum() > 0 else pd.Series(1 / len(chosen), index=chosen)
elif method == "Min-volatility":
    weights = opt.min_vol_weights(mu, cov, max(max_w, 1 / len(chosen)))
else:
    weights = opt.max_sharpe_weights(mu, cov, max(max_w, 1 / len(chosen)))
weights = weights.clip(lower=0)
weights = weights / weights.sum()

port = opt.buy_and_hold(sel, weights).rename("Your portfolio")
both = pd.concat([port, period[BENCH]], axis=1)

tab_port, tab_stocks, tab_frontier, tab_bt, tab_about = st.tabs(
    ["💼 Your portfolio", "🔎 Stock explorer", "🎯 Efficient frontier", "🧪 Honest backtest", "💡 Key insights"])

# ------------------------------------------------------------------ tab: portfolio
with tab_port:
    s = m.summary_table(both, BENCH)
    p, b = s.loc["Your portfolio"], s.loc[BENCH]
    growth = m.growth(both)
    k = st.columns(6)
    k[0].metric("Value today", inr(amount * growth['Your portfolio'].iloc[-1]),
                f"Nifty: {inr(amount * growth[BENCH].iloc[-1])}", delta_color="off")
    k[1].metric("CAGR", f"{p['CAGR']:.1%}", f"{p['CAGR'] - b['CAGR']:+.1%} vs Nifty")
    k[2].metric("Volatility", f"{p['Volatility']:.1%}", f"{p['Volatility'] - b['Volatility']:+.1%} vs Nifty", delta_color="inverse")
    k[3].metric("Sharpe ratio", f"{p['Sharpe']:.2f}", f"Nifty {b['Sharpe']:.2f}", delta_color="off",
                help=f"(annual return − {m.RISK_FREE:.0%} risk-free) ÷ volatility")
    k[4].metric("Max drawdown", f"{p['Max drawdown']:.0%}", f"Nifty {b['Max drawdown']:.0%}", delta_color="off")
    k[5].metric("1-day VaR 95%", inr(p['VaR 95% (1-day)'] * amount * growth['Your portfolio'].iloc[-1]),
                help="On the worst 1 day in 20, expect to lose at least this much (based on history).")

    c1, c2 = st.columns([2, 1])
    fig = go.Figure()
    fig.add_scatter(x=growth.index, y=growth["Your portfolio"] * amount / 1e5, name="Your portfolio", line=dict(color=BLUE, width=2.5),
                    hovertemplate="₹%{y:,.1f} L")
    fig.add_scatter(x=growth.index, y=growth[BENCH] * amount / 1e5, name="Nifty 50", line=dict(color=ORANGE, width=1.8),
                    hovertemplate="₹%{y:,.1f} L")
    fig.update_layout(title=f"Growth of {inr(amount)} since {start_year}")
    fig.update_yaxes(tickprefix="₹", ticksuffix=" L", tickformat=",.0f")      # values shown in lakhs
    c1.plotly_chart(style(fig, 420), width="stretch")

    w = weights[weights > 0.001].sort_values()
    fig = go.Figure(go.Bar(x=w.values, y=w.index, orientation="h", marker_color=BLUE,
                           text=[f"{v:.0%}" for v in w.values], textposition="outside", cliponaxis=False))
    fig.update_layout(title=f"Weights ({method.lower()})", hovermode="closest")
    fig.update_xaxes(tickformat=".0%", showgrid=True, gridcolor="rgba(137,135,129,0.25)", range=[0, w.max() * 1.25])
    c2.plotly_chart(style(fig, 420), width="stretch")

    c1, c2 = st.columns(2)
    dd = m.drawdown(both)
    fig = go.Figure()
    fig.add_scatter(x=dd.index, y=dd[BENCH], name="Nifty 50", fill="tozeroy", line=dict(color=ORANGE, width=1), opacity=0.4)
    fig.add_scatter(x=dd.index, y=dd["Your portfolio"], name="Your portfolio", line=dict(color=BLUE, width=1.5))
    fig.update_layout(title="Drawdown from previous peak")
    fig.update_yaxes(tickformat=".0%")
    c1.plotly_chart(style(fig, 380), width="stretch")

    yearly = (1 + both).groupby(both.index.year).prod() - 1
    fig = go.Figure()
    fig.add_bar(x=yearly.index.astype(str), y=yearly["Your portfolio"], name="Your portfolio", marker_color=BLUE)
    fig.add_bar(x=yearly.index.astype(str), y=yearly[BENCH], name="Nifty 50", marker_color=ORANGE)
    fig.update_layout(title=f"Calendar-year returns ({last_date.year} = year to date)", barmode="group")
    fig.update_yaxes(tickformat=".0%")
    c2.plotly_chart(style(fig, 380), width="stretch")

    if method in ("Min-volatility", "Max-Sharpe"):
        st.info("⚠️ These weights were optimised using the same period they're evaluated on (**in-sample / hindsight**). "
                "The *Honest backtest* tab shows how optimisers perform on data they haven't seen.")

# ------------------------------------------------------------------ tab: stock explorer
with tab_stocks:
    table = m.summary_table(period, BENCH)
    table.insert(0, "Sector", universe["sector"].reindex(table.index))
    fig = go.Figure()
    stocks_only = table.drop(index=BENCH)
    fig.add_scatter(x=stocks_only["Volatility"], y=stocks_only["CAGR"], mode="markers+text", text=stocks_only.index,
                    textposition="top center", textfont=dict(size=10, color=GREY),
                    marker=dict(size=11, color=[BLUE if n in chosen else GREY for n in stocks_only.index]),
                    customdata=np.stack([stocks_only["Sharpe"], stocks_only["Sector"]], axis=1),
                    hovertemplate="<b>%{text}</b><br>CAGR %{y:.1%} · Vol %{x:.1%}<br>Sharpe %{customdata[0]:.2f} · %{customdata[1]}<extra></extra>",
                    name="stocks (blue = in your portfolio)")
    fig.add_scatter(x=[table.loc[BENCH, "Volatility"]], y=[table.loc[BENCH, "CAGR"]], mode="markers",
                    marker=dict(size=16, symbol="diamond", color=ORANGE), name="Nifty 50",
                    hovertemplate="<b>Nifty 50</b><br>CAGR %{y:.1%} · Vol %{x:.1%}<extra></extra>")
    fig.update_layout(title=f"Risk vs return since {start_year}", hovermode="closest")
    fig.update_xaxes(tickformat=".0%", title="volatility (risk)", showgrid=True, gridcolor="rgba(137,135,129,0.25)")
    fig.update_yaxes(tickformat=".0%", title="CAGR (return)")
    st.plotly_chart(style(fig, 520), width="stretch")

    st.dataframe(table.sort_values("Sharpe", ascending=False), width="stretch",
                 column_config={
                     "CAGR": st.column_config.NumberColumn(format="percent"),
                     "Volatility": st.column_config.NumberColumn(format="percent"),
                     "Max drawdown": st.column_config.NumberColumn(format="percent"),
                     "Beta": st.column_config.NumberColumn(format="%.2f"),
                     "VaR 95% (1-day)": st.column_config.NumberColumn(format="percent"),
                     "CVaR 95% (1-day)": st.column_config.NumberColumn(format="percent"),
                     "Sharpe": st.column_config.NumberColumn(format="%.2f"),
                     "Sortino": st.column_config.NumberColumn(format="%.2f"),
                 })

# ------------------------------------------------------------------ tab: efficient frontier
with tab_frontier:
    st.caption("Built from the stocks you selected, over the selected period (in hindsight).")
    cloud = opt.random_portfolios(mu, cov, n=4000)
    frontier = opt.efficient_frontier(mu, cov, points=25, max_weight=1.0)
    fig = go.Figure()
    fig.add_scatter(x=cloud["volatility"], y=cloud["return"], mode="markers", name="random portfolios",
                    marker=dict(size=4, color=cloud["sharpe"], colorscale="Blues", showscale=True,
                                colorbar=dict(title="Sharpe")), hoverinfo="skip")
    fig.add_scatter(x=frontier["volatility"], y=frontier["return"], mode="lines", name="efficient frontier",
                    line=dict(color="#0b0b0b", width=2.5))
    r_, v_, s_ = opt.portfolio_stats(weights.values, mu, cov)
    fig.add_scatter(x=[v_], y=[r_], mode="markers", name="your portfolio",
                    marker=dict(size=18, symbol="star", color=ORANGE, line=dict(color="white", width=1)),
                    hovertemplate=f"Your portfolio<br>return %{{y:.1%}} · vol %{{x:.1%}} · Sharpe {s_:.2f}<extra></extra>")
    fig.update_layout(title="Efficient frontier for your stocks", hovermode="closest")
    fig.update_xaxes(tickformat=".0%", title="volatility (risk)", showgrid=True, gridcolor="rgba(137,135,129,0.25)")
    fig.update_yaxes(tickformat=".0%", title="expected annual return")
    st.plotly_chart(style(fig, 520), width="stretch")
    st.markdown("Portfolios on the **black line** get the most return for their risk. If your ⭐ is far below it, "
                "a different mix of the same stocks would have been more efficient.")

# ------------------------------------------------------------------ tab: backtest
with tab_bt:
    st.markdown("**Walk-forward test (all 27 stocks):** every January from 2019, each strategy picks weights using **only the previous 3 years**, "
                "holds them for the year (weights drift with prices), and pays **0.2% trading costs**. This is the honest, out-of-sample result.")
    with st.spinner("Running backtests…"):
        bt, expected = run_backtests(returns, str(last_date))
    s = m.summary_table(bt, BENCH)[["CAGR", "Volatility", "Max drawdown", "Sharpe"]]
    s["Sharpe expected (in-sample)"] = pd.Series(expected)
    g = m.growth(bt)
    fig = go.Figure()
    for name, col in [("Equal-weight", VIOLET), ("Min-volatility", AQUA), ("Max-Sharpe", ORANGE), (BENCH, GREY)]:
        fig.add_scatter(x=g.index, y=g[name], name=name, line=dict(color=col, width=2.2 if name != BENCH else 1.6))
    fig.update_layout(title="Out-of-sample growth of ₹1 since Jan 2019 (after costs)")
    st.plotly_chart(style(fig, 440), width="stretch")
    st.dataframe(s, width="stretch", column_config={
        "CAGR": st.column_config.NumberColumn(format="percent"),
        "Volatility": st.column_config.NumberColumn(format="percent"),
        "Max drawdown": st.column_config.NumberColumn(format="percent"),
        "Sharpe": st.column_config.NumberColumn("Sharpe achieved", format="%.2f"),
        "Sharpe expected (in-sample)": st.column_config.NumberColumn(format="%.2f")})
    st.success("**Lesson:** the max-Sharpe optimiser promised the most and delivered the least. It overfits past winners. "
               "Simple equal weighting was the best risk-adjusted strategy, and min-volatility had the smallest drawdown. "
               "Risk is predictable; returns are not.")

# ------------------------------------------------------------------ tab: insights
with tab_about:
    st.subheader("Key findings (Jan 2016 onwards)")
    st.markdown("""
1. **The Nifty 50 compounded at ~10.7% a year** (₹1 → ~₹3). Simple averages overstate this by ~1 point (volatility drag).
2. **Big dispersion:** Bajaj Finance (~30%/yr), Titan (~28%) and Tata Steel (~24%) led; TCS, Infosys, ITC and Wipro **lagged the index**.
3. **Diversification cuts risk dramatically:** single stocks swing ~27%/yr vs ~16% for the index; ~10 stocks capture most of the benefit.
4. **Crashes are more common than bell curves assume:** 5× more ±3σ days than a normal distribution predicts.
5. **COVID crash:** Nifty −38% in 69 days; low-beta defensives (HUL, Dr. Reddy's, Nestle) fell about half as much; correlations jumped 0.22 → 0.60.
6. **Optimisers overfit:** out of sample, max-Sharpe expected a Sharpe of ~1.9 but delivered ~0.44; equal-weight (0.66) and min-volatility (lowest drawdown) did better.
""")
    st.subheader("Caveats")
    st.markdown("- **Survivorship bias:** the universe is today's large caps, which flatters past performance.\n"
                "- The **Nifty 50 price index excludes dividends** (~1–1.5%/yr), while stock prices include them.\n"
                f"- Risk-free rate assumed at {m.RISK_FREE:.0%}. Educational project, **not investment advice**.")
    st.info("Code, SQL models and notebooks: [github.com/adhirajsinha1/nse-portfolio-analytics]"
            "(https://github.com/adhirajsinha1/nse-portfolio-analytics)")
