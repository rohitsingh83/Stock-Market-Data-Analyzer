"""Technical indicators (SMA20, SMA50, RSI14, MACD, Bollinger Bands) and signals."""

import numpy as np
import pandas as pd


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("date").reset_index(drop=True)
    close = out["close"]

    out["sma20"] = close.rolling(20).mean()
    out["sma50"] = close.rolling(50).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi14"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()

    std20 = close.rolling(20).std()
    out["bb_upper"] = out["sma20"] + 2 * std20
    out["bb_lower"] = out["sma20"] - 2 * std20

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
