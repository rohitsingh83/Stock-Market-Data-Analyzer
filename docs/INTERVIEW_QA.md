# Interview Preparation: Stock Market Data Analyzer (10 Q&As)

1. **Explain your project (Non-Technical):** It's a stock analysis tool that tracks historical price trends, calculates buy/sell momentum signals, measures risk, and tests how a simple trading rule would have performed in the past.
2. **Explain your project (Technical):** It ingests OHLCV candles into SQLite, computes SMA20/50, RSI14, MACD, and Bollinger Bands, runs a vectorized SMA crossover backtest with 10 bps transaction fees, and exposes results via FastAPI and Matplotlib.
3. **Why shift the trading position by 1 day in backtesting?** To eliminate look-ahead bias—a signal computed at today's close can only be executed on the next day.
4. **What is the Sharpe Ratio?** Risk-adjusted return: annualized mean strategy return divided by annualized standard deviation of returns.
5. **How do you measure downside risk?** Using Maximum Drawdown (largest peak-to-trough percentage decline) and annualized volatility.
6. **Why include transaction fees (`fee_bps`)?** Zero-fee backtests overstate profitability on frequent crossovers; modeling 10 bps per trade keeps results realistic.
7. **How does the offline simulation mode work?** When `yfinance` is unreachable, `src/ingest.py` generates deterministic geometric-Brownian-like OHLCV data and caches it to CSV.
8. **What does RSI14 indicate?** Momentum oscillator (0–100); values below 30 suggest oversold conditions and above 70 suggest overbought conditions.
9. **Why use vectorized Pandas/NumPy operations instead of row loops?** Vectorization is orders of magnitude faster and cleaner for time-series backtesting.
10. **What disclaimer is required for FinTech portfolio projects?** Explicitly state the tool is for educational purposes only and is not financial advice.
