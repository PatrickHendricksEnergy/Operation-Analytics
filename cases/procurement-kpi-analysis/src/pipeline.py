"""End-to-end pipeline for procurement KPI dataset (no forecasting)."""
from __future__ import annotations

from pathlib import Path
import json

from shared.src.common_etl import ensure_dir

from .data_loading import load_raw
from .cleaning import clean_data
from .features import add_features
from .kpis import compute_kpis
from .modeling import (
    supplier_metrics,
    supplier_risk_score,
    segment_suppliers,
    pareto_by_metric,
    scenario_noncompliant_spend,
    scenario_defect_reduction,
)
from .viz import build_figures
from .bi_model import build_star_schema


CASE_NAME = "procurement-kpi-analysis"


def _format_number(value: float | int | None, pct: bool = False) -> str:
    if value is None:
        return "N/A"
    try:
        if pct:
            return f"{value * 100:,.2f}%"
        return f"{value:,.2f}"
    except Exception:
        return str(value)


def _build_exec_summary(
    kpis: dict,
    scenario1: dict,
    scenario2: dict,
    watchlist: list[str],
    pareto_share: float | None,
) -> str:
    headline = []

    if kpis.get("total_orders") and kpis.get("supplier_count"):
        coverage = f"Dataset covers {kpis.get('total_orders')} purchase orders across {kpis.get('supplier_count')} suppliers"
        if kpis.get("order_date_min") and kpis.get("order_date_max"):
            coverage += f" (Order_Date {kpis.get('order_date_min')} to {kpis.get('order_date_max')})"
        if kpis.get("delivery_date_max"):
            coverage += f"; Delivery_Date through {kpis.get('delivery_date_max')}"
        headline.append(coverage + ".")

    headline.extend([
        f"Total negotiated spend is {_format_number(kpis.get('total_negotiated_po_value'))} with realized savings {_format_number(kpis.get('total_realized_savings'))}.",
        f"Average savings rate is {_format_number(kpis.get('avg_savings_rate_pct'), pct=True)} and average defect rate {_format_number(kpis.get('avg_defect_rate_pct'), pct=True)}.",
        f"Spend at risk from non-compliance is {_format_number(kpis.get('total_spend_at_risk'))}.",
    ])
    if kpis.get("late_delivery_rate") is not None:
        headline.append(
            f"Late delivery rate (p75 threshold {kpis.get('late_delivery_threshold_days'):.1f} days) is {_format_number(kpis.get('late_delivery_rate'), pct=True)}."
        )
    if pareto_share is not None:
        headline.append(f"Top 20% of suppliers account for ~{pareto_share * 100:,.1f}% of realized savings.")

    actions = [
        "1) Prioritize supplier remediation where spend at risk and defect exposure intersect.",
        "2) Negotiate category-level pricing for suppliers with low savings rates and high defect costs.",
        "3) Tighten governance for non-compliant suppliers with high order volumes.",
    ]

    scenario_lines = []
    if scenario1:
        scenario_lines.append(
            f"- Eliminating non-compliant suppliers impacts {_format_number(scenario1.get('pct_spend_at_risk'), pct=True)} of negotiated spend."
        )
    if scenario2:
        scenario_lines.append(
            f"- Reducing defect rate by 25% unlocks ~{_format_number(scenario2.get('estimated_savings'))} in defect-cost exposure."
        )

    scenario_block = scenario_lines if scenario_lines else ["- Insufficient evidence for scenario modeling."]

    limitations = [
        "- Supplier risk score is a composite index, not a causal model.",
    ]
    if kpis.get("missing_delivery_rate") is not None:
        limitations.insert(
            0,
            f"- Missing delivery dates on {_format_number(kpis.get('missing_delivery_rate'), pct=True)} of orders limit lead time analysis.",
        )
    else:
        limitations.insert(0, "- Missing delivery dates limit lead time analysis for some orders.")

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
        f"- Top suppliers to monitor: {', '.join(watchlist) if watchlist else 'N/A'}",
        "",
        "## Scenario Insights",
        *scenario_block,
        "",
        "## Methods & Assumptions",
        "- Missing Defective_Units are treated as 0 for defect rate calculations and flagged via defective_units_missing.",
        "- All metrics computed from provided fields; no forecasting is performed.",
        "",
        "## Limitations & Next Steps",
        *limitations,
        "",
    ]
    return "\n".join(summary)


def _write_bi_quickstart(path: Path) -> None:
    content = """
# BI Quickstart

## Power BI
1. Get Data -> Text/CSV -> select `exports/bi_fact_procurement_kpi_analysis.csv`.
2. Load each `exports/dim_*.csv` file.
3. Create relationships on `*_key` fields as described in `exports/star_schema.md`.
4. Load `exports/flat_procurement_kpi_analysis_pivot_ready.csv` for quick pivots.

## Tableau
1. Connect to `exports/bi_fact_procurement_kpi_analysis.csv`.
2. Add each `exports/dim_*.csv` as related tables on keys.

## Excel
1. Open `exports/flat_procurement_kpi_analysis_pivot_ready.csv`.
2. Insert -> PivotTable and build views by supplier, category, status, and compliance.
""".strip()
    path.write_text(content)


