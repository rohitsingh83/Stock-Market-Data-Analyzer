import unittest
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

from src.ingest import generate_synthetic_ohlcv, fetch_or_simulate_ohlcv
from src.indicators import compute_indicators
from src.backtest import run_sma_backtest
from src.portfolio import compute_portfolio_pnl
from jobs.alerts import check_technical_alerts
from api.app import app

ROOT = Path(__file__).resolve().parent.parent


class TestStockAnalyzer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_synthetic_data_generation(self):
        df = generate_synthetic_ohlcv("AAPL", days=100)
        self.assertEqual(len(df), 100)
        for col in ["date", "open", "high", "low", "close", "volume"]:
            self.assertIn(col, df.columns)
        self.assertTrue((df["high"] >= df["low"]).all())

    def test_indicators_computation(self):
        df = generate_synthetic_ohlcv("AAPL", days=150)
        ind = compute_indicators(df)
        self.assertIn("sma20", ind.columns)
        self.assertIn("sma50", ind.columns)
        self.assertIn("rsi14", ind.columns)
        self.assertIn("macd", ind.columns)
        self.assertIn("bb_upper", ind.columns)
        self.assertIn("bb_lower", ind.columns)
        self.assertIn("signal", ind.columns)

    def test_sma_backtest(self):
        df = generate_synthetic_ohlcv("AAPL", days=150)
        ind = compute_indicators(df)
        bt = run_sma_backtest(ind, fee_bps=10.0)
        self.assertIn("total_return_pct", bt)
        self.assertIn("sharpe_ratio", bt)
        self.assertIn("max_drawdown_pct", bt)
        self.assertIn("win_rate_pct", bt)

    def test_portfolio_pnl(self):
        trades = [
            {"ticker": "AAPL", "qty": 10, "avg_cost": 150.0},
            {"ticker": "MSFT", "qty": 5, "avg_cost": 300.0},
        ]
        latest_prices = {"AAPL": 160.0, "MSFT": 320.0}
        pnl_df = compute_portfolio_pnl(trades, latest_prices)
        self.assertEqual(len(pnl_df), 2)
        # AAPL: (160 - 150) * 10 = 100.0
        # MSFT: (320 - 300) * 5 = 100.0
        self.assertEqual(pnl_df.loc[pnl_df["ticker"] == "AAPL", "unrealized_pnl"].iloc[0], 100.0)
        self.assertEqual(pnl_df.loc[pnl_df["ticker"] == "MSFT", "unrealized_pnl"].iloc[0], 100.0)

    def test_technical_alerts(self):
        # Create a mock dataframe where RSI < 30
        df = pd.DataFrame([{
            "date": "2026-11-20",
            "close": 95.0,
            "rsi14": 25.0,
            "bb_lower": 100.0,
        }])
        alerts = check_technical_alerts(df, "AAPL")
        rules = {a["rule"] for a in alerts}
        self.assertIn("RSI_LT_30", rules)
        self.assertIn("CLOSE_LT_BBLOWER", rules)

    def test_api_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_api_chart(self):
        resp = self.client.get("/chart/AAPL")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["ticker"], "AAPL")
        self.assertIn("rows", data)

    def test_api_backtest(self):
        resp = self.client.post("/backtest/sma?ticker=AAPL&fee_bps=10.0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_return_pct", data)
        self.assertIn("sharpe_ratio", data)

    def test_api_portfolio_pnl(self):
        payload = {
            "trades": [{"ticker": "AAPL", "qty": 10, "avg_cost": 150.0}],
            "latest_prices": {"AAPL": 160.0},
        }
        resp = self.client.post("/portfolio/pnl", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_unrealized_pnl"], 100.0)


if __name__ == "__main__":
    unittest.main()
