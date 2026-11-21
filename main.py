"""End-to-end Stock Market Data Analyzer pipeline."""

import logging
import sqlite3
from src.config import settings
from src.ingest import fetch_or_simulate_ohlcv, upsert_candles
from src.indicators import compute_indicators
from src.backtest import run_sma_backtest
from src.plots import save_stock_charts

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logging.getLogger("matplotlib").setLevel(logging.WARNING)  # hide matplotlib INFO noise
logger = logging.getLogger("stock_analyzer")


def main(ticker: str = None) -> None:
    selected_ticker = ticker or settings.default_ticker
    logger.info("Starting quantitative analysis for %s...", selected_ticker)

    conn = sqlite3.connect(str(settings.db_path))
    try:
        conn.executescript(settings.schema_path.read_text(encoding="utf-8"))

        df, source_mode = fetch_or_simulate_ohlcv(selected_ticker, settings.data_dir, use_live=settings.use_live)
        upsert_candles(conn, selected_ticker, f"{selected_ticker} Inc.", df)

        ind = compute_indicators(df)
        bt = run_sma_backtest(ind, fee_bps=settings.fee_bps, risk_free_rate=settings.risk_free_rate)

        cur = conn.cursor()
        cur.execute(
            """INSERT INTO backtests (ticker, strategy, total_return_pct, sharpe_ratio, max_drawdown_pct, win_rate_pct)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (selected_ticker, "SMA20_SMA50_Crossover", bt["total_return_pct"], bt["sharpe_ratio"], bt["max_drawdown_pct"], bt["win_rate_pct"]),
        )
        conn.commit()
    finally:
        conn.close()

    out_csv = settings.outputs_dir / f"{selected_ticker}_indicators.csv"
    ind.to_csv(out_csv, index=False)
    save_stock_charts(ind, selected_ticker, settings.images_dir)

    latest = ind.iloc[-1]
    vol_annual = ind["daily_return"].std() * (252 ** 0.5) * 100
    summary = (
        f"Stock Market Analysis Report ({selected_ticker} | Mode: {source_mode})\n"
        f"Latest Close: ${latest['close']:.2f} | Signal: {latest['signal']} | RSI14: {latest['rsi14']:.2f}\n"
        f"Annualized Volatility: {vol_annual:.2f}%\n"
        f"SMA Crossover Backtest (10 bps fee): Return {bt['total_return_pct']}% (Benchmark B&H: {bt['buy_and_hold_return_pct']}%), "
        f"Sharpe {bt['sharpe_ratio']}, Max Drawdown {bt['max_drawdown_pct']}%, Win Rate {bt['win_rate_pct']}%\n"
    )
    (settings.reports_dir / f"{selected_ticker}_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
