"""Technical indicators (SMA20, SMA50, RSI14, MACD, Bollinger Bands, ATR) and signals."""

import numpy as np
import pandas as pd


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute moving averages, momentum, volatility bands, and trading signals."""
    out = df.copy().sort_values("date").reset_index(drop=True)
    close = out["close"]
    high = out["high"]
    low = out["low"]

    out["sma20"] = close.rolling(20).mean()
    out["sma50"] = close.rolling(50).mean()

    # RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi14"] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands (20, 2)
    std20 = close.rolling(20).std()
    out["bb_upper"] = out["sma20"] + 2 * std20
    out["bb_lower"] = out["sma20"] - 2 * std20

    # ATR (Average True Range, 14-period)
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    out["atr14"] = tr.rolling(14).mean()

    out["daily_return"] = close.pct_change()

    def _sig(row):
        if pd.isna(row["sma20"]) or pd.isna(row["sma50"]):
            return "HOLD"
        if row["sma20"] > row["sma50"]:
            return "BUY"
        if row["sma20"] < row["sma50"]:
            return "SELL"
        return "HOLD"

    out["signal"] = out.apply(_sig, axis=1)
    return out
