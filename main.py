"""
Stock Market Data Analyzer: command-line tool.

    python main.py analyze RELIANCE.NS             indicators, signals, risk metrics, backtests, report
    python main.py analyze AAPL --source live      any Yahoo Finance ticker (needs internet)
    python main.py compare                         compare the watchlist against NIFTY 50
    python main.py backtest TCS.NS --strategy "RSI mean reversion"
    python main.py portfolio                       efficient frontier + optimal weights

--source auto (default) downloads real data and falls back to the bundled sample data offline.
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src import charts
from src.analysis import compare, correlation, normalised, performance_summary
from src.backtest import STRATEGIES, run_backtest
from src.data_loader import INDEX, WATCHLIST, close_matrix, load_many, load_prices
from src.indicators import add_indicators
from src.portfolio import best_portfolios, simulate_portfolios
from src.report import excel_report
from src.signals import overall_view, signal_snapshot

ROOT = Path(__file__).resolve().parent
OUT, IMG = ROOT / "outputs", ROOT / "images"
console = Console()
VERDICT = {"Bullish": "green", "Bearish": "red", "Neutral": "yellow"}
PCT = {"Total return", "CAGR", "Volatility", "Max drawdown", "VaR 95% (1 day)", "Best day", "Worst day",
       "Positive days", "Alpha", "Buy & hold return", "Buy & hold max drawdown", "Win rate", "Time invested"}


def fmt(key: str, value: float) -> str:
    return f"{value:.2%}" if key in PCT else f"{value:,.2f}" if isinstance(value, float) else str(value)


def source_note(source: str) -> str:
    return {"live": "[green]live Yahoo Finance data[/]", "cache": "[yellow]cached Yahoo Finance data[/]",
            "sample": "[yellow]offline SAMPLE data (simulated, not real prices)[/]"}[source]


def cmd_analyze(args):
    data = load_prices(args.ticker, source=args.source)
    market = load_prices(INDEX, source=args.source)
    df = add_indicators(data.df)
    summary = performance_summary(df["Close"], market.df["Close"])
    sigs = signal_snapshot(df)
    console.print(Panel.fit(f"[bold]{args.ticker}[/]  last close {df['Close'].iloc[-1]:,.2f} on "
                            f"{df.index[-1]:%d %b %Y} · {len(df)} trading days · {source_note(data.source)}",
                            title="📈 Stock Market Data Analyzer", border_style="blue"))

    t = Table(title="Risk & return", header_style="bold white on blue")
    t.add_column("Metric")
    t.add_column("Value", justify="right")
    for k, v in summary.items():
        t.add_row(k, fmt(k, v))
    console.print(t)

    s = Table(title=f"Technical signals: {overall_view(sigs)}", header_style="bold white on blue")
    for col in ["Indicator", "Reading", "Verdict"]:
        s.add_column(col)
    for sig in sigs:
        s.add_row(sig.indicator, sig.reading, f"[{VERDICT[sig.verdict]}]{sig.verdict}[/]")
    console.print(s)

    results = [run_backtest(df["Close"], name) for name in STRATEGIES]
    b = Table(title="Backtests (0.10% cost per trade, next-day execution)", header_style="bold white on blue")
    b.add_column("Metric")
    for r in results:
        b.add_column(r.strategy, justify="right")
    for key in results[0].metrics:
        b.add_row(key, *[fmt(key, r.metrics[key]) for r in results])
    console.print(b)

    OUT.mkdir(exist_ok=True)
    IMG.mkdir(exist_ok=True)
    name = args.ticker.replace(".NS", "").replace("^", "")
    comparison = compare(close_matrix(load_many(WATCHLIST, source=args.source)), market.df["Close"])
    report = OUT / f"{name}_analysis.xlsx"
    report.write_bytes(excel_report(args.ticker, df, summary, comparison, results))
    charts.technical_chart(df.tail(260), args.ticker, IMG / f"{name}_technical.png")
    best = max(results, key=lambda r: r.metrics["Sharpe"])
    charts.equity_chart(best, args.ticker, IMG / f"{name}_backtest.png")
    console.print(f"\nSaved {report.relative_to(ROOT)}, images/{name}_technical.png, images/{name}_backtest.png")
    console.print("[dim]Educational project, not investment advice.[/]")


def cmd_compare(args):
    data = load_many(WATCHLIST + [INDEX], source=args.source)
    closes = close_matrix({t: d for t, d in data.items() if t != INDEX})
    table = compare(closes, data[INDEX].df["Close"])
    t = Table(title=f"Watchlist vs NIFTY 50 · {source_note(data[WATCHLIST[0]].source)}", header_style="bold white on blue")
    cols = ["Total return", "CAGR", "Volatility", "Sharpe", "Max drawdown", "Beta"]
    t.add_column("Ticker")
    for c in cols:
        t.add_column(c, justify="right")
    for ticker, row in table.sort_values("Sharpe", ascending=False).iterrows():
        t.add_row(ticker, *[fmt(c, row[c]) for c in cols])
    console.print(t)
    IMG.mkdir(exist_ok=True)
    all_closes = close_matrix(data)
    charts.normalised_chart(normalised(all_closes), IMG / "relative_performance.png")
    charts.correlation_heatmap(correlation(all_closes), IMG / "correlation_heatmap.png")
    table.to_csv(OUT / "watchlist_comparison.csv")
    console.print("Saved outputs/watchlist_comparison.csv, images/relative_performance.png, images/correlation_heatmap.png")


def cmd_backtest(args):
    data = load_prices(args.ticker, source=args.source)
    r = run_backtest(data.df["Close"], args.strategy, cost_bps=args.cost)
    console.print(f"[bold]{args.strategy}[/] on {args.ticker} ({source_note(data.source)})\n{STRATEGIES[args.strategy]}")
    for k, v in r.metrics.items():
        console.print(f"  {k:<26}{fmt(k, v):>12}")
    if not r.trades.empty:
        console.print(r.trades.round(3).to_string(index=False))


def cmd_portfolio(args):
    data = load_many(WATCHLIST, source=args.source)
    closes = close_matrix(data)
    sim = simulate_portfolios(closes)
    best = best_portfolios(sim)
    t = Table(title="Optimal portfolios (4,000 simulated)", header_style="bold white on blue")
    t.add_column("Ticker")
    for name in best:
        t.add_column(name, justify="right")
    for ticker in closes.columns:
        t.add_row(ticker, *[f"{best[n][ticker]:.1%}" for n in best])
    for metric in ["Return", "Volatility", "Sharpe"]:
        t.add_row(f"[bold]{metric}[/]", *[fmt("CAGR" if metric != "Sharpe" else metric, best[n][metric]) for n in best])
    console.print(t)
    IMG.mkdir(exist_ok=True)
    charts.frontier_chart(sim, best, IMG / "efficient_frontier.png")
    console.print("Saved images/efficient_frontier.png")


def main():
    p = argparse.ArgumentParser(description="Stock Market Data Analyzer")
    p.add_argument("--source", choices=["auto", "live", "sample"], default="auto")
    sub = p.add_subparsers(dest="command")
    a = sub.add_parser("analyze")
    a.add_argument("ticker", nargs="?", default="RELIANCE.NS")
    sub.add_parser("compare")
    b = sub.add_parser("backtest")
    b.add_argument("ticker", nargs="?", default="RELIANCE.NS")
    b.add_argument("--strategy", choices=list(STRATEGIES), default="SMA crossover")
    b.add_argument("--cost", type=float, default=10, help="cost per trade in basis points")
    sub.add_parser("portfolio")
    args = p.parse_args()
    if args.command is None:
        args = p.parse_args(["analyze"])
    {"analyze": cmd_analyze, "compare": cmd_compare, "backtest": cmd_backtest, "portfolio": cmd_portfolio}[args.command](args)


if __name__ == "__main__":
    main()
