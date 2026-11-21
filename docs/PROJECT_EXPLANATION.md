# Project Explanation: Stock Market Data Analyzer

## 1. What is it?

**Simple explanation.** A tool that downloads a company's share price history and answers the questions an
investor asks: Is it going up or down? How risky is it? How does it compare with other stocks and with the
market? Would a simple trading rule have beaten "buy and hold"? How should money be split across several stocks
to get the best return for the risk? Everything is shown in a dark, trading-style dashboard with candlestick
charts.

**Technical explanation.** A Python quantitative-analysis pipeline. Daily OHLCV data comes from Yahoo Finance
(yfinance), with caching and an offline fallback. It's cleaned with Pandas, and technical indicators (SMA, EMA,
RSI, MACD, Bollinger Bands, ATR, OBV) are implemented from their formulas. The analysis computes CAGR,
annualised volatility, Sharpe and Sortino ratios, drawdowns, historical VaR, and CAPM beta/alpha against the
NIFTY 50. A vectorised backtester tests three strategies with next-day execution and transaction costs. A Monte
Carlo Markowitz simulation finds the max-Sharpe and min-volatility portfolios. Results go to a Streamlit +
Plotly dashboard, a Rich CLI, an Excel report and PNG charts.

### Why it matters

Brokers (Zerodha Kite, Groww), research platforms (TradingView, Screener.in, Bloomberg), fund houses and
fintech start-ups all run these calculations. It's a strong portfolio project for **Data Analyst, Quant/Risk
Analyst, FinTech Developer and Python Developer** roles, because it combines time-series analysis, statistics,
finance concepts and visualisation.

### Workflow

```
choose ticker(s) → download (or cached/sample) prices → clean → indicators → risk & return metrics
   → signals → backtests → portfolio optimisation → charts, dashboard, Excel report
```

## 2. Tech stack options

| Option | Tools | Difficulty | Output |
|---|---|---|---|
| A. Easy | yfinance, Pandas, Matplotlib | Beginner | Price chart + moving average |
| **B. Intermediate** ✅ | yfinance, Pandas, NumPy, Plotly, Streamlit, XlsxWriter, pytest | Intermediate | Indicators, risk metrics, backtests, portfolio optimiser, dashboard |
| C. Advanced | B + backtrader/vectorbt, PostgreSQL/TimescaleDB, live broker API (Kite Connect), ML forecasting | Advanced | Automated trading research platform |

**Chosen: B**, with every indicator and metric written by hand, so each formula can be explained in an interview.

## 3. Architecture

```
  INPUT     Yahoo Finance (yfinance)  ──fails?──►  data/cache/*.csv  ──missing?──►  data/*_sample.csv
                        │
  PROCESSING  data_loader.py   clean: flatten columns, date index, sort, de-duplicate, drop bad rows
              indicators.py    SMA · EMA · RSI · MACD · Bollinger · ATR · OBV
              analysis.py      returns · CAGR · volatility · Sharpe · Sortino · drawdown · VaR · beta/alpha
              signals.py       trend, crossovers, RSI, MACD, Bollinger → Bullish / Bearish / Neutral
              backtest.py      positions → next-day execution → costs → equity curve, trades, metrics
              portfolio.py     4,000 random weight vectors → efficient frontier → best portfolios
                        │
  OUTPUT    app.py (Streamlit dashboard) · main.py (CLI) · report.py (Excel) · charts.py (PNG)
```

### Key formulas

| Metric | Formula | Meaning |
|---|---|---|
| Daily return | Pₜ / Pₜ₋₁ − 1 | % change per day |
| CAGR | (P_end / P_start)^(1/years) − 1 | steady yearly growth rate |
| Volatility | std(daily returns) × √252 | annual risk |
| Sharpe | mean(excess return) / std × √252 | return per unit of risk (risk-free 6.5%) |
| Sortino | like Sharpe, using only downside deviation | penalises only losses |
| Max drawdown | min(P / running max(P) − 1) | worst peak-to-trough fall |
| VaR 95% | −5th percentile of daily returns | "on 95% of days we lose less than this" |
| Beta | cov(stock, market) / var(market) | sensitivity to the market |
| RSI | 100 − 100/(1 + avg gain/avg loss), Wilder smoothing | momentum, 0–100 |
| MACD | EMA12 − EMA26; signal = EMA9 of MACD | trend momentum |

