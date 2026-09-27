"""
Portfolio construction & backtesting helpers (used by notebook 04 and the dashboard).

Modern Portfolio Theory in one line: choose weights w to get the best trade-off between
expected return (w · mu) and risk (sqrt(w' Σ w)), where Σ is the covariance matrix.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from metrics import TRADING_DAYS, RISK_FREE


def annualised_inputs(returns):
    """Expected annual returns (mu) and annual covariance matrix (Σ) from daily returns."""
    return returns.mean() * TRADING_DAYS, returns.cov() * TRADING_DAYS


def portfolio_stats(weights, mu, cov, rf=RISK_FREE):
    """Return (expected return, volatility, Sharpe) for one set of weights."""
    ret = float(np.dot(weights, mu))
    vol = float(np.sqrt(weights @ cov.values @ weights))
    return ret, vol, (ret - rf) / vol


def random_portfolios(mu, cov, n=10_000, seed=42, rf=RISK_FREE):
    """Simulate n random long-only portfolios (weights ≥ 0, sum to 1)."""
    rng = np.random.default_rng(seed)
    w = rng.dirichlet(np.ones(len(mu)), size=n)          # random weights that sum to 1
    rets = w @ mu.values
    vols = np.sqrt(np.einsum("ij,jk,ik->i", w, cov.values, w))
    return pd.DataFrame({"return": rets, "volatility": vols, "sharpe": (rets - rf) / vols})


def _optimise(objective, n, max_weight, extra_constraints=()):
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}, *extra_constraints]
    result = minimize(objective, x0=np.full(n, 1 / n), method="SLSQP",
                      bounds=[(0, max_weight)] * n, constraints=constraints)
    return result.x


def max_sharpe_weights(mu, cov, max_weight=1.0, rf=RISK_FREE):
    """Weights with the highest Sharpe ratio (long-only, each weight ≤ max_weight)."""
    return pd.Series(_optimise(lambda w: -portfolio_stats(w, mu, cov, rf)[2], len(mu), max_weight), index=mu.index)


def min_vol_weights(mu, cov, max_weight=1.0):
    """Weights with the lowest possible volatility."""
    return pd.Series(_optimise(lambda w: portfolio_stats(w, mu, cov)[1], len(mu), max_weight), index=mu.index)


def efficient_frontier(mu, cov, points=40, max_weight=1.0):
    """Lowest-risk portfolio for each target return → the efficient frontier curve."""
    w_min = min_vol_weights(mu, cov, max_weight)
    r_min = portfolio_stats(w_min.values, mu, cov)[0]
    rows = []
    for target in np.linspace(r_min, mu.max() * 0.98, points):
        cons = ({"type": "eq", "fun": lambda w, t=target: np.dot(w, mu) - t},)
        w = _optimise(lambda w: portfolio_stats(w, mu, cov)[1], len(mu), max_weight, cons)
        ret, vol, _ = portfolio_stats(w, mu, cov)
        if abs(ret - target) < 1e-3:                       # keep only targets the optimiser could hit
            rows.append({"return": ret, "volatility": vol})
    return pd.DataFrame(rows)


def buy_and_hold(returns, weights):
    """Daily returns of a portfolio that starts at `weights` and then lets them drift (no rebalancing)."""
    growth = (1 + returns.fillna(0)).cumprod()
    value = growth.mul(weights, axis=1).sum(axis=1)
    return value.pct_change().fillna(value.iloc[0] - 1)
