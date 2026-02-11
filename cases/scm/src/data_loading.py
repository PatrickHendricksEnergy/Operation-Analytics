"""Data loading for supply chain analysis dataset."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from shared.src.common_etl import read_csv


def detect_csv(case_dir: Path) -> Path:
    data_dir = case_dir / "data" / "raw"
    candidates = list(data_dir.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"No CSV found in {data_dir}")
    # Prefer supply_chain_data.csv if present
    for c in candidates:
        if c.name.lower() == "supply_chain_data.csv":
            return c
    return candidates[0]


def load_raw(path: str | Path | None) -> pd.DataFrame:
    if path is None:
        raise ValueError("path is required")
    return read_csv(path)