### Avoiding common backtesting mistakes

* **Look-ahead bias:** positions are shifted by one day, so a signal from today's close is traded tomorrow.
  A unit test proves the strategy can't profit from the price jump that created its signal.
* **Ignoring costs:** every buy and every sell pays 10 bps (adjustable).
* **Overfitting:** the dashboard sliders show how results change with parameters; a strategy that only works
  for one exact setting is not robust.

## 4. Implementation plan

| Phase | What | Why | Output | Common mistakes |
|---|---|---|---|---|
| 1. Setup | venv + requirements | Reproducible | Libraries | Old yfinance version |
| 2. Folders | data, src, outputs, images, docs, tests | Organisation | Tree | Notebook-only code |
| 3. Data | yfinance + cache + sample fallback | Works online and offline | Clean OHLCV | MultiIndex columns from yfinance |
| 4. Indicators | formulas in Pandas | Understand, not just call | Indicator columns | Using adjust=True EMA for RSI |
| 5. Metrics | returns, risk, CAPM | Quantify risk/return | Summary table | Forgetting √252 annualisation |
| 6. Signals | rule-based verdicts | Readable interpretation | Signal cards | Presenting as advice |
| 7. Backtest | positions, costs, next-day | Test ideas on history | Equity curve | Look-ahead bias |
| 8. Portfolio | Monte Carlo frontier | Diversification | Optimal weights | Weights not summing to 1 |
| 9. Visualise | Plotly candlesticks, subplots | Insight at a glance | Dashboard | Weekend gaps on x-axis |
| 10. Report | Excel with charts | Shareable | .xlsx | Hard-coded paths |
| 11. GitHub | push + screenshots | Proof of work | Repo | Committing cache files |

## 8. Virtual simulation

1. **Online (your PC):** `python main.py analyze RELIANCE.NS` downloads real prices from Yahoo Finance. Any
   ticker works: `AAPL`, `TSLA`, `ITC.NS`, `^NSEI`.
2. **Offline:** `scripts/generate_sample_data.py` creates two years of **simulated** prices for the NIFTY 50
   and five stocks, using geometric Brownian motion with market regimes (bull run, correction, recovery). Each
   stock = beta × market move + its own noise, so stocks are correlated like real ones. These are clearly
   labelled as simulated everywhere they appear.
3. **Validation:** the analysis recovers the betas used in the simulation (TCS ≈ 0.74, TATAMOTORS ≈ 1.24),
   which shows the beta calculation is correct.

Note: the sample outputs and screenshots in this repository were produced from the simulated data, because the
build environment had no internet access. Run the commands on your own computer to get real-market results.

## 12. Proof-building plan

| Day | Work | Commit message | Screenshot |
|---|---|---|---|
| 1 | Setup, data loader, sample data | `chore: project setup with data loader and offline samples` | Folder, CSV |
| 2 | Indicators | `feat: technical indicators from scratch` | Technical chart |
| 3 | Risk metrics + signals | `feat: risk/return metrics, CAPM beta and signals` | `analyze` output |
| 4 | Backtester + portfolio | `feat: backtester and portfolio optimiser` | Equity curve, frontier |
| 5 | Dashboard | `feat: Streamlit trading dashboard` | Each tab |
| 6 | Tests + docs | `docs: README, explanation, interview Q&A` | pytest, GitHub |

## 13. Screenshot checklist

- [ ] `python main.py analyze RELIANCE.NS` (with live data on your PC)
- [ ] `python main.py compare` and `python main.py portfolio`
- [ ] Dashboard: Chart & signals, Risk & return, Backtest, Portfolio optimizer
- [ ] Excel report opened
- [ ] pytest passing
- [ ] GitHub repository page
