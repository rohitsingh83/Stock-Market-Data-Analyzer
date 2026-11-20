"""Portfolio position aggregation and mark-to-market P&L calculation."""
import pandas as pd


def compute_portfolio_pnl(trades: list[dict], latest_prices: dict[str, float]) -> pd.DataFrame:
    rows = []
    for t in trades:
        qty = t["qty"]
        avg_cost = t["avg_cost"]
        mkt = latest_prices.get(t["ticker"], avg_cost)
        pnl = (mkt - avg_cost) * qty
        rows.append({
            "ticker": t["ticker"],
            "qty": qty,
            "avg_cost": avg_cost,
            "market_price": round(mkt, 2),
            "unrealized_pnl": round(pnl, 2),
        })
    return pd.DataFrame(rows)
