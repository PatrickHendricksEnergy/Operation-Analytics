"""KPI calculations for supply chain analysis dataset."""
from __future__ import annotations

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict:
    kpis: dict = {}

    if "revenue_generated" in df.columns:
        kpis["total_revenue"] = float(df["revenue_generated"].sum())
        kpis["avg_revenue"] = float(df["revenue_generated"].mean())

    if "total_cost_proxy" in df.columns:
        kpis["total_cost_proxy"] = float(df["total_cost_proxy"].sum())

    if "total_logistics_cost" in df.columns:
        kpis["total_logistics_cost"] = float(df["total_logistics_cost"].sum())

    if "total_manufacturing_cost" in df.columns:
        kpis["total_manufacturing_cost"] = float(df["total_manufacturing_cost"].sum())

    if "defect_rate_scaled" in df.columns:
        kpis["avg_defect_rate"] = float(df["defect_rate_scaled"].mean())

    if "product_type" in df.columns and "revenue_generated" in df.columns:
        top_product = (
            df.groupby("product_type", dropna=False)["revenue_generated"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )
        if not top_product.empty:
            kpis["top_product_type"] = top_product.index[0]

    if "supplier_name" in df.columns and "revenue_generated" in df.columns:
        top_supplier = (
            df.groupby("supplier_name", dropna=False)["revenue_generated"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )
        if not top_supplier.empty:
            kpis["top_supplier"] = top_supplier.index[0]

    if "logistics_cost_per_unit" in df.columns:
        kpis["avg_logistics_cost_per_unit"] = float(df["logistics_cost_per_unit"].mean())

    return kpis


def build_watchlist(df: pd.DataFrame) -> pd.DataFrame:
    """Identify SKUs at risk: high demand signal and low stock cover."""
    if "demand_signal" not in df.columns or "stock_cover_proxy" not in df.columns:
        return pd.DataFrame()

    high_demand = df["demand_signal"] >= df["demand_signal"].quantile(0.75)
    low_cover = df["stock_cover_proxy"] <= df["stock_cover_proxy"].quantile(0.25)
    watch = df.loc[high_demand & low_cover].copy()

    cols = [c for c in ["sku", "product_type", "supplier_name", "location", "demand_signal", "stock_cover_proxy"] if c in watch.columns]
    return watch[cols].sort_values("demand_signal", ascending=False)
