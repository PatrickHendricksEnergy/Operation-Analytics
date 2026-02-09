"""Cleaning steps for supply chain analysis dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd


NUMERIC_COLUMNS = [
    "price",
    "availability",
    "number_of_products_sold",
    "revenue_generated",
    "stock_levels",
    "lead_times",
    "order_quantities",
    "shipping_times",
    "shipping_costs",
    "lead_time",
    "production_volumes",
    "manufacturing_lead_time",
    "manufacturing_costs",
    "defect_rates",
    "costs",
]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = np.nan

    # Standardize inspection results for classification
    if "inspection_results" in df.columns:
        df["inspection_results"] = df["inspection_results"].astype(str).str.strip().str.title()

    # Handle lead time ambiguity
    if "lead_time" in df.columns and "lead_times" in df.columns:
        df["lead_time_diff"] = df["lead_time"] - df["lead_times"]
        df["lead_time_canonical"] = df["lead_time"].where(df["lead_time"].notna(), df["lead_times"])
    elif "lead_time" in df.columns:
        df["lead_time_canonical"] = df["lead_time"]
    elif "lead_times" in df.columns:
        df["lead_time_canonical"] = df["lead_times"]

    # Round up all day-based durations
    for col in ["lead_times", "lead_time", "lead_time_canonical", "manufacturing_lead_time", "shipping_times"]:
        if col in df.columns:
            df.loc[df[col].notna(), col] = np.ceil(df.loc[df[col].notna(), col])

    return df
