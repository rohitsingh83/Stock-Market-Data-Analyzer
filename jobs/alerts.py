"""Evaluate technical alert rules (RSI_LT, CLOSE_LT_BBLOWER) on latest candles."""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ingest import fetch_or_simulate_ohlcv
from src.indicators import compute_indicators


def check_technical_alerts(df: pd.DataFrame, ticker: str) -> list[dict]:
    latest = df.iloc[-1]
    alerts = []
    if pd.notna(latest["rsi14"]) and latest["rsi14"] < 30:
        alerts.append({"ticker": ticker, "rule": "RSI_LT_30", "value": round(float(latest["rsi14"]), 2)})
    if pd.notna(latest["bb_lower"]) and latest["close"] < latest["bb_lower"]:
        alerts.append({"ticker": ticker, "rule": "CLOSE_LT_BBLOWER", "value": round(float(latest["close"]), 2)})
    return alerts


def main(ticker: str = "AAPL") -> None:
    print(f"Checking technical alerts for {ticker}...")
    df, mode = fetch_or_simulate_ohlcv(ticker, ROOT / "data", use_live=False)
    ind = compute_indicators(df)
    alerts = check_technical_alerts(ind, ticker)
    if alerts:
        print(f"Triggered {len(alerts)} alerts for {ticker}:")
        for a in alerts:
            print(f"  - [{a['rule']}] Value: {a['value']}")
    else:
        print(f"No technical alerts triggered for {ticker}.")


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    main(t)
