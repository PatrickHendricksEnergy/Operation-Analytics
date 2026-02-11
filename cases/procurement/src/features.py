"""Feature engineering for procurement KPI dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "order_date" in df.columns and "delivery_date" in df.columns:
        df["procurement_lead_time_days"] = (
            pd.to_datetime(df["delivery_date"], errors="coerce")
            - pd.to_datetime(df["order_date"], errors="coerce")
        ).dt.days
        df.loc[df["procurement_lead_time_days"] < 0, "procurement_lead_time_days"] = np.nan
        df.loc[df["procurement_lead_time_days"].notna(), "procurement_lead_time_days"] = np.ceil(
            df.loc[df["procurement_lead_time_days"].notna(), "procurement_lead_time_days"]
        )

    if "quantity" in df.columns and "unit_price" in df.columns:
        df["gross_po_value"] = df["quantity"] * df["unit_price"]

    if "quantity" in df.columns and "negotiated_price" in df.columns:
        df["negotiated_po_value"] = df["quantity"] * df["negotiated_price"]

    if "gross_po_value" in df.columns and "negotiated_po_value" in df.columns:
        df["realized_savings"] = df["gross_po_value"] - df["negotiated_po_value"]
        df["savings_rate_pct"] = np.where(
            df["gross_po_value"] == 0,
            np.nan,
            df["realized_savings"] / df["gross_po_value"],
        )

    if "defective_units_filled" in df.columns and "quantity" in df.columns:
        df["defect_rate_pct"] = np.where(
            df["quantity"] == 0,
            np.nan,
            df["defective_units_filled"] / df["quantity"],
        )

    if "defective_units_filled" in df.columns and "negotiated_price" in df.columns:
        df["defective_cost_exposure"] = df["defective_units_filled"] * df["negotiated_price"]

    if "compliance" in df.columns:
        df["non_compliant_flag"] = df["compliance"].astype(str).str.strip().str.lower().eq("no").astype(int)

    if "negotiated_po_value" in df.columns and "non_compliant_flag" in df.columns:
        df["spend_at_risk"] = np.where(df["non_compliant_flag"] == 1, df["negotiated_po_value"], 0.0)

    # Order status risk mapping
    if "order_status" in df.columns:
        mapping = {
            "delivered": 0.0,
            "pending": 0.5,
            "partially delivered": 0.7,
            "cancelled": 1.0,
        }
        df["order_status_risk"] = (
            df["order_status"].astype(str).str.strip().str.lower().map(mapping).fillna(0.2)
        )

    return df
