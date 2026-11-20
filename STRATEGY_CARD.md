# Strategy Card: SMA Crossover Quantitative Model

## Strategy Details
- **Asset Class:** Equities (US Large-Cap / Tech).
- **Core Signal:** Dual Simple Moving Average (Fast SMA 20, Slow SMA 50).
- **Execution Timing:** Next-day Open execution on previous-day Close signal (Lookahead-bias free).
- **Friction Model:** 10 basis points (0.10%) commission drag per position rebalance.

## Performance Profile (AAPL Benchmark Run)
- **Strategy Return:** Net profitable after transaction friction.
- **Annualized Sharpe Ratio:** Computed over excess returns above 4.0% annualized risk-free rate.
- **Risk Control:** Long-only positioning with flat cash preservation during downtrends.

## Limitations & Risks
- **Whipsaw Risk:** In choppy sideways / range-bound markets, frequent false crossover signals incur consecutive commission drags.
- **Execution Slippage:** Large block orders in real markets may experience wider spreads than simulated fixed bps.
