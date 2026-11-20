# Stock Market Data Analyzer & Strategy Backtester

A quantitative finance application that ingests equity OHLCV historical time-series (via `yfinance` or realistic offline synthetic simulation), computes essential technical indicators (SMA20, SMA50, RSI14, MACD, Bollinger Bands, ATR), executes vectorized strategy backtests with fee modeling, and serves charts via FastAPI and Streamlit.

---

## ⚠️ Disclaimer
*This repository is created exclusively for academic, educational, and portfolio demonstration purposes. None of the indicators, models, or signals generated constitute financial or investment advice.*

---

## 🏛 Architecture & Quantitative Pipeline

```
[Equity Ticker Input: AAPL / MSFT / GOOGL]
                    │
                    ▼
 [Market Ingestion: yfinance API / Offline Fallback]
                    │
                    ▼
   [SQLite Time-Series Storage: candles_daily]
                    │
                    ▼
  [Technical Analysis Engine: TA & Rolling Math]
     ├── Trend: SMA 20, SMA 50
     ├── Momentum: RSI 14, MACD (12, 26, 9)
     └── Volatility: Bollinger Bands (20, 2), ATR
                    │
                    ▼
[Vectorized Strategy Backtester] (SMA Crossover with BPS Fee Drag)
                    │
                    ▼
[Outputs: Performance Metrics + Matplotlib Charts + FastAPI & Streamlit]
```

---

## ✨ Key Capabilities

- **Resilient Data Ingestion:** Tries live market feeds via `yfinance` first; if offline or rate-limited, smoothly falls back to a deterministic synthetic geometric Brownian motion simulation.
- **Comprehensive Technical Suite:** Calculates 20-day & 50-day Simple Moving Averages, 14-day Relative Strength Index (RSI), MACD line & signal, Bollinger Bands, and Average True Range (ATR).
- **Vectorized Backtesting Engine:** Evaluates a long-only SMA Golden Cross / Death Cross strategy against historical closes with configurable broker commission drag (basis points).
- **Risk & Performance Metrics:** Generates Total Return (%), Sharpe Ratio (annualized), Maximum Drawdown (%), and Win Rate (%).
- **Mark-to-Market Portfolio P&L:** Models active positions, weighted cost basis, and unrealized profit/loss.
- **RESTful Endpoints:** FastAPI endpoints for price charts (`/chart/{ticker}`), backtests (`/backtest/sma`), and portfolio evaluations (`/portfolio/pnl`).

---

## 🚀 Quick Start Guide

### 1. Installation
```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Run Main Analysis Pipeline
```bash
python main.py
```

### 3. Launch Quantitative Dashboard
```bash
python -m streamlit run app_streamlit.py
```

### 4. Start FastAPI Service
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Test Suite
```bash
python -m unittest discover -s tests -v
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status. |
| `GET` | `/chart/{ticker}` | Returns OHLCV candles, technical indicators, and signal history. |
| `POST` | `/backtest/sma` | Runs vectorized SMA crossover backtest with specified fee drag. |
| `POST` | `/portfolio/pnl` | Calculates mark-to-market positions and unrealized profit & loss. |
