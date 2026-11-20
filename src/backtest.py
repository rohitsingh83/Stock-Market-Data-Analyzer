"""Vectorized long-only SMA20 > SMA50 crossover backtest with transaction fees."""

import numpy as np
import pandas as pd


def run_sma_backtest(df: pd.DataFrame, fee_bps: float = 10.0) -> dict:
    bt = df.dropna(subset=["sma20", "sma50", "daily_return"]).copy()
    bt["position"] = (bt["sma20"] > bt["sma50"]).astype(int).shift(1).fillna(0)
    trades = bt["position"].diff().abs().fillna(0)
    fee_drag = trades * (fee_bps / 10000.0)

    bt["strategy_return"] = bt["position"] * bt["daily_return"] - fee_drag
    bt["equity"] = (1 + bt["strategy_return"]).cumprod()

    total_ret = (bt["equity"].iloc[-1] - 1) * 100 if not bt.empty else 0.0
    std = bt["strategy_return"].std()
    sharpe = (bt["strategy_return"].mean() / std * np.sqrt(252)) if std and std > 0 else 0.0

    roll_max = bt["equity"].cummax()
    drawdown = (bt["equity"] / roll_max - 1) * 100
    max_dd = drawdown.min() if not drawdown.empty else 0.0

    active_days = bt[bt["position"] == 1]["strategy_return"]
    win_rate = (active_days > 0).mean() * 100 if len(active_days) > 0 else 0.0

    return {
        "total_return_pct": round(float(total_ret), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "max_drawdown_pct": round(float(max_dd), 2),
        "win_rate_pct": round(float(win_rate), 2),
        "trade_signals": int(trades.sum()),
    }
