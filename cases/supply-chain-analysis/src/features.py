"""Feature engineering for supply chain analysis dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalize defect rates to proportion if needed
    if "defect_rates" in df.columns:
        max_val = df["defect_rates"].max(skipna=True)
        if max_val is not None and max_val > 1.5:
            df["defect_rate_scaled"] = df["defect_rates"] / 100.0
        else:
            df["defect_rate_scaled"] = df["defect_rates"]

    # Derived metrics
    if "revenue_generated" in df.columns and "number_of_products_sold" in df.columns and "price" in df.columns:
        units = df["number_of_products_sold"].replace(0, np.nan)
        df["unit_margin_proxy"] = (df["revenue_generated"] / units) - df["price"]

    if "number_of_products_sold" in df.columns and "availability" in df.columns:
        df["demand_signal"] = df["number_of_products_sold"] / df["availability"].replace(0, 1)

    if "stock_levels" in df.columns and "number_of_products_sold" in df.columns:
        df["stock_cover_proxy"] = df["stock_levels"] / df["number_of_products_sold"].replace(0, 1)

    if "shipping_costs" in df.columns:
        df["total_logistics_cost"] = df["shipping_costs"].fillna(0)
        if "costs" in df.columns:
            df["total_logistics_cost"] = df["total_logistics_cost"] + df["costs"].fillna(0)

    if "manufacturing_costs" in df.columns:
        if "production_volumes" in df.columns:
            df["total_manufacturing_cost"] = df["manufacturing_costs"] * df["production_volumes"]
        else:
            df["total_manufacturing_cost"] = df["manufacturing_costs"]

    if "total_logistics_cost" in df.columns and "total_manufacturing_cost" in df.columns:
        df["total_cost_proxy"] = df["total_logistics_cost"] + df["total_manufacturing_cost"]

    if "defect_rate_scaled" in df.columns and "total_cost_proxy" in df.columns:
        df["defect_cost_risk_proxy"] = df["defect_rate_scaled"] * df["total_cost_proxy"]

    if "total_logistics_cost" in df.columns and "number_of_products_sold" in df.columns:
        df["logistics_cost_per_unit"] = df["total_logistics_cost"] / df["number_of_products_sold"].replace(0, 1)

    return df
