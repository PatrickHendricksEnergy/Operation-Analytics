"""Common ETL helpers for the Operation Analytics portfolio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _to_snake(name: str) -> str:
    name = name.strip().replace("/", " ")
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with snake_case, unique column names."""
    cols = [_to_snake(c) for c in df.columns]
    seen = {}
    new_cols = []
    for c in cols:
        if c not in seen:
            seen[c] = 1
            new_cols.append(c)
        else:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
    df = df.copy()
    df.columns = new_cols
    return df


def parse_dates(
    df: pd.DataFrame, date_cols: Iterable[str] | None = None
) -> Tuple[pd.DataFrame, List[str]]:
    """Parse date columns; infer if not provided.

    Returns (df, parsed_cols).
    """
    df = df.copy()
    parsed = []

    if date_cols is None:
        candidates = [c for c in df.columns if re.search(r"date|datetime|timestamp", c)]
    else:
        candidates = list(date_cols)

    for col in candidates:
        if col not in df.columns:
            continue
        if not pd.api.types.is_object_dtype(df[col]) and not pd.api.types.is_string_dtype(df[col]):
            # Only parse object-like columns unless explicitly requested
            if date_cols is None:
                continue
        parsed_col = pd.to_datetime(df[col], errors="coerce")
        if parsed_col.notna().mean() >= 0.6:
            df[col] = parsed_col
            parsed.append(col)
    return df, parsed


def infer_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe describing schema and missingness."""
    rows = []
    for col in df.columns:
        series = df[col]
        example = series.dropna().iloc[0] if series.notna().any() else ""
        rows.append(
            {
                "column": col,
                "dtype": str(series.dtype),
                "nullable": bool(series.isna().any()),
                "missing_pct": float(series.isna().mean() * 100),
                "example_value": example,
            }
        )
    return pd.DataFrame(rows)


def read_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = canonicalize_columns(df)
    df, _ = parse_dates(df)
    return df


def build_dim_date(min_date: pd.Timestamp, max_date: pd.Timestamp) -> pd.DataFrame:
    if pd.isna(min_date) or pd.isna(max_date):
        return pd.DataFrame(columns=[
            "date_key",
            "date",
            "year",
            "quarter",
            "month",
            "month_name",
            "day",
            "day_of_week",
            "day_name",
            "week_of_year",
            "is_weekend",
        ])

    date_range = pd.date_range(min_date, max_date, freq="D")
    df = pd.DataFrame({"date": date_range})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["day"] = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.weekday + 1
    df["day_name"] = df["date"].dt.strftime("%A")
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["day_of_week"].isin([6, 7]).astype(int)
    return df


def set_matplotlib_cache_dir() -> None:
    """Ensure matplotlib has a writable cache dir."""
    if "MPLCONFIGDIR" not in os.environ:
        os.environ["MPLCONFIGDIR"] = str(Path("/tmp") / "matplotlib")
    if "MPLBACKEND" not in os.environ:
        os.environ["MPLBACKEND"] = "Agg"
