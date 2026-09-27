"""
Reusable performance & risk metrics (used by the notebooks and the dashboard).

All functions take pandas Series/DataFrames of DAILY simple returns
(one column per asset). 252 trading days per year is the market convention.
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252
RISK_FREE = 0.06   # assumed annual risk-free rate (~ Indian 91-day T-bill yields over the period); change if needed


def growth(returns):
    """Value of ₹1 invested: (1 + r1)(1 + r2)..."""
    return (1 + returns.fillna(0)).cumprod()


def cagr(returns):
    """Compound annual growth rate, using the actual calendar length of the data."""
    g = growth(returns)
    years = (g.index[-1] - g.index[0]).days / 365.25
    return g.iloc[-1] ** (1 / years) - 1


def volatility(returns):
    """Annualised volatility = standard deviation of daily returns × √252."""
    return returns.std() * np.sqrt(TRADING_DAYS)


def drawdown(returns):
    """Percentage below the previous peak, for every day (0 = at a new high)."""
    g = growth(returns)
    return g / g.cummax() - 1


def max_drawdown(returns):
    """The worst peak-to-trough fall."""
    return drawdown(returns).min()


def beta(returns, benchmark):
    """Sensitivity to the market: covariance(asset, market) / variance(market)."""
    df = pd.concat([returns, benchmark], axis=1).dropna()
    cov = df.cov()
    return cov.iloc[:-1, -1] / df.iloc[:, -1].var() if isinstance(returns, pd.DataFrame) \
        else cov.iloc[0, 1] / cov.iloc[1, 1]


def var_historical(returns, level=0.95):
    """1-day Value at Risk: the loss exceeded on only (1 - level) of days (reported as a positive number)."""
    return -returns.quantile(1 - level)


def cvar_historical(returns, level=0.95):
    """Expected Shortfall / CVaR: the average loss on the days worse than the VaR."""
    q = returns.quantile(1 - level)
    if isinstance(returns, pd.DataFrame):
        return -returns[returns.le(q)].mean()
    return -returns[returns <= q].mean()


def sharpe(returns, rf=RISK_FREE):
    """(annualised average return − risk-free rate) / annualised volatility."""
    excess = returns.mean() * TRADING_DAYS - rf
    return excess / volatility(returns)


def sortino(returns, rf=RISK_FREE):
    """Like Sharpe, but only penalises DOWNSIDE volatility (days with negative returns)."""
    downside = returns.clip(upper=0)
    downside_dev = np.sqrt((downside ** 2).mean()) * np.sqrt(TRADING_DAYS)
    return (returns.mean() * TRADING_DAYS - rf) / downside_dev


def summary_table(returns, benchmark_col, rf=RISK_FREE):
    """One row per asset with all key metrics."""
    bench = returns[benchmark_col]
    out = pd.DataFrame({
        "CAGR": cagr(returns),
        "Volatility": volatility(returns),
        "Max drawdown": max_drawdown(returns),
        "Beta": beta(returns, bench),
        "VaR 95% (1-day)": var_historical(returns),
        "CVaR 95% (1-day)": cvar_historical(returns),
        "Sharpe": sharpe(returns, rf),
        "Sortino": sortino(returns, rf),
    })
    out.loc[benchmark_col, "Beta"] = 1.0
    return out
