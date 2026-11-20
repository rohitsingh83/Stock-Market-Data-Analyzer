"""Vectorized long-only SMA crossover backtesting engine with commission drag and benchmarks."""

import numpy as np
import pandas as pd


def run_sma_backtest(
    df: pd.DataFrame, 
    fee_bps: float = 10.0,
    risk_free_rate: float = 0.04
) -> dict:
    """Execute vectorized SMA crossover backtest with realistic execution friction.
    
    Args:
        df: DataFrame with 'sma20', 'sma50', and 'daily_return' columns.
        fee_bps: Brokerage / exchange commission drag in basis points per rebalance.
        risk_free_rate: Annualized risk-free benchmark rate (default: 4.0%).
        
    Returns:
        Dictionary of strategy performance metrics including benchmark comparisons.
    """
    bt = df.dropna(subset=["sma20", "sma50", "daily_return"]).copy()
    if bt.empty:
        return {
            "total_return_pct": 0.0,
            "buy_and_hold_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate_pct": 0.0,
            "trade_signals": 0,
        }

    # Signal generated on Day T, executed at Day T+1
    bt["position"] = (bt["sma20"] > bt["sma50"]).astype(int).shift(1).fillna(0)
    trades = bt["position"].diff().abs().fillna(0)
    fee_drag = trades * (fee_bps / 10000.0)

    bt["strategy_return"] = bt["position"] * bt["daily_return"] - fee_drag
    bt["equity"] = (1 + bt["strategy_return"]).cumprod()
    bt["benchmark_equity"] = (1 + bt["daily_return"]).cumprod()

    total_ret = (bt["equity"].iloc[-1] - 1) * 100
    bnh_ret = (bt["benchmark_equity"].iloc[-1] - 1) * 100
    
    # Excess return over daily risk-free rate
    daily_rf = risk_free_rate / 252.0
    excess_return = bt["strategy_return"] - daily_rf
    std = bt["strategy_return"].std()
    sharpe = (excess_return.mean() / std * np.sqrt(252)) if std and std > 0 else 0.0

    roll_max = bt["equity"].cummax()
    drawdown = (bt["equity"] / roll_max - 1) * 100
    max_dd = drawdown.min() if not drawdown.empty else 0.0

    active_days = bt[bt["position"] == 1]["strategy_return"]
    win_rate = (active_days > 0).mean() * 100 if len(active_days) > 0 else 0.0

    return {
        "total_return_pct": round(float(total_ret), 2),
        "buy_and_hold_return_pct": round(float(bnh_ret), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "max_drawdown_pct": round(float(max_dd), 2),
        "win_rate_pct": round(float(win_rate), 2),
        "trade_signals": int(trades.sum()),
    }
