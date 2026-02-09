"""Common KPI and evaluation metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd


def safe_mae(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))


def safe_rmse(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def safe_mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    denom = np.where(y_true == 0, np.nan, y_true)
    return float(np.nanmean(np.abs((y_true - y_pred) / denom)) * 100)


def top_n(df: pd.DataFrame, group_col: str, value_col: str, n: int = 10) -> pd.DataFrame:
    if group_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame(columns=[group_col, value_col])
    return (
        df.groupby(group_col, dropna=False)[value_col]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )


def time_coverage(df: pd.DataFrame, date_col: str) -> dict:
    if date_col not in df.columns:
        return {}
    series = pd.to_datetime(df[date_col], errors="coerce")
    return {
        "min": series.min(),
        "max": series.max(),
        "days": (series.max() - series.min()).days if series.notna().any() else None,
    }
