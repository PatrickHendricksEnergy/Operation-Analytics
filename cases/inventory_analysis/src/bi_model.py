"""Star schema and BI exports for inventory analysis case."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from shared.src.common_etl import ensure_dir


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
    summary: pd.DataFrame,
    product_dim: pd.DataFrame,
    vendor_dim: pd.DataFrame,
    store_dim: pd.DataFrame,
    exports_dir: str | Path,
) -> dict:
    exports_dir = Path(exports_dir)
    ensure_dir(exports_dir)

    fact = summary.copy()
    fact["currency_code"] = "USD"

    fact_path_csv = exports_dir / "fact_inventory.csv"
    fact_path_parquet = exports_dir / "fact_inventory.parquet"
    fact.to_csv(fact_path_csv, index=False)
    fact.to_parquet(fact_path_parquet, index=False)

    product_dim.to_csv(exports_dir / "dim_product.csv", index=False)
    vendor_dim.to_csv(exports_dir / "dim_vendor.csv", index=False)
    store_dim.to_csv(exports_dir / "dim_store.csv", index=False)

    data_dicts = [
        _generate_data_dictionary(
            fact,
            "fact_inventory",
            {
                "inventory_id": "Inventory item identifier",
                "store": "Store identifier",
                "vendor_number": "Vendor identifier",
                "sales_quantity": "Total sales quantity",
                "sales_dollars": "Total sales dollars",
                "purchase_quantity": "Total purchase quantity",
                "purchase_dollars": "Total purchase dollars",
                "avg_sales_price": "Average sales price",
                "avg_purchase_price": "Average purchase price",
                "avg_lead_time_days": "Average lead time (days)",
                "material_description": "Material identifier (assumed from Description)",
                "material_type": "Material type (raw_material / wip / finished_goods)",
                "beg_on_hand": "Beginning on-hand units",
                "end_on_hand": "Ending on-hand units",
                "avg_inventory_units": "Average inventory units",
                "avg_inventory_value": "Average inventory value",
                "inventory_turnover": "Inventory turnover ratio",
                "eoq": "Economic order quantity",
                "reorder_point": "Reorder point (units)",
                "abc_class": "ABC classification",
                "carrying_cost": "Annual carrying cost",
                "currency_code": "Currency code for monetary values",
            },
        ),
        _generate_data_dictionary(product_dim, "dim_product", {"inventory_id": "Inventory item identifier"}),
        _generate_data_dictionary(vendor_dim, "dim_vendor", {"vendor_number": "Vendor identifier"}),
        _generate_data_dictionary(store_dim, "dim_store", {"store": "Store identifier"}),
    ]

    data_dictionary = pd.concat(data_dicts, ignore_index=True)
    data_dictionary.to_csv(exports_dir / "data_dictionary.csv", index=False)

    star_md = "\n".join(
        [
            "# Star Schema: fact_inventory",
            "",
            "## Fact Grain",
            "One row per inventory_id + store",
            "",
            "## Dimensions",
            "- dim_product (inventory_id)",
            "- dim_vendor (vendor_number)",
            "- dim_store (store)",
            "",
            "## Relationships",
            "- fact_inventory.inventory_id -> dim_product.inventory_id",
            "- fact_inventory.vendor_number -> dim_vendor.vendor_number",
            "- fact_inventory.store -> dim_store.store",
        ]
    )
    (exports_dir / "star_schema.md").write_text(star_md)

    return {
        "fact": fact,
        "dims": {
            "dim_product": product_dim,
            "dim_vendor": vendor_dim,
            "dim_store": store_dim,
        },
    }
