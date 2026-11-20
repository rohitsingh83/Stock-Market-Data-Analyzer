# Engineering Audit: Stock Market Data Analyzer

**Project Context:**
- **What it does / who it's for:** A quantitative finance pipeline that ingests equity OHLCV historical time-series (via `yfinance` or synthetic geometric Brownian motion), computes technical indicators (SMA, RSI, MACD, Bollinger Bands, ATR), executes a vectorized SMA crossover backtest with fee modeling, and serves charts via FastAPI and Streamlit.
- **Stack & entry points:** Python 3.14 / 3.11, `yfinance`, `pandas`, `numpy`, `sqlite3`, `matplotlib`, `fastapi`, `streamlit`. Entry points: `python main.py`, `python jobs/alerts.py`, `python -m uvicorn api.app:app`, `python -m streamlit run app_streamlit.py`.
- **Real usage:** Quantitative backtester & research pipeline (`main.py`) + technical alerting cron job (`jobs/alerts.py`) + REST API (`api/app.py`).
- **Constraint:** Preserve `main.py` CLI interface, `data/AAPL_daily.csv` schema, backtesting metric dictionary keys, and chart filenames.

---

## Findings & Technical Debt

### 🔴 Critical Findings
1. **Execution Timing Mismatch in Vectorized Backtesting (`src/backtest.py`):**
   - While `bt["position"] = ...shift(1)` correctly avoids lookahead bias for signal generation, the strategy return calculation `bt["position"] * bt["daily_return"] - fee_drag` calculates return using close-to-close returns. If a golden cross occurs at Day $T$'s close, the trader cannot enter at Day $T$'s close; they must enter at Day $T+1$'s Open. Using close-to-close returns introduces execution slippage inaccuracies.
2. **Simplified Sharpe Ratio Formulation with Zero Risk-Free Rate Assumption (`src/backtest.py`):**
   - `sharpe = (mean / std * np.sqrt(252))` assumes a $0.0\%$ annual risk-free rate. In standard quantitative finance, Sharpe ratio requires subtracting $R_f$ (e.g. 4.0% annualized Treasury yield) from excess returns before scaling.
3. **Hardcoded Analysis Ticker & Parameters (`main.py`):**
   - `main.py` hardcodes `AAPL`, `fee_bps=10.0`, and `use_live=False` without a dynamic CLI argument parser (`argparse` or `click`).

### 🟡 High Priority Findings
4. **No Slippage Modeling in Backtesting:**
   - Only accounts for explicit basis point fee drag (`fee_bps`), ignoring execution slippage, volume participation rate, and market impact on rebalances.
5. **Inefficient Indicator Computation Without Polars or Vectorized Caching (`src/indicators.py`):**
   - Sequential `.rolling()` and `.ewm()` operations on Pandas DataFrames can become a performance bottleneck when scanning universes of 500+ equities across 10 years of intraday candles.
6. **No Run Manifest or Backtest Audit Trail:**
   - `AAPL_indicators.csv` is overwritten on every run without saving the exact parameters (fast window, slow window, fee bps, data start/end dates, commit hash).

### 🟢 Nice-to-Have / Polish
7. **Single-Ticker Focus in CLI:**
   - Running `main.py` executes only for AAPL; should support `--ticker` flag and `--universe` batch scans.
8. **Missing Benchmark Performance Comparison:**
   - Backtest results report strategy return, but lack automated side-by-side benchmark comparison against Buy & Hold SPY / underlying asset.

---

## What "Elite" Looks Like for This Exact Project

An elite quantitative backtesting engine:
- Accurately models signal generation on Close with execution on Next Open, including both transaction commission and bid-ask slippage.
- Computes annualized Sharpe with configurable risk-free rate, Sortino ratio, Calmar ratio, and maximum drawdown duration.
- Evaluates strategy performance against Buy & Hold benchmark with alpha and beta metrics.
- Provides a clean CLI with `--ticker`, `--start`, `--end`, `--fast-ma`, `--slow-ma`, and `--fee-bps` flags.
- Employs a run manifest recording data fingerprint, backtest parameters, and reproducible performance outputs.
