"""
Risk and return statistics used by analysts and fund managers.

Conventions: 252 trading days per year; risk-free rate 6.5% (approx. Indian
10-year government bond yield), configurable.
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252
RISK_FREE = 0.065


def daily_returns(close: pd.Series) -> pd.Series:
    return close.pct_change().dropna()


def cagr(close: pd.Series) -> float:
    """Compound annual growth rate: the steady yearly return that gives the same result."""
    years = len(close) / TRADING_DAYS
    return float((close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1) if years > 0 else 0.0


def volatility(returns: pd.Series) -> float:
    """Annualised standard deviation of daily returns."""
    return float(returns.std() * np.sqrt(TRADING_DAYS))


def sharpe(returns: pd.Series, rf: float = RISK_FREE) -> float:
    """Extra return per unit of total risk."""
    excess = returns - rf / TRADING_DAYS
    return float(excess.mean() / excess.std() * np.sqrt(TRADING_DAYS)) if excess.std() else 0.0


def sortino(returns: pd.Series, rf: float = RISK_FREE) -> float:
    """Like Sharpe but only penalises downside volatility."""
    excess = returns - rf / TRADING_DAYS
    downside = excess[excess < 0].std()
    return float(excess.mean() / downside * np.sqrt(TRADING_DAYS)) if downside else 0.0


def drawdown(close: pd.Series) -> pd.Series:
    """How far below its previous peak the price is, at every point in time."""
    return close / close.cummax() - 1


def max_drawdown(close: pd.Series) -> float:
    return float(drawdown(close).min())


def value_at_risk(returns: pd.Series, level: float = 0.95) -> float:
    """Historical VaR: on 95% of days the loss was smaller than this."""
    return float(-np.percentile(returns, (1 - level) * 100))


def beta_alpha(returns: pd.Series, market: pd.Series, rf: float = RISK_FREE) -> tuple[float, float]:
    """Beta = sensitivity to the market; alpha = annual return not explained by the market (CAPM)."""
    joined = pd.concat([returns, market], axis=1, join="inner").dropna()
    if len(joined) < 20:
        return float("nan"), float("nan")
    r, m = joined.iloc[:, 0], joined.iloc[:, 1]
    beta = float(np.cov(r, m)[0, 1] / np.var(m, ddof=1))
    alpha = float((r.mean() - rf / TRADING_DAYS - beta * (m.mean() - rf / TRADING_DAYS)) * TRADING_DAYS)
    return beta, alpha


def performance_summary(close: pd.Series, market_close: pd.Series | None = None) -> dict:
    r = daily_returns(close)
    out = {
        "Start price": float(close.iloc[0]),
        "Last price": float(close.iloc[-1]),
        "Total return": float(close.iloc[-1] / close.iloc[0] - 1),
        "CAGR": cagr(close),
        "Volatility": volatility(r),
        "Sharpe": sharpe(r),
        "Sortino": sortino(r),
        "Max drawdown": max_drawdown(close),
        "VaR 95% (1 day)": value_at_risk(r),
        "Best day": float(r.max()),
        "Worst day": float(r.min()),
        "Positive days": float((r > 0).mean()),
    }
    if market_close is not None:
        out["Beta"], out["Alpha"] = beta_alpha(r, daily_returns(market_close))
    return out


def compare(closes: pd.DataFrame, market_close: pd.Series | None = None) -> pd.DataFrame:
    return pd.DataFrame({t: performance_summary(closes[t], market_close) for t in closes.columns}).T


def correlation(closes: pd.DataFrame) -> pd.DataFrame:
    return closes.pct_change().dropna().corr()


def normalised(closes: pd.DataFrame) -> pd.DataFrame:
    """Every series starts at 100, so different price levels can be compared."""
    return closes / closes.iloc[0] * 100
