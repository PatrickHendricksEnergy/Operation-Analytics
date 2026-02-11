"""Star schema + BI exports for supply chain analysis dataset."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from shared.src.common_etl import ensure_dir


def _build_dim(df: pd.DataFrame, col: str, key_name: str) -> pd.DataFrame:
    dim = df[[col]].dropna().drop_duplicates().sort_values(col).reset_index(drop=True)
    dim[key_name] = range(1, len(dim) + 1)
    return dim[[key_name, col]]


def _build_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["sku", "product_type"] if c in df.columns]
    dim = df[cols].dropna().drop_duplicates().sort_values(cols).reset_index(drop=True)
    dim["product_key"] = range(1, len(dim) + 1)
    return dim[["product_key"] + cols]


def build_data_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        inferred_type = str(series.dtype)
        missing_pct = float(series.isna().mean() * 100)

        row = {
            "column": col,
            "inferred_type": inferred_type,
            "%missing": missing_pct,
            "min": "",
            "max": "",
            "top_categories": "",
        }

        if pd.api.types.is_numeric_dtype(series):
            row["min"] = float(series.min()) if series.notna().any() else ""
            row["max"] = float(series.max()) if series.notna().any() else ""
        else:
            vc = series.astype(str).value_counts(normalize=True).head(5)
            top = [f"{idx} ({val:.0%})" for idx, val in vc.items()]
            row["top_categories"] = "; ".join(top)

        rows.append(row)

    return pd.DataFrame(rows)


def render_star_schema_md(fact_grain: str) -> str:
    return "\n".join(
        [
            "# Star Schema — Supply Chain",
            "",
            "## Fact Grain",
            fact_grain,
            "",
            "## Dimensions",
            "- dim_product (product_key, sku, product_type)",
            "- dim_supplier (supplier_key, supplier_name)",
            "- dim_location (location_key, location)",
            "- dim_carrier (carrier_key, shipping_carriers)",
            "- dim_route (route_key, routes)",
            "- dim_mode (mode_key, transportation_modes)",
            "",
            "## Relationships",
            "- fact_supply_chain.product_key -> dim_product.product_key",
            "- fact_supply_chain.supplier_key -> dim_supplier.supplier_key",
            "- fact_supply_chain.location_key -> dim_location.location_key",
            "- fact_supply_chain.carrier_key -> dim_carrier.carrier_key",
            "- fact_supply_chain.route_key -> dim_route.route_key",
            "- fact_supply_chain.mode_key -> dim_mode.mode_key",
        ]
    )


def build_star_schema(df: pd.DataFrame, exports_dir: str | Path) -> dict:
    exports_dir = Path(exports_dir)
    ensure_dir(exports_dir)

    dim_product = _build_dim_product(df) if "sku" in df.columns or "product_type" in df.columns else pd.DataFrame()
    dim_supplier = _build_dim(df, "supplier_name", "supplier_key") if "supplier_name" in df.columns else pd.DataFrame()
    dim_location = _build_dim(df, "location", "location_key") if "location" in df.columns else pd.DataFrame()
    dim_carrier = _build_dim(df, "shipping_carriers", "carrier_key") if "shipping_carriers" in df.columns else pd.DataFrame()
    dim_route = _build_dim(df, "routes", "route_key") if "routes" in df.columns else pd.DataFrame()
    dim_mode = _build_dim(df, "transportation_modes", "mode_key") if "transportation_modes" in df.columns else pd.DataFrame()

    fact = df.copy().reset_index(drop=True)
    fact["record_id"] = fact.index + 1
    fact["currency_code"] = "USD"

    if not dim_product.empty:
        fact = fact.merge(dim_product, on=[c for c in ["sku", "product_type"] if c in fact.columns], how="left")
    if not dim_supplier.empty:
        fact = fact.merge(dim_supplier, on="supplier_name", how="left")
    if not dim_location.empty:
        fact = fact.merge(dim_location, on="location", how="left")
    if not dim_carrier.empty:
        fact = fact.merge(dim_carrier, on="shipping_carriers", how="left")
    if not dim_route.empty:
        fact = fact.merge(dim_route, on="routes", how="left")
    if not dim_mode.empty:
        fact = fact.merge(dim_mode, on="transportation_modes", how="left")

    fact_cols = [
        c
        for c in [
            "record_id",
            "product_key",
            "supplier_key",
            "location_key",
            "carrier_key",
            "route_key",
            "mode_key",
            "price",
            "availability",
            "number_of_products_sold",
            "revenue_generated",
            "stock_levels",
            "lead_times",
            "lead_time",
            "lead_time_canonical",
            "order_quantities",
            "shipping_times",
            "shipping_costs",
            "production_volumes",
            "manufacturing_lead_time",
            "manufacturing_costs",
            "defect_rates",
            "defect_rate_scaled",
            "costs",
            "unit_margin_proxy",
            "demand_signal",
            "stock_cover_proxy",
            "total_logistics_cost",
            "total_manufacturing_cost",
            "total_cost_proxy",
            "defect_cost_risk_proxy",
            "logistics_cost_per_unit",
            "currency_code",
        ]
        if c in fact.columns
    ]
    fact = fact[fact_cols]

    fact_path_csv = exports_dir / "fact_supply_chain.csv"
    fact_path_parquet = exports_dir / "fact_supply_chain.parquet"
    fact.to_csv(fact_path_csv, index=False)
    fact.to_parquet(fact_path_parquet, index=False)

    dims = {
        "dim_product": dim_product,
        "dim_supplier": dim_supplier,
        "dim_location": dim_location,
        "dim_carrier": dim_carrier,
        "dim_route": dim_route,
        "dim_mode": dim_mode,
    }

    for name, dim in dims.items():
        if dim.empty:
            continue
        dim.to_csv(exports_dir / f"{name}.csv", index=False)
        dim.to_parquet(exports_dir / f"{name}.parquet", index=False)

    # Flat export
    flat = fact.copy()
    if not dim_product.empty:
        flat = flat.merge(dim_product, on="product_key", how="left")
    if not dim_supplier.empty:
        flat = flat.merge(dim_supplier, on="supplier_key", how="left")
    if not dim_location.empty:
        flat = flat.merge(dim_location, on="location_key", how="left")
    if not dim_carrier.empty:
        flat = flat.merge(dim_carrier, on="carrier_key", how="left")
    if not dim_route.empty:
        flat = flat.merge(dim_route, on="route_key", how="left")
    if not dim_mode.empty:
        flat = flat.merge(dim_mode, on="mode_key", how="left")

    flat.to_csv(exports_dir / "flat_supply_chain_pivot_ready.csv", index=False)

    # Data dictionary
    dict_df = build_data_dictionary(fact)
    dict_df.to_csv(exports_dir / "data_dictionary.csv", index=False)

    # Star schema markdown
    (exports_dir / "star_schema.md").write_text(
        render_star_schema_md("One row per SKU/location/supplier record")
    )

    return {"fact": fact, "dims": dims}
