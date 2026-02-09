"""End-to-end pipeline for inventory analysis case."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

from shared.src.common_etl import ensure_dir

from .data_loading import detect_dataset_dir, load_small_csv, aggregate_sales, aggregate_purchases
from .cleaning import clean_inventory, clean_sales, clean_purchases
from .features import compute_abc, compute_eoq, compute_reorder_point, compute_inventory_turnover
from .kpis import compute_kpis
from .modeling import forecast_monthly_sales
from .viz import build_figures
from .bi_model import build_star_schema


CASE_NAME = "inventory_analysis"
CARRYING_COST_RATE = 0.2  # Assumption for annual carrying cost rate


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{value:,.2f}"
    except Exception:
        return str(value)


def _build_exec_summary(kpis: dict, insights: dict, charts: list[str]) -> str:
    headline = [
        f"Total sales are {_format_number(kpis.get('total_sales'))} with total purchases {_format_number(kpis.get('total_purchases'))}.",
        f"Average inventory value is {_format_number(kpis.get('avg_inventory_value'))} with average turnover {_format_number(kpis.get('avg_inventory_turnover'))}.",
        f"Estimated annual carrying cost is {_format_number(kpis.get('total_carrying_cost'))}.",
        f"Items flagged for stockout risk: {kpis.get('stockout_risk_items', 0)}.",
    ]

    actions = [
        "1) Prioritize A-class items with low stock cover and high lead times for tighter replenishment.",
        "2) Reduce excess inventory for low-turnover items through reorder point and EOQ tuning.",
        "3) Align procurement lead times with demand variability to reduce stockouts and carrying costs.",
    ]

    watchlist = insights.get("watchlist_items", [])

    summary = [
        f"# Executive Summary — {CASE_NAME}",
        "",
        "## Headline Findings",
        *[f"- {h}" for h in headline],
        "",
        "## Recommended Actions (Ranked by Impact/Effort)",
        *[f"- {a}" for a in actions],
        "",
        "## Watchlist",
        f"- High-risk items: {', '.join(watchlist) if watchlist else 'N/A'}",
        "",
        "## Charts Included",
        *[f"- {Path(c).name}" for c in charts],
        "",
        "## Methods & Assumptions",
        f"- Carrying cost rate assumed at {CARRYING_COST_RATE:.0%} of average inventory value.",
        "- Lead time calculated from PODate to ReceivingDate and rounded up to whole days.",
        "- Raw materials are identified by the Description field; items with sales are treated as finished goods, purchases-only as raw materials, and remaining as WIP.",
        "",
        "## Limitations & Next Steps",
        "- Dataset lacks explicit service level targets; reorder points exclude safety stock for variability.",
        "- Ordering cost is approximated from invoice freight where available; refine with actual procurement costs.",
        "",
    ]
    return "\n".join(summary)


def _write_bi_quickstart(path: Path) -> None:
    content = """
# BI Quickstart

## Power BI
1. Get Data -> Text/CSV -> select `exports/fact_inventory.csv`.
2. Load `exports/dim_product.csv`, `exports/dim_vendor.csv`, `exports/dim_store.csv`.
3. Create relationships on `inventory_id`, `vendor_number`, and `store`.

## Tableau
1. Connect to `exports/fact_inventory.csv`.
2. Add each `exports/dim_*.csv` as related tables on keys.

## Excel
1. Open `exports/flat_inventory_pivot_ready.csv`.
2. Insert -> PivotTable and build views by supplier, store, and product.
""".strip()
    path.write_text(content)


def _write_measures(path: Path) -> None:
    content = """
# Power BI Measures (DAX)

