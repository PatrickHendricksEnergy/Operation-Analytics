"""Data loading utilities for inventory analysis case."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from shared.src.common_etl import canonicalize_columns


def detect_dataset_dir(case_dir: Path) -> Path:
    for name in ["Inventory Analysis data set", "inventory_analysis_data", "data"]:
        candidate = case_dir / name
        if candidate.exists() and candidate.is_dir():
            return candidate
    raise FileNotFoundError("Inventory dataset directory not found")


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = canonicalize_columns(df)
    rename_map = {
        "onhand": "on_hand",
        "salesquantity": "sales_quantity",
        "salesdollars": "sales_dollars",
        "salesprice": "sales_price",
        "salesdate": "sales_date",
        "excisetax": "excise_tax",
        "vendorno": "vendor_no",
        "ponumber": "po_number",
        "podate": "po_date",
        "receivingdate": "receiving_date",
        "invoicedate": "invoice_date",
        "paydate": "pay_date",
        "purchaseprice": "purchase_price",
        "vendornumber": "vendor_number",
    }
    for col, new_col in rename_map.items():
        if col in df.columns:
            df = df.rename(columns={col: new_col})
    return df


def load_small_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = _rename_columns(df)
    # parse dates if present
    for col in ["start_date", "end_date", "invoice_date", "po_date", "pay_date", "receiving_date", "sales_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def iter_csv(path: Path, chunksize: int = 200000):
    for chunk in pd.read_csv(path, chunksize=chunksize):
        chunk = _rename_columns(chunk)
        yield chunk


def aggregate_sales(path: Path, chunksize: int = 200000):
    sales_agg = None
    monthly_agg = None
    item_dim = {}

    for chunk in iter_csv(path, chunksize=chunksize):
        if "sales_date" in chunk.columns:
            chunk["sales_date"] = pd.to_datetime(chunk["sales_date"], errors="coerce")
            chunk["sales_month"] = chunk["sales_date"].dt.to_period("M").astype(str)

        # aggregate by inventory_id + store
        group_cols = [c for c in ["inventory_id", "store"] if c in chunk.columns]
        if not group_cols:
            continue
        agg = chunk.groupby(group_cols, dropna=False).agg(
            sales_quantity=("sales_quantity", "sum"),
            sales_dollars=("sales_dollars", "sum"),
        )
        if sales_agg is None:
            sales_agg = agg
        else:
            sales_agg = sales_agg.add(agg, fill_value=0)

        # monthly totals
        if "sales_month" in chunk.columns and "sales_dollars" in chunk.columns:
            m = chunk.groupby("sales_month", dropna=False)["sales_dollars"].sum()
            if monthly_agg is None:
                monthly_agg = m
            else:
                monthly_agg = monthly_agg.add(m, fill_value=0)

        # item dimension (capture first occurrence)
        dim_cols = [c for c in ["inventory_id", "brand", "description", "size", "classification", "volume"] if c in chunk.columns]
        if "inventory_id" in dim_cols:
            dim_sample = chunk[dim_cols].drop_duplicates(subset=["inventory_id"])
            for row in dim_sample.to_dict("records"):
                inv_id = row.get("inventory_id")
                if inv_id is None or inv_id in item_dim:
                    continue
                item_dim[inv_id] = {
                    "inventory_id": inv_id,
                    "brand": row.get("brand"),
                    "description": row.get("description"),
                    "size": row.get("size"),
                    "classification": row.get("classification"),
                    "volume": row.get("volume"),
                }

    sales_agg = sales_agg.reset_index() if sales_agg is not None else pd.DataFrame()
    monthly_agg = monthly_agg.reset_index().rename(columns={0: "sales_dollars"}) if monthly_agg is not None else pd.DataFrame()
    item_dim_df = pd.DataFrame(list(item_dim.values())) if item_dim else pd.DataFrame()

    return sales_agg, monthly_agg, item_dim_df


def aggregate_purchases(path: Path, chunksize: int = 200000):
    purchase_agg = None
    lead_time_sum = None
    vendor_spend = None

    for chunk in iter_csv(path, chunksize=chunksize):
        if "po_date" in chunk.columns:
            chunk["po_date"] = pd.to_datetime(chunk["po_date"], errors="coerce")
        if "receiving_date" in chunk.columns:
            chunk["receiving_date"] = pd.to_datetime(chunk["receiving_date"], errors="coerce")
        if "po_date" in chunk.columns and "receiving_date" in chunk.columns:
            chunk["lead_time_days"] = (chunk["receiving_date"] - chunk["po_date"]).dt.days
            chunk.loc[chunk["lead_time_days"] < 0, "lead_time_days"] = pd.NA

        group_cols = [c for c in ["inventory_id", "store"] if c in chunk.columns]
        if not group_cols:
            continue

        agg = chunk.groupby(group_cols, dropna=False).agg(
            purchase_quantity=("quantity", "sum"),
            purchase_dollars=("dollars", "sum"),
        )
        if purchase_agg is None:
            purchase_agg = agg
        else:
            purchase_agg = purchase_agg.add(agg, fill_value=0)

        if "lead_time_days" in chunk.columns:
            lt = chunk.groupby(group_cols, dropna=False)["lead_time_days"].agg(["sum", "count"])
            if lead_time_sum is None:
                lead_time_sum = lt
            else:
                lead_time_sum = lead_time_sum.add(lt, fill_value=0)

        if "vendor_number" in chunk.columns or "vendor_name" in chunk.columns:
            vendor_cols = [c for c in ["vendor_number", "vendor_name"] if c in chunk.columns]
            v = chunk.groupby(vendor_cols, dropna=False)["dollars"].sum()
            if vendor_spend is None:
                vendor_spend = v
            else:
                vendor_spend = vendor_spend.add(v, fill_value=0)

    purchase_agg = purchase_agg.reset_index() if purchase_agg is not None else pd.DataFrame()
    if lead_time_sum is not None:
        lead_time_sum = lead_time_sum.reset_index().rename(columns={"sum": "lead_time_sum", "count": "lead_time_count"})
    else:
        lead_time_sum = pd.DataFrame()

    vendor_spend = vendor_spend.reset_index().rename(columns={0: "purchase_dollars"}) if vendor_spend is not None else pd.DataFrame()

    return purchase_agg, lead_time_sum, vendor_spend
