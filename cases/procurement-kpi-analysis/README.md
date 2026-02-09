# Case: procurement-kpi-analysis

## Overview
- Business question(s): How do savings, defects, lead times, and compliance shape procurement risk?
- Audience: Procurement leadership and supplier management.
- Decision impact: Supplier scorecards, governance, and negotiation strategy.

## Data
- Source file: `Procurement KPI Analysis Dataset.csv`
- Rows/columns: 777 / 11
- Suppliers: 5 (anonymized)
- Time coverage:
  - Order_Date: 2022-01-01 to 2024-01-01
  - Delivery_Date: 2022-01-06 to 2024-01-12
- Known data issues: missing delivery dates, partial orders, and outliers

## Approach
- Ingest + cleaning (explicit handling of missing defect units)
- KPI calculations (savings, defect exposure, lead time, compliance)
- Supplier risk scoring and segmentation
- BI exports (star schema + flat)

## BI Model
- Fact grain: One row per purchase order line
- Measures: gross_po_value, negotiated_po_value, realized_savings, defect_rate_pct, spend_at_risk
- Dimensions: dim_date, dim_supplier, dim_item_category, dim_order_status, dim_compliance
- Join keys: order_date_key, delivery_date_key, supplier_key, item_category_key, order_status_key, compliance_key

## Exports
- `exports/bi_fact_procurement_kpi_analysis.csv` + `.parquet`
- `exports/dim_*.csv` + `.parquet`
- `exports/flat_procurement_kpi_analysis_pivot_ready.csv`
- `exports/data_dictionary.csv`
- `exports/star_schema.md`
- `exports/supplier_segmentation.csv`
- `exports/pareto_savings.csv` and `exports/pareto_risk.csv`
- `exports/scenario_noncompliant_spend.json`
- `exports/scenario_defect_reduction.json`

## Notebooks
- `notebooks/01_eda.ipynb`
- `notebooks/02_modeling_forecast.ipynb` (risk + segmentation)
- `notebooks/03_executive_dashboard.ipynb`

## Reports
- `reports/EXEC_SUMMARY.md`
- `reports/BI_Quickstart.md`
- `reports/measures.md`
- `reports/figures/`

## How To Run
```bash
python -m cases.procurement-kpi-analysis.src.pipeline --input "Procurement KPI Analysis Dataset.csv" --out reports --exports exports
```

## Methods & Assumptions
- Missing Defective_Units are treated as 0 for rate calculations and flagged.
- Risk scores are composite indices, not causal models.

## Limitations & Next Steps
- Missing delivery dates limit lead time analysis for some orders.
- Add contract terms and SLA detail to improve risk segmentation.
