"""KPI calculations for inventory analysis dataset."""
from __future__ import annotations

import pandas as pd


def compute_kpis(summary: pd.DataFrame) -> dict:
    kpis: dict = {}
    if summary.empty:
        return kpis

    if "sales_dollars" in summary.columns:
        kpis["total_sales"] = float(summary["sales_dollars"].sum())

    if "purchase_dollars" in summary.columns:
        kpis["total_purchases"] = float(summary["purchase_dollars"].sum())

    if "avg_inventory_value" in summary.columns:
        kpis["avg_inventory_value"] = float(summary["avg_inventory_value"].sum())

    if "inventory_turnover" in summary.columns:
        kpis["avg_inventory_turnover"] = float(summary["inventory_turnover"].mean())

    if "carrying_cost" in summary.columns:
        kpis["total_carrying_cost"] = float(summary["carrying_cost"].sum())

    if "stockout_risk_flag" in summary.columns:
        kpis["stockout_risk_items"] = int(summary["stockout_risk_flag"].sum())

    return kpis
