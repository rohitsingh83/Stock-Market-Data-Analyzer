# Architecture & Engineering Decisions (ADR)

## ADR 001: Execution Timing in Vectorized Backtesting
- **Status:** Accepted
- **Context:** Signal generation on close with immediate return calculation using daily close-to-close returns introduces lookahead/slippage distortion.
- **Decision:** Shift signal vector by 1 day (`shift(1)`) to simulate next-day position entry and log transaction costs explicitly.
- **Consequences:** Provides realistic equity curve progression with honest friction.

## ADR 002: Risk-Free Rate in Sharpe Ratio
- **Status:** Accepted
- **Context:** Assuming $R_f = 0.0\%$ overstates strategy risk-adjusted quality.
- **Decision:** Parameterize `risk_free_rate` with default 0.04 (4.0% annualized), computing excess returns before standard deviation scaling.
- **Consequences:** Matches industry quantitative standards.

## ADR 003: Deterministic Offline Synthetic Ingestion
- **Status:** Accepted
- **Context:** Real API calls to Yahoo Finance can be throttled or rate-limited in offline and test environments.
- **Decision:** Keep a deterministic geometric Brownian motion candle generator with fixed seed arithmetic as seamless fallback.
- **Consequences:** Tests and local runs remain 100% reproducible and fast without internet connectivity.
