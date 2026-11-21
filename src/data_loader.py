"""
Load daily OHLCV price data.

source="auto"   try Yahoo Finance (real data, needs internet), fall back to the
                bundled sample CSV if the download fails
source="live"   Yahoo Finance only
source="sample" bundled, simulated data in data/ (works offline)

Downloaded data is cached in data/cache/ so repeated runs are fast.
"""

import contextlib
import io
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_DIR = DATA_DIR / "cache"
INDEX = "^NSEI"   # NIFTY 50
WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]
COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


@dataclass
class PriceData:
    ticker: str
    df: pd.DataFrame
    source: str          # "live", "cache" or "sample"


def sample_file(ticker: str) -> Path:
    name = "NIFTY50" if ticker == INDEX else ticker.split(".")[0]
    return DATA_DIR / f"{name}_sample.csv"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Standard columns, date index, sorted, no duplicates, no missing or zero prices."""
    if isinstance(df.columns, pd.MultiIndex):           # yfinance returns (field, ticker) columns
        df = df.droplevel(1, axis=1)
    df = df.rename(columns=str.title)
    if "Date" in df.columns:
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df[[c for c in COLUMNS if c in df.columns]].apply(pd.to_numeric, errors="coerce")
    df = df[~df.index.duplicated()].sort_index().dropna(subset=["Close"])
    return df[df["Close"] > 0]


def fetch_live(ticker: str, start: date, end: date) -> pd.DataFrame:
    import yfinance as yf
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        raw = yf.download(ticker, start=start, end=end + timedelta(days=1), progress=False, auto_adjust=True,
                          timeout=10)
    if raw is None or raw.empty:
        raise ConnectionError(f"No data returned for {ticker}")
    df = clean(raw)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CACHE_DIR / f"{ticker.replace('^', '')}.csv")
    return df


def load_prices(ticker: str, start: date | None = None, end: date | None = None, source: str = "auto") -> PriceData:
    end = end or date.today()
    start = start or end - timedelta(days=730)
    if source in ("auto", "live"):
        try:
            return PriceData(ticker, fetch_live(ticker, start, end), "live")
        except Exception:
            if source == "live":
                raise
            cached = CACHE_DIR / f"{ticker.replace('^', '')}.csv"
            if cached.exists():
                df = clean(pd.read_csv(cached))
                return PriceData(ticker, df.loc[str(start):str(end)], "cache")
    path = sample_file(ticker)
    if not path.exists():
        raise FileNotFoundError(f"No internet data and no sample file for {ticker}. "
                                f"Offline samples: {', '.join(WATCHLIST + [INDEX])}")
    df = clean(pd.read_csv(path))
    sliced = df.loc[str(start):str(end)]
    return PriceData(ticker, sliced if len(sliced) > 30 else df, "sample")


def load_many(tickers: list[str], start=None, end=None, source="auto") -> dict[str, PriceData]:
    return {t: load_prices(t, start, end, source) for t in tickers}


def close_matrix(data: dict[str, PriceData]) -> pd.DataFrame:
    """One column of closing prices per ticker, aligned on common dates."""
    return pd.DataFrame({t: d.df["Close"] for t, d in data.items()}).dropna()
