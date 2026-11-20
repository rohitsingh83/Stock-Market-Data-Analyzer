"""FastAPI service for Stock Market Data Analyzer."""

from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

from src.ingest import fetch_or_simulate_ohlcv
from src.indicators import compute_indicators
from src.backtest import run_sma_backtest
from src.portfolio import compute_portfolio_pnl

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Stock Market Data Analyzer API", version="1.0.0")


class PortfolioRequest(BaseModel):
    trades: List[Dict[str, Any]]
    latest_prices: Dict[str, float]


@app.get("/health")
def health():
    return {"status": "ok", "service": "Stock-Market-Data-Analyzer"}


@app.get("/chart/{ticker}")
def get_chart(ticker: str):
    df, mode = fetch_or_simulate_ohlcv(ticker.upper(), ROOT / "data")
    ind = compute_indicators(df)
    return {"ticker": ticker.upper(), "mode": mode, "rows": ind.tail(30).fillna(0).to_dict(orient="records")}


@app.post("/backtest/sma")
def backtest(ticker: str = "AAPL", fee_bps: float = 10.0):
    df, mode = fetch_or_simulate_ohlcv(ticker.upper(), ROOT / "data")
    ind = compute_indicators(df)
    return {"ticker": ticker.upper(), "mode": mode, **run_sma_backtest(ind, fee_bps=fee_bps)}


@app.post("/portfolio/pnl")
def portfolio_pnl(req: PortfolioRequest):
    df = compute_portfolio_pnl(req.trades, req.latest_prices)
    total_unrealized_pnl = float(df["unrealized_pnl"].sum()) if not df.empty else 0.0
    return {
        "positions": df.to_dict(orient="records"),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
    }
