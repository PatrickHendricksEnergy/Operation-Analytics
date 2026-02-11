"""End-to-end pipeline for supply chain analysis dataset."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

from shared.src.common_etl import ensure_dir

from .data_loading import detect_csv, load_raw
from .cleaning import clean_data
from .features import add_features
from .kpis import compute_kpis, build_watchlist
from .modeling import run_regression, run_classification
from .viz import build_figures
from .bi_model import build_star_schema


CASE_NAME = "supply-chain-analysis"


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{value:,.2f}"
    except Exception:
        return str(value)


def _data_quality_summary(df: pd.DataFrame) -> dict:
    summary = {}
    summary["rows"] = int(df.shape[0])
    summary["columns"] = int(df.shape[1])
    summary["duplicates"] = int(df.duplicated().sum())

    # Negative/zero checks for key fields
    checks = {}
    for col in [
        "price",
        "availability",
        "number_of_products_sold",
        "stock_levels",
        "shipping_times",
        "manufacturing_lead_time",
        "lead_time_canonical",
        "shipping_costs",
        "manufacturing_costs",
        "costs",
    ]:
        if col in df.columns:
            checks[col] = int((df[col] <= 0).sum())
    summary["non_positive_counts"] = checks

    if "lead_time_diff" in df.columns:
        summary["lead_time_diff_nonzero"] = int(df["lead_time_diff"].abs().gt(0).sum())

    return summary


def _write_data_quality_report(df: pd.DataFrame, path: Path) -> None:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    missing = df.isna().mean().sort_values(ascending=False)

    outlier_counts = {}
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_counts[col] = int(((series < lower) | (series > upper)).sum())

    lines = [
        "# Data Quality Summary",
        "",
        "## Missingness (Top 10 Columns)",
    ]
    for col, pct in missing.head(10).items():
        lines.append(f"- {col}: {pct:.1%} missing")

    lines.extend(["", "## Outlier Counts (IQR Rule)"])
    for col, count in sorted(outlier_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        lines.append(f"- {col}: {count}")

    path.write_text("\n".join(lines))


def _scenario_carrier_change(df: pd.DataFrame) -> pd.DataFrame:
    required = {"shipping_carriers", "routes", "shipping_costs", "shipping_times"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    agg = (
        df.groupby(["routes", "shipping_carriers"], dropna=False)[["shipping_costs", "shipping_times"]]
        .mean()
        .reset_index()
    )
    scenarios = []
    for route, group in agg.groupby("routes"):
        if group.shape[0] < 2:
            continue
        best = group.sort_values("shipping_costs").iloc[0]
        worst = group.sort_values("shipping_costs", ascending=False).iloc[0]
        scenarios.append(
            {
                "route": route,
                "carrier_from": worst["shipping_carriers"],
                "carrier_to": best["shipping_carriers"],
                "avg_cost_from": float(worst["shipping_costs"]),
                "avg_cost_to": float(best["shipping_costs"]),
                "avg_time_from": float(worst["shipping_times"]),
                "avg_time_to": float(best["shipping_times"]),
                "cost_delta": float(best["shipping_costs"] - worst["shipping_costs"]),
                "time_delta": float(best["shipping_times"] - worst["shipping_times"]),
            }
        )
    return pd.DataFrame(scenarios)


def _scenario_defect_reduction(df: pd.DataFrame) -> pd.DataFrame:
    if "defect_cost_risk_proxy" not in df.columns or "supplier_name" not in df.columns:
        return pd.DataFrame()

    agg = (
        df.groupby("supplier_name", dropna=False)["defect_cost_risk_proxy"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )
    rows = []
    for supplier, value in agg.items():
        rows.append(
            {
                "supplier_name": supplier,
                "current_defect_cost_risk": float(value),
                "risk_reduction_25pct": float(value * 0.25),
                "projected_risk_after": float(value * 0.75),
            }
        )
    return pd.DataFrame(rows)


def _segmentation(df: pd.DataFrame) -> pd.DataFrame:
    required = {"demand_signal", "total_cost_proxy", "defect_cost_risk_proxy"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    df = df.copy()
    df["demand_band"] = np.where(
        df["demand_signal"] >= df["demand_signal"].median(), "High", "Low"
    )
    df["cost_band"] = np.where(
        df["total_cost_proxy"] >= df["total_cost_proxy"].median(), "High", "Low"
    )
    df["defect_band"] = np.where(
        df["defect_cost_risk_proxy"] >= df["defect_cost_risk_proxy"].median(), "High", "Low"
    )

    df["segment"] = (
        "Demand="
        + df["demand_band"]
        + ", Cost="
        + df["cost_band"]
        + ", DefectRisk="
        + df["defect_band"]
    )

    cols = [c for c in ["sku", "product_type", "supplier_name", "segment", "demand_signal", "total_cost_proxy", "defect_cost_risk_proxy"] if c in df.columns]
    return df[cols]


def _build_exec_summary(kpis: dict, watchlist: pd.DataFrame, top_levers: list[str]) -> str:
    headline = [
        f"Total revenue is {_format_number(kpis.get('total_revenue'))} with total cost proxy {_format_number(kpis.get('total_cost_proxy'))}.",
        f"Top product type by revenue is {kpis.get('top_product_type', 'N/A')} and top supplier is {kpis.get('top_supplier', 'N/A')}.",
        f"Average defect rate is {_format_number((kpis.get('avg_defect_rate') or 0) * 100)}%.",
    ]

    actions = [
        "1) Optimize carrier/route combinations with the highest logistics cost per unit.",
        "2) Prioritize quality improvement for suppliers driving the largest defect cost risk.",
        "3) Rebalance inventory for SKUs with high demand signals but low stock cover.",
    ]

    watchlist_items = watchlist.head(5)
    watchlist_str = (
        "; ".join(
            watchlist_items["sku"].astype(str).tolist()
        ) if not watchlist_items.empty and "sku" in watchlist_items.columns else "N/A"
    )

    lever_lines = [f"- {l}" for l in top_levers] if top_levers else ["- N/A"]

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
        f"- Top SKUs to monitor: {watchlist_str}",
        "",
        "## Top Controllable Levers",
        *lever_lines,
        "",
        "## Methods & Assumptions",
        "- Columns standardized to snake_case. Lead time ambiguity resolved via lead_time_canonical. Derived cost and margin proxies computed from provided fields.",
        "",
        "## Limitations & Next Steps",
        "- No time column in dataset, so trend analysis and forecasting are not included.",
        "- Cost proxies assume manufacturing_costs scale with production volumes where available.",
        "",
    ]
    return "\n".join(summary)


def _write_bi_quickstart(path: Path) -> None:
    content = """
