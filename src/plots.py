"""Stock price, moving averages, and daily return distribution charts."""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def save_stock_charts(df: pd.DataFrame, ticker: str, images_dir: Path) -> None:
    dates = pd.to_datetime(df["date"])

    # 1. Closing Price + SMA20/SMA50
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, df["close"], label="Close", color="#1565C0", linewidth=1.6)
    ax.plot(dates, df["sma20"], label="SMA 20", color="#EF6C00", linewidth=1.3)
    ax.plot(dates, df["sma50"], label="SMA 50", color="#2E7D32", linewidth=1.3)
    ax.set_title(f"{ticker} Closing Price & Moving Averages", fontweight="bold")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(images_dir / f"{ticker}_price_sma.png", dpi=150)
    plt.close(fig)

    # 2. Daily Returns Histogram
    fig, ax = plt.subplots(figsize=(8, 4.5))
    df["daily_return"].dropna().mul(100).hist(bins=30, color="#00838F", edgecolor="white", ax=ax)
    ax.set_title(f"{ticker} Daily Returns Distribution (%)", fontweight="bold")
    ax.set_xlabel("Daily Return (%)")
    ax.set_ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(images_dir / f"{ticker}_returns_dist.png", dpi=150)
    plt.close(fig)
