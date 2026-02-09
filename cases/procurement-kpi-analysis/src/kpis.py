"""KPI calculations for procurement KPI dataset."""
from __future__ import annotations

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict:
    kpis: dict = {}

    if "supplier" in df.columns:
        kpis["supplier_count"] = int(df["supplier"].nunique(dropna=True))

    if "gross_po_value" in df.columns:
        kpis["total_gross_po_value"] = float(df["gross_po_value"].sum())

    if "negotiated_po_value" in df.columns:
        kpis["total_negotiated_po_value"] = float(df["negotiated_po_value"].sum())

    if "realized_savings" in df.columns:
        kpis["total_realized_savings"] = float(df["realized_savings"].sum())
        kpis["avg_savings_rate_pct"] = float(df["savings_rate_pct"].mean()) if "savings_rate_pct" in df.columns else None

    if "defective_cost_exposure" in df.columns:
        kpis["total_defective_cost_exposure"] = float(df["defective_cost_exposure"].sum())

    if "defect_rate_pct" in df.columns:
        kpis["avg_defect_rate_pct"] = float(df["defect_rate_pct"].mean())

    if "procurement_lead_time_days" in df.columns:
        kpis["avg_lead_time_days"] = float(df["procurement_lead_time_days"].mean())
        threshold = df["procurement_lead_time_days"].quantile(0.75)
        kpis["late_delivery_threshold_days"] = float(threshold)
        kpis["late_delivery_rate"] = float((df["procurement_lead_time_days"] > threshold).mean())

    if "non_compliant_flag" in df.columns:
        kpis["non_compliance_rate"] = float(df["non_compliant_flag"].mean())

    if "spend_at_risk" in df.columns:
        kpis["total_spend_at_risk"] = float(df["spend_at_risk"].sum())

    kpis["total_orders"] = int(df.shape[0])

    if "order_date" in df.columns:
        order_dates = pd.to_datetime(df["order_date"], errors="coerce")
        if order_dates.notna().any():
            kpis["order_date_min"] = order_dates.min().date().isoformat()
            kpis["order_date_max"] = order_dates.max().date().isoformat()

    if "delivery_date" in df.columns:
        delivery_dates = pd.to_datetime(df["delivery_date"], errors="coerce")
        kpis["missing_delivery_rate"] = float(delivery_dates.isna().mean())
        if delivery_dates.notna().any():
            kpis["delivery_date_min"] = delivery_dates.min().date().isoformat()
            kpis["delivery_date_max"] = delivery_dates.max().date().isoformat()

    if "supplier" in df.columns and "realized_savings" in df.columns:
        top_supplier = (
            df.groupby("supplier", dropna=False)["realized_savings"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )
        if not top_supplier.empty:
            kpis["top_savings_supplier"] = top_supplier.index[0]

    if "item_category" in df.columns and "realized_savings" in df.columns:
        top_category = (
            df.groupby("item_category", dropna=False)["realized_savings"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )
        if not top_category.empty:
            kpis["top_savings_category"] = top_category.index[0]

    return kpis
