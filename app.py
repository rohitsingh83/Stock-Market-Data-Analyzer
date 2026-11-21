"""
Stock Market Data Analyzer dashboard.

Run:  streamlit run app.py
"""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.analysis import compare, correlation, drawdown, normalised, performance_summary
from src.backtest import STRATEGIES, run_backtest
from src.data_loader import INDEX, WATCHLIST, close_matrix, load_prices
from src.indicators import add_indicators
from src.portfolio import best_portfolios, simulate_portfolios
from src.report import excel_report
from src.signals import overall_view, signal_snapshot

st.set_page_config(page_title="Stock Market Analyzer", page_icon="📈", layout="wide")
TEMPLATE = "plotly_dark"
GREEN, RED, BLUE, AMBER = "#22C55E", "#EF4444", "#3B82F6", "#F59E0B"
VERDICT_COLOUR = {"Bullish": GREEN, "Bearish": RED, "Neutral": AMBER}

st.markdown("""
<style>
.block-container {padding-top: 1.6rem;}
.hero {background: linear-gradient(120deg, #0F172A 0%, #14532D 60%, #22C55E 130%); border: 1px solid #1E293B;
       padding: 1.3rem 1.8rem; border-radius: 16px; margin-bottom: 1.1rem;}
.hero h1 {margin: 0; font-size: 2rem; color: white;}
.hero p {margin: .3rem 0 0 0; color: #CBD5E1;}
.kpi {background: #111A2E; border: 1px solid #1E293B; border-radius: 14px; padding: .9rem 1.1rem;}
.kpi .label {color: #94A3B8; font-size: .78rem; text-transform: uppercase; letter-spacing: .05em;}
.kpi .value {font-size: 1.7rem; font-weight: 700; color: #F8FAFC;}
.kpi .up {color: #22C55E; font-size: .85rem;} .kpi .down {color: #EF4444; font-size: .85rem;}
.sig {background: #111A2E; border-left: 5px solid; border-radius: 10px; padding: .6rem .9rem; margin-bottom: .5rem;}
.sig .small {color: #94A3B8; font-size: .82rem;}
.banner {background: #422006; color: #FDE68A; border-radius: 10px; padding: .5rem .9rem; margin-bottom: .8rem;}
</style>
""", unsafe_allow_html=True)


def kpi(col, label, value, change=None):
    ch = ""
    if change is not None:
        ch = f'<div class="{"up" if change >= 0 else "down"}">{"▲" if change >= 0 else "▼"} {abs(change):.2%}</div>'
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>{ch}</div>',
                 unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner="Loading prices...")
def get_prices(ticker: str, start: date, end: date, source: str):
    d = load_prices(ticker, start, end, source)
    return d.df, d.source


with st.sidebar:
    st.header("📈 Settings")
    ticker = st.selectbox("Stock", WATCHLIST, format_func=lambda t: t.replace(".NS", ""))
    custom = st.text_input("…or any Yahoo Finance ticker", placeholder="e.g. AAPL, TSLA, ITC.NS")
    if custom.strip():
        ticker = custom.strip().upper()
    period = st.select_slider("Period", ["6M", "1Y", "2Y"], value="2Y")
    days = {"6M": 182, "1Y": 365, "2Y": 730}[period]
    end = date(2026, 11, 20) if date.today() < date(2026, 11, 20) else date.today()
    start = end - timedelta(days=days)
    source = st.radio("Data source", ["auto", "live", "sample"], horizontal=True,
                      help="auto = real Yahoo Finance data, falls back to bundled sample data when offline")
    st.caption("Educational project, not investment advice.")

try:
    # extra history so the 200-day average is already available on the first visible day
    df_raw, used = get_prices(ticker, start - timedelta(days=300), end, source)
    idx_raw, _ = get_prices(INDEX, start, end, source)
except Exception as exc:
    st.error(f"Could not load {ticker}: {exc}")
    st.stop()

df = add_indicators(df_raw)
view = df.loc[str(start):]
summary = performance_summary(view["Close"], idx_raw["Close"])
last, prev = view.iloc[-1], view.iloc[-2]

st.markdown(f'<div class="hero"><h1>📈 Stock Market Data Analyzer</h1><p>{ticker} · {view.index[0]:%d %b %Y} → '
            f'{view.index[-1]:%d %b %Y} · {len(view)} trading days</p></div>', unsafe_allow_html=True)
