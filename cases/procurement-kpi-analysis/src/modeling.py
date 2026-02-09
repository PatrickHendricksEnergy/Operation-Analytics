"""Risk and segmentation analytics for procurement KPI dataset (no forecasting)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _min_max(series: pd.Series) -> pd.Series:
    if series.nunique() <= 1:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - series.min()) / (series.max() - series.min())


def supplier_metrics(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "supplier",
        "gross_po_value",
        "negotiated_po_value",
        "realized_savings",
        "defective_units_filled",
        "quantity",
        "defective_cost_exposure",
        "procurement_lead_time_days",
        "non_compliant_flag",
        "order_status_risk",
        "spend_at_risk",
    ]
    if not all(col in df.columns for col in required):
        return pd.DataFrame()

    agg = df.groupby("supplier", dropna=False).agg(
        gross_po_value=("gross_po_value", "sum"),
        negotiated_po_value=("negotiated_po_value", "sum"),
        realized_savings=("realized_savings", "sum"),
        defective_units=("defective_units_filled", "sum"),
        quantity=("quantity", "sum"),
        defective_cost_exposure=("defective_cost_exposure", "sum"),
        avg_lead_time_days=("procurement_lead_time_days", "mean"),
        non_compliance_rate=("non_compliant_flag", "mean"),
        avg_order_status_risk=("order_status_risk", "mean"),
        spend_at_risk=("spend_at_risk", "sum"),
    ).reset_index()

    agg["defect_rate_pct"] = np.where(
        agg["quantity"] == 0,
        np.nan,
        agg["defective_units"] / agg["quantity"],
    )
    agg["savings_rate_pct"] = np.where(
        agg["gross_po_value"] == 0,
        np.nan,
        agg["realized_savings"] / agg["gross_po_value"],
    )
    agg["spend_at_risk_pct"] = np.where(
        agg["negotiated_po_value"] == 0,
        np.nan,
        agg["spend_at_risk"] / agg["negotiated_po_value"],
    )

    return agg


def supplier_risk_score(supplier_df: pd.DataFrame) -> pd.DataFrame:
    if supplier_df.empty:
        return supplier_df

    risk_components = {
        "non_compliance_rate": 0.25,
        "defect_rate_pct": 0.25,
        "avg_lead_time_days": 0.25,
        "avg_order_status_risk": 0.25,
    }

    for col in risk_components:
        if col not in supplier_df.columns:
            supplier_df[col] = np.nan

    scaled = pd.DataFrame({col: _min_max(supplier_df[col].fillna(0)) for col in risk_components})
    supplier_df["supplier_risk_score"] = 0.0
    for col, weight in risk_components.items():
        supplier_df["supplier_risk_score"] += scaled[col] * weight

    return supplier_df


def segment_suppliers(supplier_df: pd.DataFrame) -> pd.DataFrame:
    if supplier_df.empty:
        return supplier_df

    risk_threshold = supplier_df["supplier_risk_score"].median()
    savings_threshold = supplier_df["savings_rate_pct"].median()
    noncompliance_threshold = supplier_df["non_compliance_rate"].median()

    def label(row):
        high_risk = row["supplier_risk_score"] >= risk_threshold
        high_savings = row["savings_rate_pct"] >= savings_threshold
        high_noncomp = row["non_compliance_rate"] >= noncompliance_threshold

        if high_risk and high_noncomp:
            return "Governance Risk"
        if high_risk and high_savings:
            return "Cost Trap"
        if high_risk and not high_savings:
            return "Operational Risk"
        return "Strategic"

    supplier_df["supplier_segment"] = supplier_df.apply(label, axis=1)
    return supplier_df


def pareto_by_metric(supplier_df: pd.DataFrame, metric: str) -> pd.DataFrame:
    if supplier_df.empty or metric not in supplier_df.columns:
        return pd.DataFrame()
    df = supplier_df[["supplier", metric]].copy()
    df = df.sort_values(metric, ascending=False).reset_index(drop=True)
    total = df[metric].sum()
    if total == 0:
        df["cum_pct"] = 0.0
    else:
        df["cum_pct"] = df[metric].cumsum() / total
    df["supplier_rank"] = df.index + 1
    return df


def scenario_noncompliant_spend(supplier_df: pd.DataFrame) -> dict:
    if supplier_df.empty:
        return {}
    total_spend = supplier_df["negotiated_po_value"].sum()
    spend_at_risk = supplier_df["spend_at_risk"].sum()
    pct = spend_at_risk / total_spend if total_spend else 0
    return {
        "total_spend": float(total_spend),
        "spend_at_risk": float(spend_at_risk),
        "pct_spend_at_risk": float(pct),
    }


def scenario_defect_reduction(supplier_df: pd.DataFrame, reduction_pct: float = 0.25) -> dict:
    if supplier_df.empty or "defective_cost_exposure" not in supplier_df.columns:
        return {}
    current = supplier_df["defective_cost_exposure"].sum()
    savings = current * reduction_pct
    return {
        "current_defect_cost_exposure": float(current),
        "reduction_pct": reduction_pct,
        "estimated_savings": float(savings),
    }
