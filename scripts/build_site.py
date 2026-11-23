"""Build the GitHub Pages report: python scripts/build_site.py  -> docs/index.html (uses bundled sample data)"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from site_template import fig_html, page, table_html
from src.analysis import compare, correlation, normalised
from src.backtest import STRATEGIES, run_backtest
from src.data_loader import INDEX, WATCHLIST, close_matrix, load_many, load_prices
from src.indicators import add_indicators
from src.portfolio import best_portfolios, simulate_portfolios
from src.signals import overall_view, signal_snapshot

PCT = ["Total return", "CAGR", "Volatility", "Max drawdown"]


def main() -> None:
    data = load_many(WATCHLIST + [INDEX], source="sample")
    idx = data[INDEX].df["Close"]
    df = add_indicators(data["HDFCBANK.NS"].df)
    v = df.tail(260)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[.6, .2, .2], vertical_spacing=.03)
    fig.add_trace(go.Candlestick(x=v.index, open=v["Open"], high=v["High"], low=v["Low"], close=v["Close"],
                                 name="Price", increasing_line_color="#22C55E", decreasing_line_color="#EF4444"), 1, 1)
    for col, c in [("SMA50", "#3B82F6"), ("SMA200", "#F59E0B")]:
        fig.add_trace(go.Scatter(x=v.index, y=v[col], name=col, line=dict(color=c, width=1.3)), 1, 1)
    fig.add_trace(go.Scatter(x=v.index, y=v["RSI14"], name="RSI", line=dict(color="#A78BFA")), 2, 1)
    fig.add_trace(go.Bar(x=v.index, y=v["MACD_hist"], name="MACD hist",
                         marker_color=["#22C55E" if h >= 0 else "#EF4444" for h in v["MACD_hist"]]), 3, 1)
    fig.update_layout(title="HDFCBANK: candlesticks, moving averages, RSI and MACD (last 12 months)",
                      xaxis_rangeslider_visible=False, showlegend=False)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

    closes = close_matrix({t: d for t, d in data.items() if t != INDEX})
    allc = close_matrix(data)
    norm = normalised(allc).rename(columns=lambda c: "NIFTY 50" if c == INDEX else c.replace(".NS", ""))
    line = px.line(norm, title="Growth of ₹100 invested")
    corr = correlation(allc).rename(index=lambda c: c.replace(".NS", "").replace("^NSEI", "NIFTY"),
                                    columns=lambda c: c.replace(".NS", "").replace("^NSEI", "NIFTY"))
    heat = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdYlGn", zmin=-1, zmax=1,
                     title="Correlation of daily returns")
    table = compare(closes, idx)[PCT + ["Sharpe", "Beta"]].reset_index(names="Ticker")
    for c in PCT:
        table[c] = (table[c] * 100).round(1).astype(str) + "%"
    table[["Sharpe", "Beta"]] = table[["Sharpe", "Beta"]].round(2)

    eq = go.Figure()
    rows = []
    for name in STRATEGIES:
        r = run_backtest(df["Close"], name)
        eq.add_trace(go.Scatter(x=r.equity.index, y=r.equity["Strategy"] * 100, name=name))
        rows.append({"Strategy": name, "Return": f"{r.metrics['Total return']:.1%}",
                     "Max drawdown": f"{r.metrics['Max drawdown']:.1%}", "Sharpe": round(r.metrics["Sharpe"], 2),
                     "Trades": r.metrics["Trades"], "Win rate": f"{r.metrics['Win rate']:.0%}"})
    eq.add_trace(go.Scatter(x=r.equity.index, y=r.equity["Buy & Hold"] * 100, name="Buy & hold",
                            line=dict(color="#94a3b8", dash="dot")))
    eq.update_layout(title="HDFCBANK backtests: growth of ₹100 (0.10% cost per trade, next-day execution)")

    sim = simulate_portfolios(closes)
    best = best_portfolios(sim)
    front = px.scatter(sim, x="Volatility", y="Return", color="Sharpe", color_continuous_scale="Viridis", opacity=.6,
                       title="Efficient frontier (4,000 random portfolios)")
    front.update_layout(xaxis_tickformat=".0%", yaxis_tickformat=".0%")
    weights = pd.DataFrame({n: (best[n][closes.columns] * 100).round(1).astype(str) + "%" for n in best}) \
        .reset_index(names="Ticker")
    sigs = signal_snapshot(df)
    sig_tbl = pd.DataFrame([{"Indicator": s.indicator, "Reading": s.reading, "Verdict": s.verdict} for s in sigs])

    html = page(
        title="Stock Market Data Analyzer",
        tagline="Technical indicators, risk metrics, strategy backtests and portfolio optimisation for NSE stocks.",
        accent="#22C55E", repo="Stock-Market-Data-Analyzer",
        kpis=[("Stocks analysed", "5 + NIFTY 50"), ("Trading days", str(len(df))), ("Strategies backtested", "3"),
              ("Portfolios simulated", "4,000"), ("Automated tests", "14")],
        sections=[
            ("Chart & indicators", f"Overall signal today: {overall_view(sigs)}.",
             fig_html(fig, 640) + table_html(sig_tbl)),
            ("Compare the watchlist", "Risk and return of each stock vs the NIFTY 50.",
             f'<div class="grid2">{fig_html(line, 400)}{fig_html(heat, 400)}</div><div class="scroll">{table_html(table)}</div>'),
            ("Backtests", "Signals are traded the next day to avoid look-ahead bias.", fig_html(eq, 420) + table_html(pd.DataFrame(rows))),
            ("Portfolio optimizer", "Markowitz Monte Carlo simulation.",
             f'<div class="grid2">{fig_html(front, 420)}<div>{table_html(weights)}</div></div>'),
        ],
        note="Prices on this page are SIMULATED sample data bundled for offline use (scripts/generate_sample_data.py). "
             "Run the app on your computer for live Yahoo Finance data. Educational project, not investment advice.",
        run_cmds=["pip install -r requirements.txt", "python main.py analyze RELIANCE.NS", "python main.py compare",
                  "streamlit run app.py"])
    out = ROOT / "docs" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
