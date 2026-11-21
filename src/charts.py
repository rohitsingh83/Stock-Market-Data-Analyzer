"""Static Matplotlib charts for the README and Excel report."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .backtest import BacktestResult

plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9})


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def technical_chart(df: pd.DataFrame, ticker: str, path: Path) -> Path:
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(11, 10), sharex=True,
                                             gridspec_kw={"height_ratios": [3, 1, 1, 1]})
    ax1.plot(df.index, df["Close"], color="#0F172A", lw=1.3, label="Close")
    ax1.plot(df.index, df["SMA50"], color="#2563EB", lw=1, label="SMA 50")
    ax1.plot(df.index, df["SMA200"], color="#DC2626", lw=1, label="SMA 200")
    ax1.fill_between(df.index, df["BB_lower"], df["BB_upper"], color="#93C5FD", alpha=.25, label="Bollinger bands")
    ax1.set_title(f"{ticker}: price, moving averages and Bollinger bands", weight="bold", fontsize=12)
    ax1.legend(loc="upper left", frameon=False, ncol=4)
    colours = ["#16A34A" if r >= 0 else "#DC2626" for r in df["Close"].diff().fillna(0)]
    ax2.bar(df.index, df["Volume"], color=colours, width=1)
    ax2.set_ylabel("Volume")
    ax3.plot(df.index, df["RSI14"], color="#7C3AED", lw=1)
    ax3.axhline(70, color="#DC2626", ls="--", lw=.8)
    ax3.axhline(30, color="#16A34A", ls="--", lw=.8)
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("RSI 14")
    ax4.plot(df.index, df["MACD"], color="#2563EB", lw=1, label="MACD")
    ax4.plot(df.index, df["MACD_signal"], color="#F59E0B", lw=1, label="Signal")
    ax4.bar(df.index, df["MACD_hist"], color=["#16A34A" if h >= 0 else "#DC2626" for h in df["MACD_hist"]], width=1)
    ax4.set_ylabel("MACD")
    ax4.legend(loc="upper left", frameon=False, ncol=2)
    return _save(fig, path)


def equity_chart(result: BacktestResult, ticker: str, path: Path) -> Path:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    eq = result.equity
    ax1.plot(eq.index, eq["Strategy"], color="#2563EB", lw=1.6, label=f"{result.strategy}")
    ax1.plot(eq.index, eq["Buy & Hold"], color="#94A3B8", lw=1.3, label="Buy & hold")
    ax1.set_ylabel("Growth of ₹1")
    ax1.set_title(f"Backtest on {ticker}: {result.strategy} vs buy & hold", weight="bold", fontsize=12)
    ax1.legend(frameon=False)
    dd = eq["Strategy"] / eq["Strategy"].cummax() - 1
    ax2.fill_between(dd.index, dd * 100, 0, color="#DC2626", alpha=.35)
    ax2.set_ylabel("Drawdown %")
    return _save(fig, path)


def normalised_chart(norm: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11, 5))
    for col in norm.columns:
        ax.plot(norm.index, norm[col], lw=1.4, label=col.replace(".NS", ""))
    ax.axhline(100, color="#94A3B8", lw=.8)
    ax.set_ylabel("Value of ₹100 invested")
    ax.set_title("Relative performance (all start at 100)", weight="bold", fontsize=12)
    ax.legend(frameon=False, ncol=6)
    return _save(fig, path)


def correlation_heatmap(corr: pd.DataFrame, path: Path) -> Path:
    labels = [c.replace(".NS", "").replace("^", "") for c in corr.columns]
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(corr, cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)), labels, rotation=40, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=.8)
    ax.set_title("Correlation of daily returns", weight="bold", fontsize=12)
    return _save(fig, path)


def frontier_chart(sim: pd.DataFrame, best: dict, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sc = ax.scatter(sim["Volatility"] * 100, sim["Return"] * 100, c=sim["Sharpe"], cmap="viridis", s=6, alpha=.7)
    for name, row, marker in [("Max Sharpe", best["Max Sharpe"], "*"), ("Min volatility", best["Min volatility"], "D")]:
        ax.scatter(row["Volatility"] * 100, row["Return"] * 100, marker=marker, s=220, color="#DC2626",
                   edgecolor="white", label=name, zorder=3)
    fig.colorbar(sc, ax=ax, label="Sharpe ratio")
    ax.set_xlabel("Risk: annual volatility (%)")
    ax.set_ylabel("Expected annual return (%)")
    ax.set_title("Efficient frontier: 4,000 random portfolios", weight="bold", fontsize=12)
    ax.legend(frameon=False)
    return _save(fig, path)
