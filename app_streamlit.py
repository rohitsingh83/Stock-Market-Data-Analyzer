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
st.set_page_config(page_title="Stock Market Data Analyzer", layout="wide", page_icon="📈")
st.title("📈 Stock Market Data Analyzer & Strategy Backtester")

# Sidebar Controls
st.sidebar.header("Asset Selection & Parameters")
ticker = st.sidebar.selectbox("Select Equity Ticker", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"])
use_live = st.sidebar.checkbox("Attempt Live Yahoo Finance Fetch", value=False)
fee_bps = st.sidebar.slider("Trading Fee (basis points)", min_value=0.0, max_value=50.0, value=10.0, step=1.0)

# Fetch Data
df, mode = fetch_or_simulate_ohlcv(ticker, ROOT / "data", use_live=use_live)
ind = compute_indicators(df)
bt = run_sma_backtest(ind, fee_bps=fee_bps)

# Generate latest charts
save_stock_charts(ind, ticker, ROOT / "images")

# Top KPI metrics
latest = ind.iloc[-1]
vol_annual = ind["daily_return"].std() * (252 ** 0.5) * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Latest Close", f"${latest['close']:.2f}")
c2.metric("Technical Signal", latest["signal"])
c3.metric("RSI (14)", f"{latest['rsi14']:.1f}")
c4.metric("Strategy Return", f"{bt['total_return_pct']}%")
c5.metric("Sharpe Ratio", f"{bt['sharpe_ratio']:.2f}")

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📊 Technical Charts", "⚙️ Backtest Metrics", "💼 Portfolio P&L Calculator"])

with tab1:
    st.subheader(f"Technical Analysis for {ticker} (Data Source: {mode})")
    col1, col2 = st.columns(2)
    with col1:
        price_chart = ROOT / "images" / f"{ticker}_price_sma.png"
        if price_chart.exists():
            st.image(str(price_chart), caption=f"{ticker} Price & SMA Crossover", use_container_width=True)
    with col2:
        dist_chart = ROOT / "images" / f"{ticker}_returns_dist.png"
        if dist_chart.exists():
            st.image(str(dist_chart), caption=f"{ticker} Daily Return Distribution", use_container_width=True)

    st.subheader("Latest Technical Indicators (Last 15 Sessions)")
    st.dataframe(ind.tail(15)[["date", "close", "sma20", "sma50", "rsi14", "macd", "bb_upper", "bb_lower", "signal"]], use_container_width=True)

with tab2:
    st.subheader("SMA Crossover Backtest Performance (20-day vs 50-day)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Strategy Return", f"{bt['total_return_pct']}%")
    m2.metric("Sharpe Ratio", f"{bt['sharpe_ratio']}")
    m3.metric("Max Drawdown", f"{bt['max_drawdown_pct']}%")
    m4.metric("Win Rate", f"{bt['win_rate_pct']}%")

with tab3:
    st.subheader("Mark-to-Market Portfolio P&L Simulator")
    sample_trades = [
        {"ticker": ticker, "qty": 100, "avg_cost": round(latest["close"] * 0.95, 2)},
        {"ticker": "MSFT", "qty": 50, "avg_cost": 415.00},
    ]
    latest_prices = {ticker: round(float(latest["close"]), 2), "MSFT": 425.50}
    pnl_df = compute_portfolio_pnl(sample_trades, latest_prices)
    st.dataframe(pnl_df, use_container_width=True)
    st.success(f"Total Unrealized P&L: ${pnl_df['unrealized_pnl'].sum():,.2f}")
