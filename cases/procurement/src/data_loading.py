"""Data loading for procurement KPI analysis dataset."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from shared.src.common_etl import read_csv, parse_dates


def load_raw(path: str | Path) -> pd.DataFrame:
    df = read_csv(path)
    df, _ = parse_dates(df, ["order_date", "delivery_date"])
    return df
