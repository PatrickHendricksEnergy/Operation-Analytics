"""Feature engineering for inventory analysis dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_abc(df: pd.DataFrame, value_col: str = "sales_dollars") -> pd.DataFrame:
    if df.empty or value_col not in df.columns:
        return pd.DataFrame()

    temp = df[["inventory_id", value_col]].groupby("inventory_id", dropna=False)[value_col].sum().sort_values(ascending=False)
    total = temp.sum()
    if total == 0:
        return pd.DataFrame()

    abc = temp.reset_index().rename(columns={value_col: "annual_value"})
    abc["cum_pct"] = abc["annual_value"].cumsum() / total
    abc["abc_class"] = pd.cut(
        abc["cum_pct"],
        bins=[-np.inf, 0.8, 0.95, np.inf],
        labels=["A", "B", "C"],
    )
    return abc


def compute_eoq(demand: pd.Series, order_cost: float, holding_cost: pd.Series) -> pd.Series:
    # EOQ = sqrt((2*D*S)/H)
    return np.sqrt((2 * demand * order_cost) / holding_cost.replace(0, np.nan))


def compute_reorder_point(demand_rate: pd.Series, lead_time_days: pd.Series) -> pd.Series:
    return demand_rate * lead_time_days


def compute_inventory_turnover(cost_of_sales: pd.Series, avg_inventory_value: pd.Series) -> pd.Series:
    return cost_of_sales / avg_inventory_value.replace(0, np.nan)