# BI Quickstart

## Power BI
1. Get Data -> Text/CSV -> select `data/processed/fact_supply_chain.csv`.
2. Load each `data/processed/dim_*.csv` file.
3. Create relationships on `*_key` fields as described in `data/processed/star_schema.md`.
4. Load `data/processed/flat_supply_chain_pivot_ready.csv` for quick pivots.

## Tableau
1. Connect to `data/processed/fact_supply_chain.csv`.
2. Add each `data/processed/dim_*.csv` as related tables on keys.

## Excel
1. Open `data/processed/flat_supply_chain_pivot_ready.csv`.
2. Insert -> PivotTable and build views by product, supplier, location, carrier, and route.
""".strip()
    path.write_text(content)


def _write_measures(path: Path) -> None:
    content = """
# Power BI Measures (DAX)

- m_total_revenue = SUM(fact_supply_chain[revenue_generated])
- m_total_cost_proxy = SUM(fact_supply_chain[total_cost_proxy])
- m_gross_margin_proxy = [m_total_revenue] - [m_total_cost_proxy]
- m_avg_defect_rate = AVERAGE(fact_supply_chain[defect_rate_scaled])
- m_logistics_cost_per_unit = AVERAGE(fact_supply_chain[logistics_cost_per_unit])
""".strip()
    path.write_text(content)


def run(
    input_path: str | Path | None = None,
    reports_dir: str | Path | None = None,
    exports_dir: str | Path | None = None,
    visuals_dir: str | Path | None = None,
) -> None:
    case_dir = Path(__file__).resolve().parents[1]
    if input_path:
        input_path = Path(input_path)
    else:
        input_path = detect_csv(case_dir)

    reports_dir = Path(reports_dir) if reports_dir else case_dir / "reports"
    exports_dir = Path(exports_dir) if exports_dir else case_dir / "data" / "processed"
    visuals_dir = Path(visuals_dir) if visuals_dir else case_dir / "visuals"

    ensure_dir(reports_dir)
    ensure_dir(exports_dir)
    ensure_dir(visuals_dir)

    df_raw = load_raw(input_path)
    df_clean = clean_data(df_raw)
    df_feat = add_features(df_clean)

    # Data quality summary
    quality = _data_quality_summary(df_feat)
    (reports_dir / "DATA_QUALITY.json").write_text(json.dumps(quality, indent=2))
    _write_data_quality_report(df_feat, reports_dir / "DATA_QUALITY.md")

    # KPIs and watchlist
    kpis = compute_kpis(df_feat)
    watchlist = build_watchlist(df_feat)
    if not watchlist.empty:
        watchlist.to_csv(exports_dir / "watchlist_supply_chain.csv", index=False)
    (reports_dir / "kpi_snapshot.json").write_text(json.dumps(kpis, indent=2))

    # Supplier performance table
    if "supplier_name" in df_feat.columns:
        supplier_perf = df_feat.groupby("supplier_name", dropna=False).agg(
            total_revenue=("revenue_generated", "sum") if "revenue_generated" in df_feat.columns else ("supplier_name", "count"),
            total_cost_proxy=("total_cost_proxy", "sum") if "total_cost_proxy" in df_feat.columns else ("supplier_name", "count"),
            avg_defect_rate=("defect_rate_scaled", "mean") if "defect_rate_scaled" in df_feat.columns else ("supplier_name", "count"),
            avg_logistics_cost_per_unit=("logistics_cost_per_unit", "mean") if "logistics_cost_per_unit" in df_feat.columns else ("supplier_name", "count"),
            avg_lead_time=("lead_time_canonical", "mean") if "lead_time_canonical" in df_feat.columns else ("supplier_name", "count"),
            sku_count=("sku", "nunique") if "sku" in df_feat.columns else ("supplier_name", "count"),
        ).reset_index()
        if "total_revenue" in supplier_perf.columns and "total_cost_proxy" in supplier_perf.columns:
            supplier_perf["gross_margin_proxy"] = supplier_perf["total_revenue"] - supplier_perf["total_cost_proxy"]
        total_rev = supplier_perf["total_revenue"].sum() if "total_revenue" in supplier_perf.columns else 0
        if "total_revenue" in supplier_perf.columns:
            supplier_perf["share_of_revenue"] = supplier_perf["total_revenue"] / total_rev if total_rev else 0
        supplier_perf["currency_code"] = "USD"
        supplier_perf = supplier_perf.sort_values("total_revenue", ascending=False)
        supplier_perf.to_csv(
            exports_dir / "supplier_performance_supply_chain_analysis.csv",
            index=False,
        )

    # Modeling
    reg_scores, reg_importance, reg_metrics, reg_pdp = run_regression(df_feat, target="revenue_generated")
    if not reg_scores.empty:
        reg_scores.to_csv(exports_dir / "model_scores_supply_chain_regression.csv", index=False)
    if not reg_importance.empty:
        reg_importance.to_csv(exports_dir / "feature_importance_supply_chain_regression.csv", index=False)
    if not reg_pdp.empty:
        reg_pdp.to_csv(exports_dir / "partial_dependence_supply_chain.csv", index=False)

    cls_scores, cls_importance, cls_metrics, cls_target = run_classification(df_feat)
    if not cls_scores.empty:
        cls_scores.to_csv(exports_dir / "model_scores_supply_chain_classification.csv", index=False)
    if not cls_importance.empty:
        cls_importance.to_csv(exports_dir / "feature_importance_supply_chain_classification.csv", index=False)

    # Top controllable levers
    top_levers = []
    if not reg_importance.empty:
        levers = reg_importance[reg_importance["feature"].str.contains(
            "shipping_carriers|transportation_modes|routes|supplier_name|price|order_quantities|availability|stock_levels",
            regex=True,
            na=False,
        )]
        raw_levers = levers.head(5)["feature"].tolist()
        cleaned = []
        for feat in raw_levers:
            feat = feat.replace("num__", "").replace("cat__", "")
            for prefix in [
                "shipping_carriers_",
                "transportation_modes_",
                "routes_",
                "supplier_name_",
            ]:
                if feat.startswith(prefix):
                    feat = prefix.replace("_", " ").strip() + ": " + feat[len(prefix):]
            cleaned.append(feat.replace("_", " "))
        top_levers = cleaned

    # Segmentation and scenarios
    segmentation = _segmentation(df_feat)
    if not segmentation.empty:
        segmentation["currency_code"] = "USD"
        segmentation.to_csv(exports_dir / "segmentation_supply_chain.csv", index=False)

    scenario_carrier = _scenario_carrier_change(df_feat)
    if not scenario_carrier.empty:
        scenario_carrier["currency_code"] = "USD"
        scenario_carrier.to_csv(exports_dir / "scenario_carrier_change.csv", index=False)

    scenario_defect = _scenario_defect_reduction(df_feat)
    if not scenario_defect.empty:
        scenario_defect["currency_code"] = "USD"
        scenario_defect.to_csv(exports_dir / "scenario_defect_reduction.csv", index=False)

    # Visuals
    chart_files = build_figures(df_feat, visuals_dir)

    # BI exports
    build_star_schema(df_feat, exports_dir)

    # Executive summary
    exec_summary = _build_exec_summary(kpis, watchlist, top_levers)
    (reports_dir / "EXEC_SUMMARY.md").write_text(exec_summary)
    _write_bi_quickstart(reports_dir / "BI_Quickstart.md")
    _write_measures(reports_dir / "measures.md")

    # Metrics snapshot
    metrics_payload = {
        "kpis": kpis,
        "regression_metrics": reg_metrics,
        "classification_metrics": cls_metrics,
        "classification_target": cls_target,
    }
    (reports_dir / "model_metrics.json").write_text(json.dumps(metrics_payload, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run supply chain analysis pipeline")
    parser.add_argument("--input", dest="input_path", default=None)
    parser.add_argument("--out", dest="reports_dir", default=None)
    parser.add_argument("--exports", dest="exports_dir", default=None)
    args = parser.parse_args()
    run(args.input_path, args.reports_dir, args.exports_dir)
