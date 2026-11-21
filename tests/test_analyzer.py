"""Run with:  python -m pytest -q"""

import numpy as np
import pandas as pd
import pytest

from src.analysis import (beta_alpha, cagr, compare, daily_returns, drawdown, max_drawdown, normalised, sharpe,
                          value_at_risk, volatility)
from src.backtest import STRATEGIES, run_backtest
from src.data_loader import INDEX, WATCHLIST, clean, close_matrix, load_many, load_prices
from src.indicators import add_indicators, bollinger, macd, rsi, sma
from src.portfolio import best_portfolios, simulate_portfolios
from src.report import excel_report
from src.signals import crossovers, signal_snapshot


def series(values) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2025-01-01", periods=len(values)), dtype=float)


def test_sample_data_loads_offline():
    d = load_prices("TCS.NS", source="sample")
    assert d.source == "sample" and len(d.df) > 500
    assert list(d.df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert (d.df["High"] >= d.df["Low"]).all()


def test_clean_handles_messy_data():
    raw = pd.DataFrame({"date": ["2025-01-03", "2025-01-02", "2025-01-02", "2025-01-06"],
                        "close": [10, 9, 9, None], "open": [1, 1, 1, 1], "high": [1, 1, 1, 1],
                        "low": [1, 1, 1, 1], "volume": [1, 1, 1, 1]})
    out = clean(raw)
    assert list(out["Close"]) == [9, 10] and out.index.is_monotonic_increasing


def test_sma_and_rsi_known_values():
    s = series(range(1, 21))
    assert sma(s, 5).iloc[-1] == pytest.approx(18)
    assert rsi(s).iloc[-1] == 100                    # only gains -> RSI 100
    assert rsi(series(range(40, 0, -1))).iloc[-1] < 1  # only losses -> RSI ~0


def test_macd_and_bollinger_shapes():
    s = series(np.linspace(100, 150, 60))
    m, b = macd(s), bollinger(s)
    assert m["MACD"].iloc[-1] > 0                     # steady uptrend: fast EMA above slow EMA
    assert (b["BB_upper"].dropna() >= b["BB_lower"].dropna()).all()


def test_risk_metrics_on_known_series():
    s = series([100, 110, 99, 120])
    assert max_drawdown(s) == pytest.approx(-0.1)
    assert drawdown(s).iloc[-1] == 0
    flat = series([100] * 253)
    assert cagr(series([100] * 252 + [110])) == pytest.approx(0.1, rel=0.01)
    assert volatility(daily_returns(flat)) == 0


def test_beta_of_market_with_itself_is_one():
    idx = load_prices(INDEX, source="sample").df["Close"]
    beta, alpha = beta_alpha(daily_returns(idx), daily_returns(idx))
    assert beta == pytest.approx(1.0) and alpha == pytest.approx(0, abs=1e-9)


def test_simulated_betas_are_recovered():
    """The generator used betas 0.75 (TCS) and 1.45 (TATAMOTORS); analysis should find similar values."""
    data = load_many(WATCHLIST, source="sample")
    table = compare(close_matrix(data), load_prices(INDEX, source="sample").df["Close"])
    assert table.loc["TCS.NS", "Beta"] < 0.9 < table.loc["TATAMOTORS.NS", "Beta"]


def test_crossovers():
    fast, slow = series([1, 2, 3, 2, 1]), series([2, 2, 2, 2, 2])
    assert list(crossovers(fast, slow)) == [0, 0, 1, -1, 0]   # 2 is not above 2


@pytest.mark.parametrize("strategy", list(STRATEGIES))
def test_backtests_run_and_are_consistent(strategy):
    close = load_prices("INFY.NS", source="sample").df["Close"]
    r = run_backtest(close, strategy)
    assert r.equity["Strategy"].iloc[0] == pytest.approx(1.0, abs=0.01)
    assert r.metrics["Buy & hold return"] == pytest.approx(close.iloc[-1] / close.iloc[0] - 1)
    assert 0 <= r.metrics["Time invested"] <= 1


def test_backtest_has_no_look_ahead():
    close = series([100, 100, 100, 200, 200])     # jump on day 4
    r = run_backtest(close, "SMA crossover", cost_bps=0, fast=1, slow=2)
    assert r.equity["Strategy"].iloc[3] == 1.0     # signal can't capture the jump that created it


def test_portfolio_weights_sum_to_one():
    closes = close_matrix(load_many(WATCHLIST, source="sample"))
    sim = simulate_portfolios(closes, n=500)
    assert np.allclose(sim[closes.columns].sum(axis=1), 1)
    best = best_portfolios(sim)
    assert best["Max Sharpe"]["Sharpe"] == sim["Sharpe"].max()
    assert best["Min volatility"]["Volatility"] == sim["Volatility"].min()


def test_signals_and_report():
    df = add_indicators(load_prices("RELIANCE.NS", source="sample").df)
    assert {s.verdict for s in signal_snapshot(df)} <= {"Bullish", "Bearish", "Neutral"}
    closes = close_matrix(load_many(WATCHLIST, source="sample"))
    data = excel_report("RELIANCE.NS", df, {"CAGR": 0.1}, compare(closes), [run_backtest(df["Close"])])
    assert data[:2] == b"PK"
    assert normalised(closes).iloc[0].eq(100).all()