def _write_measures(path: Path) -> None:
    content = """
# Power BI Measures (DAX)

- m_total_negotiated_spend = SUM(bi_fact_procurement_kpi_analysis[negotiated_po_value])
- m_total_savings = SUM(bi_fact_procurement_kpi_analysis[realized_savings])
- m_savings_rate = DIVIDE([m_total_savings], SUM(bi_fact_procurement_kpi_analysis[gross_po_value]))
- m_defect_rate = DIVIDE(SUM(bi_fact_procurement_kpi_analysis[defective_units_filled]), SUM(bi_fact_procurement_kpi_analysis[quantity]))
- m_spend_at_risk = SUM(bi_fact_procurement_kpi_analysis[spend_at_risk])
""".strip()
    path.write_text(content)


def run(
    input_path: str | Path | None = None,
    reports_dir: str | Path | None = None,
    exports_dir: str | Path | None = None,
) -> None:
    case_dir = Path(__file__).resolve().parents[1]
    input_path = Path(input_path) if input_path else case_dir / "Procurement KPI Analysis Dataset.csv"
    reports_dir = Path(reports_dir) if reports_dir else case_dir / "reports"
    exports_dir = Path(exports_dir) if exports_dir else case_dir / "exports"

    ensure_dir(reports_dir)
    ensure_dir(exports_dir)

    df_raw = load_raw(input_path)
    df_clean = clean_data(df_raw)
    df_feat = add_features(df_clean)

    kpis = compute_kpis(df_feat)

    supplier_df = supplier_metrics(df_feat)
    supplier_df = supplier_risk_score(supplier_df)
    supplier_df = segment_suppliers(supplier_df)

    if not supplier_df.empty:
        supplier_df["currency_code"] = "USD"
        supplier_df.to_csv(exports_dir / "supplier_segmentation.csv", index=False)

        supplier_perf = supplier_df.copy()
        total_spend = supplier_perf["negotiated_po_value"].sum() if "negotiated_po_value" in supplier_perf.columns else 0
        if "negotiated_po_value" in supplier_perf.columns:
            supplier_perf["share_of_spend"] = supplier_perf["negotiated_po_value"] / total_spend if total_spend else 0
        supplier_perf["currency_code"] = "USD"
        supplier_perf_cols = [
            c
            for c in [
                "supplier",
                "gross_po_value",
                "negotiated_po_value",
                "realized_savings",
                "savings_rate_pct",
                "defect_rate_pct",
                "defective_cost_exposure",
                "avg_lead_time_days",
                "non_compliance_rate",
                "spend_at_risk",
                "supplier_risk_score",
                "supplier_segment",
                "share_of_spend",
                "currency_code",
            ]
            if c in supplier_perf.columns
        ]
        supplier_perf[supplier_perf_cols].to_csv(
            exports_dir / "supplier_performance_procurement_kpi_analysis.csv",
            index=False,
        )

    pareto_savings = pareto_by_metric(supplier_df, "realized_savings")
    if not pareto_savings.empty:
        pareto_savings["currency_code"] = "USD"
        pareto_savings.to_csv(exports_dir / "pareto_savings.csv", index=False)

    pareto_risk = pareto_by_metric(supplier_df, "supplier_risk_score")
    if not pareto_risk.empty:
        pareto_risk.to_csv(exports_dir / "pareto_risk.csv", index=False)

    scenario1 = scenario_noncompliant_spend(supplier_df)
    scenario2 = scenario_defect_reduction(supplier_df)
    if scenario1:
        scenario1["currency_code"] = "USD"
    if scenario2:
        scenario2["currency_code"] = "USD"
    (exports_dir / "scenario_noncompliant_spend.json").write_text(json.dumps(scenario1, indent=2))
    (exports_dir / "scenario_defect_reduction.json").write_text(json.dumps(scenario2, indent=2))

    chart_files = build_figures(df_feat, supplier_df, reports_dir)

    build_star_schema(df_feat, exports_dir, supplier_summary=supplier_df)

    watchlist = (
        supplier_df.sort_values("supplier_risk_score", ascending=False).head(5)["supplier"].tolist()
        if not supplier_df.empty
        else []
    )

    pareto_share = None
    if not pareto_savings.empty:
        cutoff = max(1, int(len(pareto_savings) * 0.2))
        pareto_share = pareto_savings.head(cutoff)["realized_savings"].sum() / pareto_savings["realized_savings"].sum()

    exec_summary = _build_exec_summary(kpis, scenario1, scenario2, watchlist, pareto_share)
    (reports_dir / "EXEC_SUMMARY.md").write_text(exec_summary)
    _write_bi_quickstart(reports_dir / "BI_Quickstart.md")
    _write_measures(reports_dir / "measures.md")

    (reports_dir / "kpi_snapshot.json").write_text(json.dumps(kpis, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run procurement KPI pipeline")
    parser.add_argument("--input", dest="input_path", default=None)
    parser.add_argument("--out", dest="reports_dir", default=None)
    parser.add_argument("--exports", dest="exports_dir", default=None)
    args = parser.parse_args()
    run(args.input_path, args.reports_dir, args.exports_dir)
