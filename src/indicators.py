"""
Technical indicators, written from scratch with Pandas (no black-box library)
so every formula can be explained in an interview.
"""

import numpy as np
import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """Simple moving average: plain average of the last `window` closes."""
    return close.rolling(window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    """Exponential moving average: recent prices get more weight."""
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder). 0-100; above 70 = overbought, below 30 = oversold.
    RSI = 100 - 100 / (1 + average gain / average loss)
    """
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD line = EMA12 - EMA26; signal line = EMA9 of MACD; histogram = difference."""
    line = ema(close, fast) - ema(close, slow)
    sig = line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({"MACD": line, "MACD_signal": sig, "MACD_hist": line - sig})


def bollinger(close: pd.Series, window: int = 20, k: float = 2.0) -> pd.DataFrame:
    """Middle = SMA20; bands = middle ± 2 standard deviations."""
    mid = sma(close, window)
    std = close.rolling(window).std()
    return pd.DataFrame({"BB_mid": mid, "BB_upper": mid + k * std, "BB_lower": mid - k * std})


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range: typical daily price range, a volatility measure."""
    prev = df["Close"].shift()
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - prev).abs(), (df["Low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume: adds volume on up days, subtracts on down days."""
    direction = np.sign(df["Close"].diff()).fillna(0)
    return (direction * df["Volume"]).cumsum()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    c = out["Close"]
    out["SMA20"], out["SMA50"], out["SMA200"] = sma(c, 20), sma(c, 50), sma(c, 200)
    out["EMA20"] = ema(c, 20)
    out["RSI14"] = rsi(c)
    out = out.join(macd(c)).join(bollinger(c))
    out["ATR14"] = atr(out)
    out["OBV"] = obv(out)
    out["Return"] = c.pct_change()
    return out
