"""Cleaning steps for procurement KPI dataset."""
from __future__ import annotations

import pandas as pd
import numpy as np


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    numeric_cols = ["quantity", "unit_price", "negotiated_price", "defective_units"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = np.nan

    # Explicitly flag missing defects and create filled column (assumption: missing = 0 for rate calc)
    if "defective_units" in df.columns:
        df["defective_units_missing"] = df["defective_units"].isna().astype(int)
        df["defective_units_filled"] = df["defective_units"].fillna(0)

    # Guard illogical values
    if "defective_units" in df.columns and "quantity" in df.columns:
        df.loc[df["defective_units"] > df["quantity"], "defective_units"] = np.nan

    return df
