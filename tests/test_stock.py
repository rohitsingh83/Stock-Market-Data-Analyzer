import unittest
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

from src.ingest import generate_synthetic_ohlcv, fetch_or_simulate_ohlcv
from src.indicators import compute_indicators
from src.backtest import run_sma_backtest
from src.portfolio import compute_portfolio_pnl
from jobs.alerts import check_technical_alerts
from api.app import app

ROOT = Path(__file__).resolve().parent.parent


class TestStockMarketAnalyzer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.df = generate_synthetic_ohlcv("AAPL", days=100)

    def test_synthetic_data_generation(self):
        """Verify synthetic generator yields expected columns and row count."""
        self.assertEqual(len(self.df), 100)
        for col in ["date", "open", "high", "low", "close", "volume"]:
            self.assertIn(col, self.df.columns)

    def test_technical_indicators_computation(self):
        """Verify SMA, RSI, MACD, and Bollinger Bands calculation."""
        ind = compute_indicators(self.df)
        self.assertIn("sma20", ind.columns)
        self.assertIn("sma50", ind.columns)
        self.assertIn("rsi14", ind.columns)
        self.assertIn("macd", ind.columns)
        self.assertIn("bb_upper", ind.columns)
        self.assertIn("bb_lower", ind.columns)
        self.assertIn("atr14", ind.columns)
        self.assertIn("signal", ind.columns)

    def test_sma_backtest_execution(self):
        """Verify backtest returns key metrics within sensible ranges."""
        ind = compute_indicators(self.df)
        bt = run_sma_backtest(ind, fee_bps=10.0)
        self.assertIn("total_return_pct", bt)
        self.assertIn("sharpe_ratio", bt)
        self.assertIn("max_drawdown_pct", bt)
        self.assertIn("win_rate_pct", bt)

    def test_portfolio_pnl(self):
        """Verify portfolio mark-to-market calculations."""
        trades = [{"ticker": "AAPL", "qty": 10, "avg_cost": 150.0}]
        latest_prices = {"AAPL": 165.0}
        pnl = compute_portfolio_pnl(trades, latest_prices)
        self.assertEqual(len(pnl), 1)
        self.assertEqual(pnl.iloc[0]["unrealized_pnl"], 150.0)

    def test_technical_alerts(self):
        """Verify technical alerts rule evaluation."""
        ind = compute_indicators(self.df)
        alerts = check_technical_alerts(ind, "AAPL")
        self.assertIsInstance(alerts, list)

    def test_api_health(self):
        """Verify API health status probe."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_api_chart_endpoint(self):
        """Verify chart endpoint returns ticker indicators."""
        resp = self.client.get("/chart/AAPL")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["ticker"], "AAPL")
        self.assertIn("rows", data)

    def test_api_backtest_endpoint(self):
        """Verify backtest endpoint calculates metrics."""
        resp = self.post_backtest = self.client.post("/backtest/sma?ticker=AAPL&fee_bps=10")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("total_return_pct", resp.json())


if __name__ == "__main__":
    unittest.main()
