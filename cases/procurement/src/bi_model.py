"""Star schema + BI exports for procurement KPI dataset."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from shared.src.common_etl import build_dim_date, ensure_dir


def _build_dim(df: pd.DataFrame, col: str, key_name: str) -> pd.DataFrame:
    dim = df[[col]].dropna().drop_duplicates().sort_values(col).reset_index(drop=True)
    dim[key_name] = range(1, len(dim) + 1)
    return dim[[key_name, col]]


def _generate_data_dictionary(df: pd.DataFrame, table_name: str, descriptions: dict) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        example = series.dropna().iloc[0] if series.notna().any() else ""
        rows.append(
            {
                "table": table_name,
                "column": col,
                "type": str(series.dtype),
                "%missing": float(series.isna().mean() * 100),
                "description": descriptions.get(col, ""),
                "example_value": example,
            }
        )
    return pd.DataFrame(rows)


def build_star_schema(
    df: pd.DataFrame,
    exports_dir: str | Path,
    supplier_summary: pd.DataFrame | None = None,
) -> dict:
    exports_dir = Path(exports_dir)
    ensure_dir(exports_dir)

    dim_supplier = _build_dim(df, "supplier", "supplier_key") if "supplier" in df.columns else pd.DataFrame()
    dim_item_category = _build_dim(df, "item_category", "item_category_key") if "item_category" in df.columns else pd.DataFrame()
    dim_order_status = _build_dim(df, "order_status", "order_status_key") if "order_status" in df.columns else pd.DataFrame()
    dim_compliance = _build_dim(df, "compliance", "compliance_key") if "compliance" in df.columns else pd.DataFrame()

    if supplier_summary is not None and not supplier_summary.empty and not dim_supplier.empty:
        dim_supplier = dim_supplier.merge(
            supplier_summary[["supplier", "supplier_risk_score", "supplier_segment"]],
            on="supplier",
            how="left",
        )

    if "order_date" in df.columns or "delivery_date" in df.columns:
        min_date = pd.to_datetime(df[[c for c in ["order_date", "delivery_date"] if c in df.columns]].min().min())
        max_date = pd.to_datetime(df[[c for c in ["order_date", "delivery_date"] if c in df.columns]].max().max())
        dim_date = build_dim_date(min_date, max_date)
    else:
        dim_date = pd.DataFrame()

    fact = df.copy()

    if not dim_supplier.empty:
        fact = fact.merge(dim_supplier[["supplier", "supplier_key"]], on="supplier", how="left")
    if not dim_item_category.empty:
        fact = fact.merge(dim_item_category, on="item_category", how="left")
    if not dim_order_status.empty:
        fact = fact.merge(dim_order_status, on="order_status", how="left")
    if not dim_compliance.empty:
        fact = fact.merge(dim_compliance, on="compliance", how="left")

    if "order_date" in fact.columns:
        fact["order_date_key"] = pd.to_datetime(fact["order_date"], errors="coerce").dt.strftime("%Y%m%d").astype("Int64")
    if "delivery_date" in fact.columns:
        fact["delivery_date_key"] = pd.to_datetime(fact["delivery_date"], errors="coerce").dt.strftime("%Y%m%d").astype("Int64")

    fact["currency_code"] = "USD"

    fact_cols = [
        c
        for c in [
            "po_id",
            "order_date_key",
            "delivery_date_key",
            "supplier_key",
            "item_category_key",
            "order_status_key",
            "compliance_key",
            "quantity",
            "unit_price",
            "negotiated_price",
            "defective_units",
            "defective_units_filled",
            "defective_units_missing",
            "gross_po_value",
            "negotiated_po_value",
            "realized_savings",
            "savings_rate_pct",
            "defect_rate_pct",
            "defective_cost_exposure",
            "procurement_lead_time_days",
            "non_compliant_flag",
            "spend_at_risk",
            "order_status_risk",
            "currency_code",
        ]
        if c in fact.columns
    ]
    fact = fact[fact_cols]

    fact_path_csv = exports_dir / "bi_fact_procurement_kpi_analysis.csv"
    fact_path_parquet = exports_dir / "bi_fact_procurement_kpi_analysis.parquet"
    fact.to_csv(fact_path_csv, index=False)
    fact.to_parquet(fact_path_parquet, index=False)

    dims = {
        "dim_date": dim_date,
        "dim_supplier": dim_supplier,
        "dim_item_category": dim_item_category,
        "dim_order_status": dim_order_status,
        "dim_compliance": dim_compliance,
    }

    for name, dim in dims.items():
        if dim.empty:
            continue
        dim.to_csv(exports_dir / f"{name}.csv", index=False)
        dim.to_parquet(exports_dir / f"{name}.parquet", index=False)

    flat = fact.copy()
    if not dim_supplier.empty:
        flat = flat.merge(dim_supplier, on="supplier_key", how="left")
    if not dim_item_category.empty:
        flat = flat.merge(dim_item_category, on="item_category_key", how="left")
    if not dim_order_status.empty:
        flat = flat.merge(dim_order_status, on="order_status_key", how="left")
    if not dim_compliance.empty:
        flat = flat.merge(dim_compliance, on="compliance_key", how="left")
    if not dim_date.empty:
        order_dates = dim_date[["date_key", "date"]].rename(
            columns={"date_key": "order_date_key", "date": "order_date"}
        )
        delivery_dates = dim_date[["date_key", "date"]].rename(
            columns={"date_key": "delivery_date_key", "date": "delivery_date"}
        )
        flat = flat.merge(order_dates, on="order_date_key", how="left")
        flat = flat.merge(delivery_dates, on="delivery_date_key", how="left")

    flat.to_csv(exports_dir / "flat_procurement_kpi_analysis_pivot_ready.csv", index=False)

    descriptions_fact = {
        "po_id": "Purchase order identifier",
        "order_date_key": "Order date key (YYYYMMDD)",
        "delivery_date_key": "Delivery date key (YYYYMMDD)",
        "supplier_key": "Supplier surrogate key",
        "item_category_key": "Item category surrogate key",
        "order_status_key": "Order status surrogate key",
        "compliance_key": "Compliance surrogate key",
        "quantity": "Ordered quantity",
        "unit_price": "Unit price before negotiation",
        "negotiated_price": "Negotiated unit price",
        "defective_units": "Reported defective units (raw)",
        "defective_units_filled": "Defective units with missing filled as 0",
        "defective_units_missing": "Flag for missing defective units",
        "gross_po_value": "Quantity * unit_price",
        "negotiated_po_value": "Quantity * negotiated_price",
        "realized_savings": "gross_po_value - negotiated_po_value",
        "savings_rate_pct": "Realized savings / gross_po_value",
        "defect_rate_pct": "Defective units / quantity",
        "defective_cost_exposure": "Defective units * negotiated_price",
        "procurement_lead_time_days": "Delivery date minus order date",
        "non_compliant_flag": "1 if compliance == No",
        "spend_at_risk": "Negotiated value for non-compliant orders",
        "order_status_risk": "Risk score derived from order status",
        "currency_code": "Currency code for monetary values (ISO 4217)",
    }
    descriptions_supplier = {
        "supplier_key": "Supplier surrogate key",
        "supplier": "Supplier name",
        "supplier_risk_score": "Composite supplier risk score",
        "supplier_segment": "Supplier segmentation label",
    }
    descriptions_item_category = {
        "item_category_key": "Item category surrogate key",
        "item_category": "Item category",
    }
    descriptions_order_status = {
        "order_status_key": "Order status surrogate key",
        "order_status": "Order status",
    }
    descriptions_compliance = {
        "compliance_key": "Compliance surrogate key",
        "compliance": "Compliance status",
    }
    descriptions_date = {
        "date_key": "Date key (YYYYMMDD)",
        "date": "Calendar date",
        "year": "Calendar year",
        "quarter": "Calendar quarter",
        "month": "Calendar month",
        "month_name": "Calendar month name",
        "day": "Day of month",
        "day_of_week": "Day of week (1=Mon)",
        "day_name": "Day name",
        "week_of_year": "ISO week of year",
        "is_weekend": "Weekend flag",
    }

    dict_frames = [
        _generate_data_dictionary(fact, "bi_fact_procurement_kpi_analysis", descriptions_fact),
    ]
    if not dim_supplier.empty:
        dict_frames.append(_generate_data_dictionary(dim_supplier, "dim_supplier", descriptions_supplier))
    if not dim_item_category.empty:
        dict_frames.append(_generate_data_dictionary(dim_item_category, "dim_item_category", descriptions_item_category))
    if not dim_order_status.empty:
        dict_frames.append(_generate_data_dictionary(dim_order_status, "dim_order_status", descriptions_order_status))
    if not dim_compliance.empty:
        dict_frames.append(_generate_data_dictionary(dim_compliance, "dim_compliance", descriptions_compliance))
    if not dim_date.empty:
        dict_frames.append(_generate_data_dictionary(dim_date, "dim_date", descriptions_date))

    data_dictionary = pd.concat(dict_frames, ignore_index=True)
    data_dictionary.to_csv(exports_dir / "data_dictionary.csv", index=False)

    star_md = "\n".join(
        [
            "# Star Schema: bi_fact_procurement_kpi_analysis",
            "",
            "## Fact Grain",
            "One row per purchase order line",
            "",
            "## Dimensions",
            "- dim_date (date_key)",
            "- dim_supplier (supplier_key)",
            "- dim_item_category (item_category_key)",
            "- dim_order_status (order_status_key)",
            "- dim_compliance (compliance_key)",
            "",
            "## Relationships",
            "- bi_fact_procurement_kpi_analysis.order_date_key -> dim_date.date_key",
            "- bi_fact_procurement_kpi_analysis.delivery_date_key -> dim_date.date_key",
            "- bi_fact_procurement_kpi_analysis.supplier_key -> dim_supplier.supplier_key",
            "- bi_fact_procurement_kpi_analysis.item_category_key -> dim_item_category.item_category_key",
            "- bi_fact_procurement_kpi_analysis.order_status_key -> dim_order_status.order_status_key",
            "- bi_fact_procurement_kpi_analysis.compliance_key -> dim_compliance.compliance_key",
        ]
    )
    (exports_dir / "star_schema.md").write_text(star_md)

    return {"fact": fact, "dims": dims}
