"""Interactive Streamlit dashboard for Stock Market Data Analyzer."""
from pathlib import Path
import streamlit as st
import pandas as pd

from src.ingest import fetch_or_simulate_ohlcv
from src.indicators import compute_indicators
from src.backtest import run_sma_backtest
from src.plots import save_stock_charts
from src.portfolio import compute_portfolio_pnl
from jobs.alerts import check_technical_alerts

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Quantitative Equity & Backtesting Lab",
    layout="wide",
    page_icon="📈",
)

st.title("📈 Quantitative Equity Analysis & Strategy Lab")
st.caption("Vectorized Technical Indicators, Golden-Cross Backtesting & Portfolio P&L")

# Sidebar
with st.sidebar:
    st.header("⚙️ Parameters & Asset")
    ticker = st.selectbox("Select Equity Ticker", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"])
    fee_bps = st.slider("Trading Fee Drag (basis points)", min_value=0.0, max_value=50.0, value=10.0, step=1.0)
    use_live = st.checkbox("Attempt Live Yahoo Finance Fetch", value=False)
    st.markdown("---")
    st.markdown("### 📚 Indicator Guide")
    st.markdown("- **Trend:** SMA20 vs SMA50")
    st.markdown("- **Momentum:** RSI 14 (Overbought > 70, Oversold < 30)")
    st.markdown("- **Volatility:** Bollinger Bands & ATR")

# Fetch and compute
df, mode = fetch_or_simulate_ohlcv(ticker, ROOT / "data", use_live=use_live)
ind = compute_indicators(df)
bt = run_sma_backtest(ind, fee_bps=fee_bps)
save_stock_charts(ind, ticker, ROOT / "images")

latest = ind.iloc[-1]
alerts = check_technical_alerts(ind, ticker)

# Top KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Latest Close", f"${latest['close']:.2f}")
signal_color = "🟢" if latest["signal"] == "BUY" else ("🔴" if latest["signal"] == "SELL" else "⚪")
c2.metric("Technical Signal", f"{signal_color} {latest['signal']}")
c3.metric("RSI (14)", f"{latest['rsi14']:.1f}")
c4.metric("Backtest Return", f"{bt['total_return_pct']}%", delta=f"{bt['total_return_pct']}%")
c5.metric("Sharpe Ratio", f"{bt['sharpe_ratio']:.2f}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Technical Charts", "⚙️ Backtest Breakdown", "⚠️ Technical Alerts", "💼 Portfolio Simulator"])

with tab1:
    st.subheader(f"Price & Momentum Charts for {ticker} (Source: {mode})")
    col1, col2 = st.columns(2)
    with col1:
        p_chart = ROOT / "images" / f"{ticker}_price_sma.png"
        if p_chart.exists():
            st.image(str(p_chart), caption=f"{ticker} Moving Average Crossover", use_container_width=True)
    with col2:
        d_chart = ROOT / "images" / f"{ticker}_returns_dist.png"
        if d_chart.exists():
            st.image(str(d_chart), caption=f"{ticker} Daily Return Distribution", use_container_width=True)

    st.subheader("Recent Historical Indicators")
    cols_to_show = [c for c in ["date", "close", "sma20", "sma50", "rsi14", "macd", "atr14", "signal"] if c in ind.columns]
    st.dataframe(ind.tail(15)[cols_to_show], use_container_width=True)

with tab2:
    st.subheader("SMA (20 / 50) Crossover Performance Audit")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Strategy Net Return", f"{bt['total_return_pct']}%")
    m2.metric("Sharpe Ratio (Annualized)", f"{bt['sharpe_ratio']}")
    m3.metric("Maximum Drawdown", f"{bt['max_drawdown_pct']}%")
    m4.metric("Win Rate", f"{bt['win_rate_pct']}%")
    st.info(f"Total Trade Signals Executed: **{bt.get('trade_signals', 0)}** with **{fee_bps} bps** commission drag.")

with tab3:
    st.subheader("Active Technical Rule Alerts")
    if alerts:
        for a in alerts:
            st.warning(f"⚠️ Rule **{a['rule']}** triggered for {a['ticker']}: Value = {a['value']}")
    else:
        st.success(f"No extreme technical alerts triggered for {ticker} (RSI in normal range, price within Bollinger bands).")

with tab4:
    st.subheader("Mark-to-Market Portfolio P&L Calculator")
    sample_trades = [
        {"ticker": ticker, "qty": 100, "avg_cost": round(latest["close"] * 0.95, 2)},
        {"ticker": "MSFT", "qty": 50, "avg_cost": 415.00},
    ]
    latest_prices = {ticker: round(float(latest["close"]), 2), "MSFT": 425.50}
    pnl_df = compute_portfolio_pnl(sample_trades, latest_prices)
    st.dataframe(pnl_df, use_container_width=True)
    st.success(f"Total Unrealized P&L: **${pnl_df['unrealized_pnl'].sum():,.2f}**")