- m_total_sales = SUM(fact_inventory[sales_dollars])
- m_total_purchases = SUM(fact_inventory[purchase_dollars])
- m_avg_inventory_value = AVERAGE(fact_inventory[avg_inventory_value])
- m_inventory_turnover = DIVIDE([m_total_sales], [m_avg_inventory_value])
- m_carrying_cost = SUM(fact_inventory[carrying_cost])
""".strip()
    path.write_text(content)


def run(
    input_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
    exports_dir: str | Path | None = None,
) -> None:
    case_dir = Path(__file__).resolve().parents[1]
    data_dir = Path(input_dir) if input_dir else detect_dataset_dir(case_dir)
    reports_dir = Path(reports_dir) if reports_dir else case_dir / "reports"
    exports_dir = Path(exports_dir) if exports_dir else case_dir / "exports"

    ensure_dir(reports_dir)
    ensure_dir(exports_dir)

    beg_inv = clean_inventory(load_small_csv(data_dir / "BegInvFINAL12312016.csv"))
    end_inv = clean_inventory(load_small_csv(data_dir / "EndInvFINAL12312016.csv"))
    invoice = load_small_csv(data_dir / "InvoicePurchases12312016.csv")

    sales_agg, monthly_sales, product_dim = aggregate_sales(data_dir / "SalesFINAL12312016.csv")
    sales_agg = clean_sales(sales_agg)

    purchase_agg, lead_time_df, vendor_spend = aggregate_purchases(data_dir / "PurchasesFINAL12312016.csv")
    purchase_agg = clean_purchases(purchase_agg)

    # Basic dims
    store_dim = pd.concat(
        [
            beg_inv[["store", "city"]],
            end_inv[["store", "city"]],
        ]
    ).drop_duplicates().reset_index(drop=True)

    vendor_dim = vendor_spend.copy()
    if "vendor_number" in vendor_dim.columns:
        vendor_dim = vendor_dim[["vendor_number", "vendor_name"]].drop_duplicates()
    else:
        vendor_dim = pd.DataFrame(columns=["vendor_number", "vendor_name"])

    # Inventory snapshot
    inv = beg_inv.merge(end_inv, on=["inventory_id", "store"], how="outer", suffixes=("_beg", "_end"))
    inv["beg_on_hand"] = inv.get("on_hand_beg")
    inv["end_on_hand"] = inv.get("on_hand_end")
    inv["avg_inventory_units"] = (inv["beg_on_hand"].fillna(0) + inv["end_on_hand"].fillna(0)) / 2

    inv["beg_value"] = inv["beg_on_hand"] * inv.get("price_beg")
    inv["end_value"] = inv["end_on_hand"] * inv.get("price_end")
    inv["avg_inventory_value"] = (inv["beg_value"].fillna(0) + inv["end_value"].fillna(0)) / 2

    # Merge sales and purchases
    summary = inv.merge(sales_agg, on=["inventory_id", "store"], how="left")
    summary = summary.merge(purchase_agg, on=["inventory_id", "store"], how="left")
    summary = summary.merge(lead_time_df, on=["inventory_id", "store"], how="left")

    summary["avg_sales_price"] = summary["sales_dollars"] / summary["sales_quantity"].replace(0, np.nan)
    summary["avg_purchase_price"] = summary["purchase_dollars"] / summary["purchase_quantity"].replace(0, np.nan)

    summary["avg_lead_time_days"] = summary["lead_time_sum"] / summary["lead_time_count"].replace(0, np.nan)
    summary["avg_lead_time_days"] = np.ceil(summary["avg_lead_time_days"]).astype("Int64")

    # Material mapping assumptions
    summary["material_description"] = summary.get("description_beg")
    if "description_end" in summary.columns:
        summary["material_description"] = summary["material_description"].fillna(summary["description_end"])
    summary["material_description"] = summary["material_description"].fillna(summary["inventory_id"])

    sales_units = summary["sales_quantity"].fillna(0)
    purchase_units = summary["purchase_quantity"].fillna(0)
    summary["material_type"] = np.where(
        sales_units > 0,
        "finished_goods",
        np.where(purchase_units > 0, "raw_material", "wip"),
    )

    # Demand rate for reorder point
    if not monthly_sales.empty:
        monthly_sales["sales_month"] = pd.to_datetime(monthly_sales["sales_month"], errors="coerce")
        period_days = (monthly_sales["sales_month"].max() - monthly_sales["sales_month"].min()).days
        period_days = period_days if period_days > 0 else 365
    else:
        period_days = 365

    summary["annual_demand_units"] = summary["sales_quantity"].fillna(0)
    summary["daily_demand_units"] = summary["annual_demand_units"] / period_days

    summary["reorder_point"] = compute_reorder_point(summary["daily_demand_units"], summary["avg_lead_time_days"].fillna(0))

    # EOQ
    ordering_cost = invoice["freight"].mean() if "freight" in invoice.columns else 0
    holding_cost = summary["avg_purchase_price"].fillna(0) * CARRYING_COST_RATE
    summary["eoq"] = compute_eoq(summary["annual_demand_units"], ordering_cost, holding_cost)

    # ABC
    abc = compute_abc(summary.rename(columns={"sales_dollars": "sales_dollars"}), value_col="sales_dollars")
    summary = summary.merge(abc[["inventory_id", "abc_class"]], on="inventory_id", how="left")

    # Inventory turnover
    summary["inventory_turnover"] = compute_inventory_turnover(summary["sales_dollars"], summary["avg_inventory_value"])

    # Carrying cost
    summary["carrying_cost"] = summary["avg_inventory_value"] * CARRYING_COST_RATE

    # Stockout risk flag (simple): end_on_hand < reorder_point
    summary["stockout_risk_flag"] = (summary["end_on_hand"] < summary["reorder_point"]).fillna(False).astype(int)

    # Watchlist
    watchlist = summary.sort_values("stockout_risk_flag", ascending=False).head(10)["inventory_id"].astype(str).tolist()

    # KPI snapshot
    kpis = compute_kpis(summary)
    (reports_dir / "kpi_snapshot.json").write_text(json.dumps(kpis, indent=2))

    # Forecast
    forecast_df = forecast_monthly_sales(monthly_sales, periods=3)
    if not forecast_df.empty:
        forecast_df["currency_code"] = "USD"
        forecast_df.to_csv(exports_dir / "forecast_inventory_sales.csv", index=False)

    # ABC export
    if not abc.empty:
        abc.to_csv(exports_dir / "abc_classification.csv", index=False)

    # Supplier spend
    if not vendor_spend.empty:
        vendor_spend["currency_code"] = "USD"
        vendor_spend.to_csv(exports_dir / "supplier_spend.csv", index=False)

    # Optimal inventory levels by raw material (description-based)
    if "material_description" in summary.columns:
        raw_only = summary[summary["material_type"] == "raw_material"].copy()
        material_levels = (
            raw_only.groupby("material_description", dropna=False)
            .agg(
                material_type=("material_type", "first"),
                eoq_units=("eoq", "sum"),
                reorder_point_units=("reorder_point", "sum"),
                avg_inventory_units=("avg_inventory_units", "mean"),
                avg_lead_time_days=("avg_lead_time_days", "mean"),
                inventory_turnover=("inventory_turnover", "mean"),
                avg_inventory_value=("avg_inventory_value", "sum"),
                carrying_cost=("carrying_cost", "sum"),
            )
            .reset_index()
        )
        material_levels["currency_code"] = "USD"
        material_levels.to_csv(exports_dir / "optimal_inventory_levels_raw_materials.csv", index=False)

    # Optimal inventory levels by material type (raw / wip / finished)
    if "material_type" in summary.columns:
        material_type_levels = (
            summary.groupby("material_type", dropna=False)
            .agg(
                eoq_units=("eoq", "sum"),
                reorder_point_units=("reorder_point", "sum"),
                avg_inventory_units=("avg_inventory_units", "mean"),
                avg_lead_time_days=("avg_lead_time_days", "mean"),
                inventory_turnover=("inventory_turnover", "mean"),
                avg_inventory_value=("avg_inventory_value", "sum"),
                carrying_cost=("carrying_cost", "sum"),
            )
            .reset_index()
        )
        material_type_levels["currency_code"] = "USD"
        material_type_levels.to_csv(exports_dir / "optimal_inventory_levels_by_material_type.csv", index=False)

    # Build figures
    chart_files = build_figures(summary, monthly_sales, abc, vendor_spend, reports_dir)

    # BI exports
    flat = summary.copy()
    flat["currency_code"] = "USD"
    flat.to_csv(exports_dir / "flat_inventory_pivot_ready.csv", index=False)

    build_star_schema(summary, product_dim, vendor_dim, store_dim, exports_dir)

    # Executive summary
    insights = {"watchlist_items": watchlist}
    exec_summary = _build_exec_summary(kpis, insights, chart_files)
    (reports_dir / "EXEC_SUMMARY.md").write_text(exec_summary)
    _write_bi_quickstart(reports_dir / "BI_Quickstart.md")
    _write_measures(reports_dir / "measures.md")

    # Assumptions log
    assumptions = [
        "# Assumptions Log — inventory_analysis",
        "",
        "- Raw materials are identified by the Description field (material_description).",
        "- Items with sales are classified as finished goods; items with purchases but no sales are classified as raw materials; remaining items are treated as WIP.",
        "- EOQ uses average invoice freight as an ordering cost proxy.",
        f"- Carrying cost rate assumed at {CARRYING_COST_RATE:.0%} of average inventory value.",
        "- Lead time is rounded up to whole days; negative lead times are excluded.",
    ]
    (reports_dir / "ASSUMPTIONS.md").write_text("\n".join(assumptions))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run inventory analysis pipeline")
    parser.add_argument("--input", dest="input_dir", default=None)
    parser.add_argument("--out", dest="reports_dir", default=None)
    parser.add_argument("--exports", dest="exports_dir", default=None)
    args = parser.parse_args()
    run(args.input_dir, args.reports_dir, args.exports_dir)
