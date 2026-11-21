"""
Create offline sample price data so the project runs without internet.

IMPORTANT: these prices are SIMULATED, not real market history. When you are
online, the app downloads real data from Yahoo Finance (yfinance) instead.

How the simulation works (a standard quant technique):
  - a market index follows geometric Brownian motion with changing "regimes"
    (calm bull market, volatile correction, recovery)
  - each stock = beta x market return + its own random return, so stocks are
    correlated with the market and with each other, like real ones
  - OHLC and volume are derived from the daily close with realistic noise

Run:  python scripts/generate_sample_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data"
rng = np.random.default_rng(21)

DATES = pd.bdate_range("2024-11-20", "2026-11-20")
N = len(DATES)

# (ticker, start price, beta to market, own annual drift, own annual volatility, avg volume)
STOCKS = [
    ("RELIANCE.NS", 1290, 1.05, 0.04, 0.16, 9_000_000),
    ("TCS.NS", 4150, 0.75, 0.01, 0.15, 2_500_000),
    ("INFY.NS", 1880, 0.85, 0.03, 0.18, 6_000_000),
    ("HDFCBANK.NS", 1760, 0.95, 0.06, 0.14, 11_000_000),
    ("TATAMOTORS.NS", 790, 1.45, -0.02, 0.30, 15_000_000),
]

# market regimes: (number of days, annual drift, annual volatility)
REGIMES = [(120, 0.18, 0.12), (70, -0.30, 0.24), (110, 0.25, 0.14), (60, 0.02, 0.18), (N, 0.14, 0.13)]


def market_returns() -> np.ndarray:
    out = []
    for days, mu, sigma in REGIMES:
        out.append(rng.normal(mu / 252, sigma / np.sqrt(252), days))
    return np.concatenate(out)[:N]


def to_ohlcv(close: np.ndarray, avg_volume: int, daily_vol: float) -> pd.DataFrame:
    prev = np.concatenate([[close[0]], close[:-1]])
    open_ = prev * (1 + rng.normal(0, daily_vol * 0.3, N))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, daily_vol * 0.5, N)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, daily_vol * 0.5, N)))
    move = np.abs(close / prev - 1)
    volume = (avg_volume * (0.6 + rng.lognormal(0, 0.35, N)) * (1 + 8 * move)).astype(int)
    return pd.DataFrame({"Date": DATES, "Open": open_, "High": high, "Low": low, "Close": close,
                         "Volume": volume}).round({"Open": 2, "High": 2, "Low": 2, "Close": 2})


def main() -> None:
    OUT.mkdir(exist_ok=True)
    mkt = market_returns()
    index_close = 23_500 * np.cumprod(1 + mkt)
    to_ohlcv(index_close, 300_000_000, 0.009).to_csv(OUT / "NIFTY50_sample.csv", index=False)
    print(f"NIFTY50_sample.csv  {index_close[0]:,.0f} -> {index_close[-1]:,.0f}")
    for ticker, start, beta, mu, sigma, vol in STOCKS:
        own = rng.normal(mu / 252, sigma / np.sqrt(252), N)
        r = beta * mkt + own
        close = start * np.cumprod(1 + r)
        name = ticker.replace(".NS", "") + "_sample.csv"
        to_ohlcv(close, vol, float(np.std(r))).to_csv(OUT / name, index=False)
        print(f"{name:24} {close[0]:,.0f} -> {close[-1]:,.0f}")


if __name__ == "__main__":
    main()
