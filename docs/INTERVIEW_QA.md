# Interview Preparation: Stock Market Data Analyzer

### 1. Explain your project.

**HR version:** I built a stock analysis tool that downloads share prices and shows how a stock has performed,
how risky it is, and how it compares with other stocks and the market. It can test simple trading strategies on
past data, and suggests how to split money across stocks for the best balance of risk and return. It all comes
together in an interactive dashboard with professional candlestick charts.

**Technical version:** It's a Python quant-analysis pipeline. I pull OHLCV data with yfinance, with caching and
an offline fallback, and clean it with Pandas. I implemented the technical indicators myself: SMA, EMA, Wilder
RSI, MACD, Bollinger Bands, ATR and OBV. I calculate CAGR, annualised volatility, Sharpe, Sortino, max drawdown,
historical VaR, and CAPM beta and alpha against the NIFTY 50. A vectorised backtester runs three strategies with
next-day execution and transaction costs to avoid look-ahead bias. A Monte Carlo Markowitz simulation finds the
max-Sharpe and min-volatility portfolios. The front end is Streamlit with Plotly, and I wrote 14 pytest tests.

### 2. What is the difference between SMA and EMA?

SMA is the plain average of the last N closes, so every day counts equally. EMA gives exponentially more weight
to recent prices, so it reacts faster to new moves but is noisier.

### 3. Explain RSI.

RSI compares the average gain with the average loss over 14 days: `RSI = 100 − 100/(1 + avg gain/avg loss)`,
using Wilder's smoothing. It ranges from 0 to 100. Above 70 is usually called overbought and below 30 oversold.
In strong trends RSI can stay overbought for a long time, so it shouldn't be used alone.

### 4. What do Sharpe ratio and max drawdown tell you?

Sharpe is excess return over the risk-free rate divided by volatility: return per unit of risk. Max drawdown is
the worst peak-to-trough fall, the most painful loss an investor would have sat through. Two stocks with the
same return can have very different Sharpe ratios and drawdowns.

### 5. What is beta?

Beta = covariance(stock, market) ÷ variance(market). A beta of 1.2 means the stock tends to move 1.2% when the
market moves 1%. In my simulated data the analysis recovered the betas used to generate the data (TCS ≈ 0.74,
Tata Motors ≈ 1.24), which validated the code.

### 6. What is look-ahead bias and how did you avoid it?

It means using information in a backtest that wouldn't have been known at the time, for example trading at
today's close on a signal computed from that same close. I shift positions by one day, and a unit test checks
that a strategy can't profit from the price jump that triggered its own signal.

### 7. Why include transaction costs?

Every trade pays brokerage, taxes (STT in India) and slippage. A strategy that trades often can look great
without costs and lose money with them. My backtester charges 10 bps per trade by default, and the dashboard has
a slider to test sensitivity.

### 8. Did the strategies beat buy-and-hold?

Sometimes, depending on the stock and period. On the sample data, the SMA crossover beat buy-and-hold on
HDFC Bank with a much smaller drawdown, but lost on others. That's realistic: no simple rule wins everywhere, and
the main benefit of trend-following is often lower drawdowns rather than higher returns.

### 9. How does the portfolio optimiser work?

It's Markowitz Modern Portfolio Theory. I compute the annualised mean returns and covariance matrix of daily
returns, then generate 4,000 random weight vectors (Dirichlet, so weights are positive and sum to 1). For each
I calculate expected return `wᵀμ`, risk `√(wᵀΣw)` and Sharpe. The max-Sharpe and min-volatility portfolios are
picked from the cloud, which traces the efficient frontier. Diversification works because the stocks aren't
perfectly correlated.

### 10. What are the limitations of your analysis?

Historical returns don't predict future returns, mean-variance optimisation is very sensitive to the expected
return estimates, the backtests ignore dividends and taxes on gains, and two years is a short sample. Technical
signals are educational, not investment advice.

### 11. How did you handle data problems?

yfinance can return MultiIndex columns, timezone-aware dates, duplicates or gaps. The `clean()` function
flattens columns, normalises the index, removes duplicates and missing or zero prices, and sorts by date. If the
download fails, the app falls back to cached data and then to bundled sample data, and the UI clearly shows
which source is in use.

### 12. Why generate simulated data instead of downloading once and saving it?

Redistributing downloaded market data can break the provider's terms, and the build environment had no internet
access. Simulated data with a realistic structure (geometric Brownian motion, regimes, correlations, betas) lets
the project and its tests run anywhere, and it's clearly labelled as simulated. Real data is used automatically
when online.

### 13. How would you extend it?

Fundamental data (P/E, earnings), more strategies with walk-forward optimisation, stop-losses and position
sizing, a database of daily prices updated by a scheduled job, alerts on signals, and an ML model for
volatility forecasting.
