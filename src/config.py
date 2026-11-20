"""Centralized configuration for Stock Market Data Analyzer."""

from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    db_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    images_dir: Path = field(init=False)
    reports_dir: Path = field(init=False)
    
    db_path: Path = field(init=False)
    schema_path: Path = field(init=False)
    
    default_ticker: str = os.getenv("DEFAULT_TICKER", "AAPL")
    fee_bps: float = float(os.getenv("FEE_BPS", "10.0"))
    risk_free_rate: float = float(os.getenv("RISK_FREE_RATE", "0.04"))
    use_live: bool = os.getenv("USE_LIVE", "false").lower() == "true"

    def __post_init__(self):
        root = self.root_dir
        object.__setattr__(self, "data_dir", root / "data")
        object.__setattr__(self, "db_dir", root / "db")
        object.__setattr__(self, "outputs_dir", root / "outputs")
        object.__setattr__(self, "images_dir", root / "images")
        object.__setattr__(self, "reports_dir", root / "reports")
        
        object.__setattr__(self, "db_path", root / "db" / "market.db")
        object.__setattr__(self, "schema_path", root / "db" / "schema.sql")
        
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
