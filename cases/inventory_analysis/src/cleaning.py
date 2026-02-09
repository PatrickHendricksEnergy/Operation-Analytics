"""Cleaning steps for inventory analysis dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd


def clean_inventory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["on_hand", "price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = np.nan
    return df


def clean_purchases(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["quantity", "dollars", "purchase_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = np.nan
    return df


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["sales_quantity", "sales_dollars", "sales_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = np.nan
    return df