if used == "sample":
    st.markdown('<div class="banner">⚠️ Offline mode: showing bundled <b>simulated</b> sample prices, not real market '
                'data. Run on a computer with internet for live Yahoo Finance data.</div>', unsafe_allow_html=True)

k = st.columns(5)
kpi(k[0], "Last close", f"{last['Close']:,.2f}", last["Close"] / prev["Close"] - 1)
kpi(k[1], f"{period} return", f"{summary['Total return']:.1%}")
kpi(k[2], "Volatility", f"{summary['Volatility']:.1%}")
kpi(k[3], "Sharpe ratio", f"{summary['Sharpe']:.2f}")
kpi(k[4], "Max drawdown", f"{summary['Max drawdown']:.1%}")
st.write("")

tab_chart, tab_perf, tab_compare, tab_bt, tab_port = st.tabs(
    ["🕯️ Chart & signals", "📊 Risk & return", "🔀 Compare", "🧪 Backtest", "🥧 Portfolio optimizer"])

# ------------------------------------------------------------------ chart
with tab_chart:
    c_left, c_right = st.columns([3, 1])
    with c_left:
        overlays = st.multiselect("Overlays", ["SMA20", "SMA50", "SMA200", "EMA20", "Bollinger bands"],
                                  default=["SMA50", "SMA200", "Bollinger bands"])
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                            row_heights=[0.55, 0.15, 0.15, 0.15])
        fig.add_trace(go.Candlestick(x=view.index, open=view["Open"], high=view["High"], low=view["Low"],
                                     close=view["Close"], name="Price", increasing_line_color=GREEN,
                                     decreasing_line_color=RED), 1, 1)
        colours = {"SMA20": "#A78BFA", "SMA50": BLUE, "SMA200": AMBER, "EMA20": "#F472B6"}
        for o in overlays:
            if o == "Bollinger bands":
                fig.add_trace(go.Scatter(x=view.index, y=view["BB_upper"], line=dict(width=0.8, color="#64748B"),
                                         name="BB upper"), 1, 1)
                fig.add_trace(go.Scatter(x=view.index, y=view["BB_lower"], line=dict(width=0.8, color="#64748B"),
                                         fill="tonexty", fillcolor="rgba(100,116,139,0.12)", name="BB lower"), 1, 1)
            else:
                fig.add_trace(go.Scatter(x=view.index, y=view[o], line=dict(width=1.3, color=colours[o]), name=o), 1, 1)
        fig.add_trace(go.Bar(x=view.index, y=view["Volume"], name="Volume", marker_color=[
            GREEN if c >= o else RED for c, o in zip(view["Close"], view["Open"])]), 2, 1)
        fig.add_trace(go.Scatter(x=view.index, y=view["RSI14"], name="RSI 14", line=dict(color="#A78BFA")), 3, 1)
        fig.add_hline(70, line_dash="dash", line_color=RED, row=3, col=1)
        fig.add_hline(30, line_dash="dash", line_color=GREEN, row=3, col=1)
        fig.add_trace(go.Bar(x=view.index, y=view["MACD_hist"], name="MACD hist",
                             marker_color=[GREEN if h >= 0 else RED for h in view["MACD_hist"]]), 4, 1)
        fig.add_trace(go.Scatter(x=view.index, y=view["MACD"], name="MACD", line=dict(color=BLUE, width=1)), 4, 1)
        fig.add_trace(go.Scatter(x=view.index, y=view["MACD_signal"], name="Signal", line=dict(color=AMBER, width=1)), 4, 1)
        fig.update_layout(template=TEMPLATE, height=760, xaxis_rangeslider_visible=False, showlegend=False,
                          margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
        for i, label in enumerate(["Price", "Volume", "RSI", "MACD"], start=1):
            fig.update_yaxes(title_text=label, row=i, col=1)
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
        st.plotly_chart(fig, width="stretch")
    with c_right:
        sigs = signal_snapshot(df)
        st.markdown(f"#### Signals: {overall_view(sigs)}")
        for s in sigs:
            st.markdown(f'<div class="sig" style="border-color:{VERDICT_COLOUR[s.verdict]}"><b>{s.indicator}</b> · '
                        f'<span style="color:{VERDICT_COLOUR[s.verdict]}">{s.verdict}</span><br>{s.reading}'
                        f'<div class="small">{s.explanation}</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ performance
with tab_perf:
    p1, p2 = st.columns([1, 2])
    pct_keys = {"Total return", "CAGR", "Volatility", "Max drawdown", "VaR 95% (1 day)", "Best day", "Worst day",
                "Positive days", "Alpha"}
    table = pd.DataFrame({"Metric": summary.keys(),
                          "Value": [f"{v:.2%}" if k in pct_keys else f"{v:,.2f}" for k, v in summary.items()]})
    p1.dataframe(table, hide_index=True, width="stretch", height=530)
    with p2:
        dd = drawdown(view["Close"]) * 100
        ddf = go.Figure(go.Scatter(x=dd.index, y=dd, fill="tozeroy", line=dict(color=RED), name="Drawdown"))
        ddf.update_layout(template=TEMPLATE, title="Drawdown: % below the previous peak", height=260,
                          margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(ddf, width="stretch")
        rets = view["Return"].dropna() * 100
        hist = px.histogram(rets, nbins=60, title="Distribution of daily returns (%)", template=TEMPLATE,
                            color_discrete_sequence=[BLUE])
        hist.add_vline(-summary["VaR 95% (1 day)"] * 100, line_dash="dash", line_color=RED,
                       annotation_text="VaR 95%")
        hist.update_layout(showlegend=False, height=260, margin=dict(l=10, r=10, t=50, b=10),
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(hist, width="stretch")
        monthly = view["Close"].resample("ME").last().pct_change().dropna()
        mdf = pd.DataFrame({"year": monthly.index.year, "month": monthly.index.strftime("%b"), "ret": monthly * 100})
        heat = px.imshow(mdf.pivot(index="year", columns="month", values="ret")
                         .reindex(columns=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]),
                         color_continuous_scale="RdYlGn", color_continuous_midpoint=0, text_auto=".1f", aspect="auto",
                         title="Monthly returns (%)", template=TEMPLATE)
        heat.update_layout(height=230, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(heat, width="stretch")

# ------------------------------------------------------------------ compare
with tab_compare:
    picks = st.multiselect("Compare", WATCHLIST + [INDEX], default=WATCHLIST + [INDEX],
                           format_func=lambda t: "NIFTY 50" if t == INDEX else t.replace(".NS", ""))
    if len(picks) >= 2:
        closes = close_matrix({t: type("D", (), {"df": get_prices(t, start, end, source)[0]})() for t in picks})
        closes = closes.loc[str(start):]
        norm = normalised(closes).rename(columns=lambda c: "NIFTY 50" if c == INDEX else c.replace(".NS", ""))
        line = px.line(norm, title="Growth of ₹100 invested at the start", template=TEMPLATE)
        line.update_layout(height=400, legend_title=None, margin=dict(l=10, r=10, t=50, b=10),
                           paper_bgcolor="rgba(0,0,0,0)", yaxis_title="Value (₹)")
        st.plotly_chart(line, width="stretch")
        cc1, cc2 = st.columns([1, 1])
        corr = correlation(closes).rename(index=lambda c: c.replace(".NS", "").replace("^NSEI", "NIFTY"),
                                          columns=lambda c: c.replace(".NS", "").replace("^NSEI", "NIFTY"))
        cmap = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdYlGn", zmin=-1, zmax=1,
                         title="Correlation of daily returns", template=TEMPLATE)
        cmap.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
        cc1.plotly_chart(cmap, width="stretch")
        comp = compare(closes, idx_raw["Close"])
        rr = px.scatter(comp.reset_index(names="Ticker"), x="Volatility", y="CAGR", text="Ticker", size=[18] * len(comp),
                        color="Sharpe", color_continuous_scale="RdYlGn", title="Risk vs return", template=TEMPLATE)
        rr.update_traces(textposition="top center")
        rr.update_layout(height=420, xaxis_tickformat=".0%", yaxis_tickformat=".0%", margin=dict(l=10, r=10, t=50, b=10),
                         paper_bgcolor="rgba(0,0,0,0)")
        cc2.plotly_chart(rr, width="stretch")
        show = comp[["Total return", "CAGR", "Volatility", "Sharpe", "Max drawdown", "Beta"]]
        st.dataframe(show.style.format({c: "{:.2%}" for c in ["Total return", "CAGR", "Volatility", "Max drawdown"]}
                                       | {"Sharpe": "{:.2f}", "Beta": "{:.2f}"}), width="stretch")

# ------------------------------------------------------------------ backtest
with tab_bt:
    b1, b2 = st.columns([1, 3])
    with b1:
        strategy = st.selectbox("Strategy", list(STRATEGIES))
        st.caption(STRATEGIES[strategy])
        params = {}
        if strategy == "SMA crossover":
            params["fast"] = st.slider("Fast SMA", 5, 50, 20)
            params["slow"] = st.slider("Slow SMA", 20, 200, 50)
        elif strategy == "RSI mean reversion":
            params["lower"] = st.slider("Buy below RSI", 10, 45, 30)
            params["upper"] = st.slider("Sell above RSI", 55, 90, 70)
        cost = st.slider("Cost per trade (bps)", 0, 50, 10)
    result = run_backtest(view["Close"], strategy, cost_bps=cost, **params)
    m = result.metrics
    with b2:
        mm = st.columns(4)
        kpi(mm[0], "Strategy return", f"{m['Total return']:.1%}")
        kpi(mm[1], "Buy & hold", f"{m['Buy & hold return']:.1%}")
        kpi(mm[2], "Max drawdown", f"{m['Max drawdown']:.1%}")
        kpi(mm[3], "Trades · win rate", f"{m['Trades']} · {m['Win rate']:.0%}")
        eq = go.Figure()
        eq.add_trace(go.Scatter(x=result.equity.index, y=result.equity["Strategy"] * 100, name=strategy,
                                line=dict(color=GREEN, width=2)))
        eq.add_trace(go.Scatter(x=result.equity.index, y=result.equity["Buy & Hold"] * 100, name="Buy & hold",
                                line=dict(color="#94A3B8")))
        if not result.trades.empty:
            eq.add_trace(go.Scatter(x=result.trades["Entry date"], y=result.equity["Strategy"].reindex(
                result.trades["Entry date"]) * 100, mode="markers", name="Buy", marker=dict(symbol="triangle-up",
                                                                                         size=11, color=GREEN)))
            eq.add_trace(go.Scatter(x=result.trades["Exit date"], y=result.equity["Strategy"].reindex(
                result.trades["Exit date"]) * 100, mode="markers", name="Sell", marker=dict(symbol="triangle-down",
                                                                                         size=11, color=RED)))
        eq.update_layout(template=TEMPLATE, title="Growth of ₹100", height=420, margin=dict(l=10, r=10, t=50, b=10),
                         paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(eq, width="stretch")
    if not result.trades.empty:
        st.dataframe(result.trades.style.format({"Entry price": "{:,.2f}", "Exit price": "{:,.2f}", "Return": "{:.2%}",
                                                 "Entry date": "{:%d %b %Y}", "Exit date": "{:%d %b %Y}"}),
                     hide_index=True, width="stretch")
    st.caption("Signals are traded on the next day's close to avoid look-ahead bias. Past performance does not "
               "guarantee future results.")

# ------------------------------------------------------------------ portfolio
with tab_port:
    closes = close_matrix({t: type("D", (), {"df": get_prices(t, start, end, source)[0]})() for t in WATCHLIST})
    closes = closes.loc[str(start):]
    sim = simulate_portfolios(closes)
    best = best_portfolios(sim)
    f1, f2 = st.columns([2, 1])
    front = px.scatter(sim, x="Volatility", y="Return", color="Sharpe", color_continuous_scale="Viridis", opacity=.6,
                       title="Efficient frontier: 4,000 random portfolios", template=TEMPLATE)
    for name, symbol in [("Max Sharpe", "star"), ("Min volatility", "diamond")]:
        front.add_trace(go.Scatter(x=[best[name]["Volatility"]], y=[best[name]["Return"]], mode="markers+text",
                                   text=[name], textposition="top center", name=name,
                                   marker=dict(symbol=symbol, size=18, color=RED, line=dict(color="white", width=1))))
    front.update_layout(height=470, xaxis_tickformat=".0%", yaxis_tickformat=".0%", showlegend=False,
                        margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
    f1.plotly_chart(front, width="stretch")
    with f2:
        choice = st.radio("Portfolio", list(best), horizontal=True)
        w = best[choice][closes.columns]
        pie = px.pie(names=[c.replace(".NS", "") for c in w.index], values=w.values, hole=.5, template=TEMPLATE,
                     title=f"{choice} weights")
        pie.update_layout(height=330, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(pie, width="stretch")
        st.markdown(f"Expected return **{best[choice]['Return']:.1%}** · risk **{best[choice]['Volatility']:.1%}** · "
                    f"Sharpe **{best[choice]['Sharpe']:.2f}**")
    st.download_button("⬇️ Download full Excel report", excel_report(
        ticker, view, summary, compare(closes, idx_raw["Close"]),
        [run_backtest(view["Close"], s) for s in STRATEGIES]), f"{ticker.replace('.NS', '')}_analysis.xlsx")
