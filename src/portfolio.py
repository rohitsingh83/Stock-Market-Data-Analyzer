"""
Portfolio optimisation with Modern Portfolio Theory (Markowitz).

We simulate thousands of random portfolios (different weights for each stock),
compute each one's expected return and risk, and pick:
  - the maximum-Sharpe portfolio (best return per unit of risk)
  - the minimum-volatility portfolio (smoothest ride)
The cloud of points forms the "efficient frontier".
"""

import numpy as np
import pandas as pd

from .analysis import RISK_FREE, TRADING_DAYS


def simulate_portfolios(closes: pd.DataFrame, n: int = 4000, seed: int = 0, rf: float = RISK_FREE) -> pd.DataFrame:
    returns = closes.pct_change().dropna()
    mean = returns.mean().to_numpy() * TRADING_DAYS
    cov = returns.cov().to_numpy() * TRADING_DAYS
    rng = np.random.default_rng(seed)
    w = rng.dirichlet(np.ones(len(closes.columns)), n)        # random weights that sum to 1
    port_ret = w @ mean
    port_vol = np.sqrt(np.einsum("ij,jk,ik->i", w, cov, w))
    df = pd.DataFrame(w, columns=closes.columns)
    df["Return"], df["Volatility"] = port_ret, port_vol
    df["Sharpe"] = (port_ret - rf) / port_vol
    return df


def best_portfolios(sim: pd.DataFrame) -> dict[str, pd.Series]:
    return {"Max Sharpe": sim.loc[sim["Sharpe"].idxmax()], "Min volatility": sim.loc[sim["Volatility"].idxmin()]}
