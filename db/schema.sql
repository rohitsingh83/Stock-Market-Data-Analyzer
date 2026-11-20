CREATE TABLE IF NOT EXISTS symbols (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candles_daily (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS indicators_daily (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    sma20 REAL,
    sma50 REAL,
    rsi14 REAL,
    macd REAL,
    macd_signal REAL,
    bb_upper REAL,
    bb_lower REAL,
    signal TEXT,
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS backtests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    strategy TEXT NOT NULL,
    total_return_pct REAL NOT NULL,
    sharpe_ratio REAL NOT NULL,
    max_drawdown_pct REAL NOT NULL,
    win_rate_pct REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
