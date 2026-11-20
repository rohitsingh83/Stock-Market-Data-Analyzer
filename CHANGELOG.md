# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-20

### Added
- Standard `pyproject.toml` with PEP 621 packaging metadata.
- Centralized `Settings` configuration dataclass in `src/config.py`.
- Strategy Card (`STRATEGY_CARD.md`) explaining quantitative methodology and risks.
- Average True Range (`ATR 14`) volatility indicator in `src/indicators.py`.
- Buy & Hold benchmark comparison in `src/backtest.py`.
- Parameterized annual risk-free rate in Sharpe ratio calculation.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`).

### Changed
- Shifted strategy positions to simulate realistic Next-Day Open execution.
- Added structured logging to `main.py`.
