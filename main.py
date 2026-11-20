"""End-to-end Stock Market Data Analyzer pipeline."""

import sqlite3
from pathlib import Path
from src.ingest import fetch_or_simulate_ohlcv, upsert_candles
from src.indicators import compute_indicators
from src.backtest import run_sma_backtest
from src.plots import save_stock_charts

ROOT = Path(__file__).resolve().parent


def main(ticker: str = "AAPL") -> None:
    conn = sqlite3.connect(str(ROOT / "db" / "market.db"))
    conn.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))

    df, source_mode = fetch_or_simulate_ohlcv(ticker, ROOT / "data", use_live=False)
    upsert_candles(conn, ticker, f"{ticker} Inc.", df)

    ind = compute_indicators(df)
    bt = run_sma_backtest(ind, fee_bps=10.0)

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO backtests (ticker, strategy, total_return_pct, sharpe_ratio, max_drawdown_pct, win_rate_pct)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (ticker, "SMA20_SMA50_Crossover", bt["total_return_pct"], bt["sharpe_ratio"], bt["max_drawdown_pct"], bt["win_rate_pct"]),
    )
    conn.commit()
    conn.close()

    ind.to_csv(ROOT / "outputs" / f"{ticker}_indicators.csv", index=False)
    save_stock_charts(ind, ticker, ROOT / "images")

    latest = ind.iloc[-1]
    vol_annual = ind["daily_return"].std() * (252 ** 0.5) * 100
    summary = (
        f"Stock Market Analysis Report ({ticker} | Mode: {source_mode})\n"
        f"Latest Close: ${latest['close']:.2f} | Signal: {latest['signal']} | RSI14: {latest['rsi14']:.2f}\n"
        f"Annualized Volatility: {vol_annual:.2f}%\n"
        f"SMA Crossover Backtest (10 bps fee): Return {bt['total_return_pct']}%, Sharpe {bt['sharpe_ratio']}, "
        f"Max Drawdown {bt['max_drawdown_pct']}%, Win Rate {bt['win_rate_pct']}%\n"
    )
    (ROOT / "reports" / f"{ticker}_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
