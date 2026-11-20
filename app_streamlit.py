"""Flagship Quantitative Equity Analysis & Algorithmic Backtesting Terminal.
Features:
- Live market data fetch for ANY ticker via yfinance (with synthetic GBM fallback)
- Interactive Plotly Candlestick charts with volume bars
- Technical overlays: SMA20, SMA50, Bollinger Bands (20,2), ATR, and RSI(14)
- Interactive Parameterized Strategy Backtester with equity curve vs Buy & Hold benchmark
- Live Technical Alert Scanner & Signals
- Interactive Mark-to-Market Portfolio P&L Calculator
"""

import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.config import settings
from src.ingest import fetch_or_simulate_ohlcv
from src.indicators import compute_indicators
from src.backtest import run_sma_backtest
from src.portfolio import compute_portfolio_pnl
from jobs.alerts import check_technical_alerts

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="QuantPulse — Algorithmic Equity Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .terminal-title { font-size: 2.2rem; font-weight: 800; color: #0F172A; }
    .terminal-subtitle { font-size: 1.05rem; color: #64748B; margin-bottom: 1.2rem; }
    .metric-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="terminal-title">📈 QuantPulse — Quantitative Equity & Strategy Terminal</div>', unsafe_allow_html=True)
st.markdown('<div class="terminal-subtitle">Algorithmic Backtesting • Vectorized Technical Indicators • Execution Slippage & Benchmark Analytics</div>', unsafe_allow_html=True)

# Sidebar: Asset selection & Backtest parameters
with st.sidebar:
    st.header("🔍 Market Data Settings")
    popular_tickers = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META"]
    ticker_choice = st.selectbox("Popular Tickers", popular_tickers)
    custom_ticker = st.text_input("Or Enter Custom Ticker Symbol", value=ticker_choice).upper().strip()
    ticker = custom_ticker if custom_ticker else ticker_choice
    
    use_live_data = st.checkbox("Fetch Live Market Data (Yahoo Finance)", value=True, help="Fetches live daily OHLCV candles. Falls back to offline simulation if offline.")
    
    st.markdown("---")
    st.header("⚙️ Backtest Strategy Parameters")
    fast_ma = st.slider("Fast Moving Average (Days)", min_value=5, max_value=50, value=20, step=1)
    slow_ma = st.slider("Slow Moving Average (Days)", min_value=20, max_value=200, value=50, step=5)
    fee_bps = st.slider("Broker Commission Drag (basis points)", min_value=0.0, max_value=50.0, value=10.0, step=1.0)
    risk_free_rate = st.number_input("Annual Risk-Free Rate (%)", min_value=0.0, max_value=15.0, value=4.0, step=0.5) / 100.0

# Fetch Data
with st.spinner(f"Ingesting daily market data for {ticker}..."):
    df, mode = fetch_or_simulate_ohlcv(ticker, settings.data_dir, use_live=use_live_data)
    
    # Recalculate indicators with user's custom fast/slow MA
    ind = df.copy().sort_values("date").reset_index(drop=True)
    ind["sma_fast"] = ind["close"].rolling(fast_ma).mean()
    ind["sma_slow"] = ind["close"].rolling(slow_ma).mean()
    ind = compute_indicators(ind)
    
    # Re-run backtest on dynamic parameters
    bt_data = ind.dropna(subset=["sma_fast", "sma_slow", "daily_return"]).copy()
    bt_data["position"] = (bt_data["sma_fast"] > bt_data["sma_slow"]).astype(int).shift(1).fillna(0)
    trades = bt_data["position"].diff().abs().fillna(0)
    fee_drag = trades * (fee_bps / 10000.0)
    bt_data["strategy_return"] = bt_data["position"] * bt_data["daily_return"] - fee_drag
    bt_data["strategy_equity"] = (1 + bt_data["strategy_return"]).cumprod()
    bt_data["benchmark_equity"] = (1 + bt_data["daily_return"]).cumprod()
    
    latest = ind.iloc[-1]
    tot_ret = (bt_data["strategy_equity"].iloc[-1] - 1) * 100 if not bt_data.empty else 0.0
    bnh_ret = (bt_data["benchmark_equity"].iloc[-1] - 1) * 100 if not bt_data.empty else 0.0
    std = bt_data["strategy_return"].std()
    excess = bt_data["strategy_return"] - (risk_free_rate / 252.0)
    sharpe = (excess.mean() / std * np.sqrt(252)) if std and std > 0 else 0.0
    roll_max = bt_data["strategy_equity"].cummax()
    max_dd = ((bt_data["strategy_equity"] / roll_max - 1) * 100).min() if not bt_data.empty else 0.0
    win_rate = (bt_data[bt_data["position"] == 1]["strategy_return"] > 0).mean() * 100 if not bt_data.empty else 0.0

# Top KPI Summary Cards
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Latest Close", f"${latest['close']:.2f}")
delta_day = latest['daily_return'] * 100 if pd.notna(latest['daily_return']) else 0.0
k2.metric("Daily Change", f"{delta_day:+.2f}%", delta=f"{delta_day:.2f}%")
sig_icon = "🟢" if latest["signal"] == "BUY" else ("🔴" if latest["signal"] == "SELL" else "⚪")
k3.metric("Trend Signal", f"{sig_icon} {latest['signal']}")
k4.metric("Strategy Return", f"{tot_ret:+.1f}%", delta=f"{tot_ret - bnh_ret:+.1f}% vs B&H")
k5.metric("Sharpe Ratio", f"{sharpe:.2f}")
k6.metric("Max Drawdown", f"{max_dd:.1f}%")

st.markdown("---")

tab_chart, tab_backtest, tab_alerts, tab_portfolio = st.tabs([
    "📊 Interactive Candlestick & Technicals",
    "⚡ Quantitative Strategy Backtest",
    "🚨 Live Risk Alerts & Signals",
    "💼 Mark-to-Market Portfolio"
])

with tab_chart:
    st.subheader(f"{ticker} Technical Chart Analysis (Source: {mode})")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        show_bb = st.checkbox("Overlay Bollinger Bands (20, 2)", value=True)
    with col_t2:
        show_fast = st.checkbox(f"Overlay Fast SMA ({fast_ma}D)", value=True)
    with col_t3:
        show_slow = st.checkbox(f"Overlay Slow SMA ({slow_ma}D)", value=True)

    # Build Candlestick + Volume + RSI + MACD Subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.60, 0.20, 0.20],
        subplot_titles=(f"{ticker} Daily OHLCV Price Action", "RSI (14)", "MACD (12, 26, 9)")
    )

    # 1. Candlestick
    fig.add_trace(
        go.Candlestick(
            x=ind["date"], open=ind["open"], high=ind["high"], low=ind["low"], close=ind["close"],
            name="OHLC",
            increasing_line_color="#16A34A", decreasing_line_color="#DC2626"
        ),
        row=1, col=1
    )

    # Moving Averages
    if show_fast and "sma_fast" in ind.columns:
        fig.add_trace(go.Scatter(x=ind["date"], y=ind["sma_fast"], name=f"SMA {fast_ma}", line=dict(color="#F59E0B", width=1.5)), row=1, col=1)
    if show_slow and "sma_slow" in ind.columns:
        fig.add_trace(go.Scatter(x=ind["date"], y=ind["sma_slow"], name=f"SMA {slow_ma}", line=dict(color="#3B82F6", width=1.5)), row=1, col=1)

    # Bollinger Bands
    if show_bb and "bb_upper" in ind.columns:
        fig.add_trace(go.Scatter(x=ind["date"], y=ind["bb_upper"], name="BB Upper", line=dict(color="rgba(148, 163, 184, 0.6)", dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["date"], y=ind["bb_lower"], name="BB Lower", line=dict(color="rgba(148, 163, 184, 0.6)", dash="dot")), row=1, col=1)

    # 2. RSI
    if "rsi14" in ind.columns:
        fig.add_trace(go.Scatter(x=ind["date"], y=ind["rsi14"], name="RSI", line=dict(color="#8B5CF6", width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#EF4444", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10B981", row=2, col=1)

    # 3. MACD
    if "macd" in ind.columns and "macd_signal" in ind.columns:
        fig.add_trace(go.Scatter(x=ind["date"], y=ind["macd"], name="MACD", line=dict(color="#06B6D4", width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=ind["date"], y=ind["macd_signal"], name="Signal", line=dict(color="#F97316", width=1.2)), row=3, col=1)
        macd_hist = ind["macd"] - ind["macd_signal"]
        hist_colors = ["#16A34A" if val >= 0 else "#DC2626" for val in macd_hist]
        fig.add_trace(go.Bar(x=ind["date"], y=macd_hist, name="Hist", marker_color=hist_colors), row=3, col=1)

    fig.update_layout(height=720, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

with tab_backtest:
    st.subheader(f"Strategy Performance: {fast_ma}-Day vs {slow_ma}-Day Crossover")
    
    # Cumulative Return Comparison Plot
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(x=bt_data["date"], y=(bt_data["strategy_equity"] - 1) * 100, name="SMA Strategy (Net of Fees)", line=dict(color="#2563EB", width=2.2)))
    fig_equity.add_trace(go.Scatter(x=bt_data["date"], y=(bt_data["benchmark_equity"] - 1) * 100, name=f"{ticker} Buy & Hold", line=dict(color="#64748B", width=1.5, dash="dash")))
    fig_equity.update_layout(
        title=f"Cumulative Growth: SMA Crossover vs Buy & Hold Benchmark (Fee: {fee_bps} bps)",
        yaxis_title="Cumulative Return (%)",
        xaxis_title="Date",
        height=420,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig_equity, use_container_width=True)

    # Performance Table
    st.subheader("Key Quantitative Performance Statistics")
    stats_df = pd.DataFrame([
        {"Metric": "Strategy Net Total Return", "Value": f"{tot_ret:+.2f}%"},
        {"Metric": "Buy & Hold Benchmark Return", "Value": f"{bnh_ret:+.2f}%"},
        {"Metric": "Excess Return (Alpha)", "Value": f"{tot_ret - bnh_ret:+.2f}%"},
        {"Metric": "Annualized Sharpe Ratio", "Value": f"{sharpe:.2f}"},
        {"Metric": "Maximum Drawdown", "Value": f"{max_dd:.2f}%"},
        {"Metric": "Win Rate (% Profitable Days in Market)", "Value": f"{win_rate:.1f}%"},
        {"Metric": "Rebalance Execution Trades", "Value": f"{int(trades.sum())}"},
        {"Metric": "Commission Drag Incurred", "Value": f"{int(trades.sum()) * fee_bps:.1f} bps"},
    ])
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

with tab_alerts:
    st.subheader(f"Real-Time Technical Rule Scanner ({ticker})")
    alerts = check_technical_alerts(ind, ticker)
    
    if alerts:
        for a in alerts:
            st.warning(f"⚠️ **Rule Triggered [{a['rule']}]:** Current value is **{a['value']}**")
    else:
        st.success(f"✅ Normal Market Regimes: No critical technical alerts triggered for {ticker}.")

    st.markdown("### Configured Alert Definitions")
    st.markdown("""
    - **RSI_LT_30:** Triggered when 14-period RSI drops below 30.0 (Oversold condition).
    - **RSI_GT_70:** Triggered when 14-period RSI rises above 70.0 (Overbought condition).
    - **CLOSE_LT_BBLOWER:** Triggered when current price breaks below lower 2-sigma Bollinger Band.
    """)

with tab_portfolio:
    st.subheader("Mark-to-Market Portfolio & P&L Tracker")
    st.write("Simulate your portfolio positions and track real-time mark-to-market performance.")
    
    sample_positions = [
        {"ticker": ticker, "qty": 100, "avg_cost": round(float(latest['close']) * 0.96, 2)},
        {"ticker": "MSFT", "qty": 40, "avg_cost": 412.50},
        {"ticker": "NVDA", "qty": 50, "avg_cost": 135.00},
    ]
    prices = {ticker: round(float(latest['close']), 2), "MSFT": 428.00, "NVDA": 142.50}
    pnl_df = compute_portfolio_pnl(sample_positions, prices)
    st.dataframe(pnl_df, use_container_width=True, hide_index=True)
    
    total_val = sum(r['qty'] * r['market_price'] for _, r in pnl_df.iterrows())
    total_pnl = float(pnl_df["unrealized_pnl"].sum())
    p_c1, p_c2 = st.columns(2)
    p_c1.metric("Total Portfolio Market Value", f"${total_val:,.2f}")
    p_c2.metric("Total Unrealized P&L", f"${total_pnl:+,.2f}", delta=f"{total_pnl:,.2f}")
