"""Market OHLCV ingestion via yfinance with deterministic offline simulation fallback."""

import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd


def generate_synthetic_ohlcv(ticker: str, days: int = 252, seed: int = 42) -> pd.DataFrame:
    """Generate realistic daily OHLCV candles for offline simulation."""
    rng = np.random.default_rng(seed + sum(ord(c) for c in ticker))
    dates = pd.bdate_range(end="2026-11-18", periods=days)
    returns = rng.normal(loc=0.0006, scale=0.016, size=days)
    close = 180.0 * np.exp(np.cumsum(returns))
    open_p = np.roll(close, 1)
    open_p[0] = close[0] * 0.995
    high = np.maximum(open_p, close) * (1 + rng.uniform(0.002, 0.015, size=days))
    low = np.minimum(open_p, close) * (1 - rng.uniform(0.002, 0.015, size=days))
    volume = rng.integers(15_000_000, 65_000_000, size=days)

    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": np.round(open_p, 2),
        "high": np.round(high, 2),
        "low": np.round(low, 2),
        "close": np.round(close, 2),
        "volume": volume,
    })


def fetch_or_simulate_ohlcv(ticker: str, data_dir: Path, use_live: bool = False) -> tuple[pd.DataFrame, str]:
    csv_path = data_dir / f"{ticker}_daily.csv"
    if use_live:
        try:
            import yfinance as yf
            hist = yf.Ticker(ticker).history(period="1y")
            if not hist.empty:
                hist = hist.reset_index()
                df = pd.DataFrame({
                    "date": pd.to_datetime(hist["Date"]).dt.strftime("%Y-%m-%d"),
                    "open": hist["Open"].round(2),
                    "high": hist["High"].round(2),
                    "low": hist["Low"].round(2),
                    "close": hist["Close"].round(2),
                    "volume": hist["Volume"].astype(int),
                })
                df.to_csv(csv_path, index=False)
                return df, "yfinance-live"
        except Exception:
            pass

    if csv_path.exists():
        return pd.read_csv(csv_path), "cached-csv"

    df = generate_synthetic_ohlcv(ticker)
    df.to_csv(csv_path, index=False)
    return df, "simulation"


def upsert_candles(conn: sqlite3.Connection, ticker: str, name: str, df: pd.DataFrame) -> None:
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO symbols (ticker, name) VALUES (?, ?)", (ticker, name))
    for _, r in df.iterrows():
        cur.execute(
            """INSERT OR REPLACE INTO candles_daily (ticker, date, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ticker, r["date"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), int(r["volume"])),
        )
    conn.commit()
