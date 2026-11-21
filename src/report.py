"""Excel workbook with the analysis of one stock and a comparison of the watchlist."""

from io import BytesIO

import pandas as pd

from .backtest import BacktestResult

PCT_ROWS = {"Total return", "CAGR", "Volatility", "Max drawdown", "VaR 95% (1 day)", "Best day", "Worst day",
            "Positive days", "Alpha", "Buy & hold return", "Buy & hold max drawdown", "Win rate", "Time invested"}


def excel_report(ticker: str, df: pd.DataFrame, summary: dict, comparison: pd.DataFrame,
                 backtests: list[BacktestResult]) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        book = xw.book
        header = book.add_format({"bold": True, "bg_color": "#1E3A8A", "font_color": "white"})
        pct = book.add_format({"num_format": "0.00%"})
        num = book.add_format({"num_format": "#,##0.00"})

        s = pd.DataFrame({"Metric": list(summary), "Value": list(summary.values())})
        s.to_excel(xw, sheet_name="Summary", index=False, startrow=2)
        sh = xw.sheets["Summary"]
        sh.write(0, 0, f"{ticker}: performance summary", book.add_format({"bold": True, "font_size": 14}))
        sh.set_column(0, 0, 24)
        for i, (k, v) in enumerate(summary.items(), start=3):
            sh.write(i, 1, v, pct if k in PCT_ROWS else num)

        bt = pd.DataFrame({r.strategy: r.metrics for r in backtests})
        bt.to_excel(xw, sheet_name="Backtests")
        xw.sheets["Backtests"].set_column(0, len(backtests), 24)

        comparison.to_excel(xw, sheet_name="Watchlist comparison")
        cs = xw.sheets["Watchlist comparison"]
        cs.set_column(0, len(comparison.columns), 15)

        data = df.copy()
        data.index = data.index.strftime("%Y-%m-%d")
        data.round(4).to_excel(xw, sheet_name="Prices & indicators")
        ps = xw.sheets["Prices & indicators"]
        ps.set_column(0, len(data.columns), 12)
        ps.freeze_panes(1, 1)
        n = len(data)
        chart = book.add_chart({"type": "line"})
        for col, colour in [("Close", "#0F172A"), ("SMA50", "#2563EB"), ("SMA200", "#DC2626")]:
            j = list(data.columns).index(col) + 1
            chart.add_series({"name": col, "categories": ["Prices & indicators", 1, 0, n, 0],
                              "values": ["Prices & indicators", 1, j, n, j], "line": {"color": colour, "width": 1.25}})
        chart.set_title({"name": f"{ticker} price and moving averages"})
        chart.set_x_axis({"num_font": {"rotation": -45}, "interval_unit": 40})
        xw.sheets["Summary"].insert_chart("D3", chart, {"x_scale": 1.8, "y_scale": 1.4})
        for sheet in xw.sheets.values():
            sheet.set_row(0, None, header) if sheet.name != "Summary" else None
    return buf.getvalue()
