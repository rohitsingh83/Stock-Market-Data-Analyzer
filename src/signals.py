"""
Trading signals from technical indicators, plus a combined snapshot of what
each indicator says today. Educational only, not investment advice.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    indicator: str
    reading: str
    verdict: str   # Bullish / Bearish / Neutral
    explanation: str


def crossovers(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """+1 on the day fast crosses above slow, -1 when it crosses below, else 0."""
    above = (fast > slow).astype(int)
    return above.diff().fillna(0).astype(int)


def signal_snapshot(df: pd.DataFrame) -> list[Signal]:
    """df must already contain indicators (see indicators.add_indicators)."""
    last = df.iloc[-1]
    out = []
    trend = "Bullish" if last["Close"] > last["SMA50"] > last["SMA200"] else \
            "Bearish" if last["Close"] < last["SMA50"] < last["SMA200"] else "Neutral"
    out.append(Signal("Trend (SMA 50/200)", f"{last['Close']:,.0f} vs {last['SMA50']:,.0f} / {last['SMA200']:,.0f}",
                      trend, "Price above both averages and SMA50 above SMA200 is an uptrend."))
    cross = crossovers(df["SMA50"], df["SMA200"])
    recent = cross[cross != 0].tail(1)
    if not recent.empty:
        kind = "Golden cross" if recent.iloc[0] > 0 else "Death cross"
        out.append(Signal("Last 50/200 crossover", f"{kind} on {recent.index[0]:%d %b %Y}",
                          "Bullish" if recent.iloc[0] > 0 else "Bearish",
                          "Golden cross = SMA50 moves above SMA200; death cross = moves below."))
    r = last["RSI14"]
    out.append(Signal("RSI (14)", f"{r:.1f}", "Bearish" if r > 70 else "Bullish" if r < 30 else "Neutral",
                      "Above 70 is overbought (may fall), below 30 oversold (may bounce)."))
    out.append(Signal("MACD", f"{last['MACD']:.2f} vs signal {last['MACD_signal']:.2f}",
                      "Bullish" if last["MACD"] > last["MACD_signal"] else "Bearish",
                      "MACD above its signal line shows rising momentum."))
    pos = (last["Close"] - last["BB_lower"]) / (last["BB_upper"] - last["BB_lower"])
    out.append(Signal("Bollinger position", f"{pos * 100:.0f}% of band",
                      "Bearish" if pos > 1 else "Bullish" if pos < 0 else "Neutral",
                      "Closing outside the bands signals an unusually large move."))
    return out


def overall_view(signals: list[Signal]) -> str:
    score = sum({"Bullish": 1, "Bearish": -1}.get(s.verdict, 0) for s in signals)
    return "Mostly bullish" if score >= 2 else "Mostly bearish" if score <= -2 else "Mixed"
