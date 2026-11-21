"""
Backtesting: "if I had followed this rule in the past, what would have happened?"

Rules are long-only (either fully invested or in cash). To avoid look-ahead
bias, a signal computed on today's close is traded on the NEXT day.
Each buy or sell costs `cost_bps` basis points (0.10% default) for brokerage,
taxes and slippage.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .analysis import TRADING_DAYS, max_drawdown, sharpe
from .indicators import macd, rsi, sma

STRATEGIES = {
    "SMA crossover": "Hold when the short moving average is above the long one.",
    "RSI mean reversion": "Buy when RSI drops below the lower level, sell when it rises above the upper level.",
    "MACD momentum": "Hold while the MACD line is above its signal line.",
}


@dataclass
class BacktestResult:
    strategy: str
    equity: pd.DataFrame        # columns: Strategy, Buy & Hold (both start at 1.0)
    position: pd.Series         # 1 = invested, 0 = cash
    trades: pd.DataFrame
    metrics: dict


def positions(close: pd.Series, strategy: str, **p) -> pd.Series:
    if strategy == "SMA crossover":
        fast, slow = sma(close, p.get("fast", 20)), sma(close, p.get("slow", 50))
        return (fast > slow).astype(int)
    if strategy == "RSI mean reversion":
        r = rsi(close, p.get("period", 14))
        lower, upper = p.get("lower", 30), p.get("upper", 70)
        state, pos = 0, []
        for value in r:
            if value < lower:
                state = 1
            elif value > upper:
                state = 0
            pos.append(state)
        return pd.Series(pos, index=close.index)
    if strategy == "MACD momentum":
        m = macd(close)
        return (m["MACD"] > m["MACD_signal"]).astype(int)
    raise ValueError(f"Unknown strategy {strategy!r}. Choose from {list(STRATEGIES)}")


def run_backtest(close: pd.Series, strategy: str = "SMA crossover", cost_bps: float = 10, **params) -> BacktestResult:
    pos = positions(close, strategy, **params).shift(1).fillna(0)   # trade the day after the signal
    ret = close.pct_change().fillna(0)
    changes = pos.diff().abs().fillna(pos.iloc[0])
    strat_ret = pos * ret - changes * cost_bps / 10_000
    equity = pd.DataFrame({"Strategy": (1 + strat_ret).cumprod(), "Buy & Hold": (1 + ret).cumprod()})

    # list of round-trip trades
    trades, entry = [], None
    for day, (prev, now) in zip(pos.index, zip(pos.shift(1).fillna(0), pos)):
        if now == 1 and prev == 0:
            entry = day
        elif now == 0 and prev == 1 and entry is not None:
            trades.append((entry, day, close[entry], close[day]))
            entry = None
    if entry is not None:
        trades.append((entry, close.index[-1], close[entry], close.iloc[-1]))
    tdf = pd.DataFrame(trades, columns=["Entry date", "Exit date", "Entry price", "Exit price"])
    if not tdf.empty:
        tdf["Return"] = tdf["Exit price"] / tdf["Entry price"] - 1 - 2 * cost_bps / 10_000
        tdf["Days held"] = (tdf["Exit date"] - tdf["Entry date"]).dt.days

    years = len(close) / TRADING_DAYS
    final = equity["Strategy"].iloc[-1]
    metrics = {
        "Total return": float(final - 1),
        "Buy & hold return": float(equity["Buy & Hold"].iloc[-1] - 1),
        "CAGR": float(final ** (1 / years) - 1) if years else 0.0,
        "Sharpe": sharpe(strat_ret[1:]),
        "Max drawdown": max_drawdown(equity["Strategy"]),
        "Buy & hold max drawdown": max_drawdown(equity["Buy & Hold"]),
        "Trades": int(len(tdf)),
        "Win rate": float((tdf["Return"] > 0).mean()) if not tdf.empty else 0.0,
        "Time invested": float(pos.mean()),
    }
    return BacktestResult(strategy, equity, pos, tdf, metrics)
