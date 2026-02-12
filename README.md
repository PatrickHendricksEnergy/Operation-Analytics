# Operation Analytics Portfolio

## Executive Overview
Decision-grade analytics cases that turn operational data into actions on cost, service, and risk. Each case includes executive summaries, visuals, and BI-ready exports for rapid adoption.

## Portfolio Cases
- `cases/procurement`: Supplier performance, compliance, delivery lag, and savings opportunities.
- `cases/scm`: End-to-end supply chain optimization across demand, inventory, logistics, and quality.

## Decision Impact
- Identify revenue concentration and SKU risk exposure.
- Reduce lead-time variability and defect-driven cost leakage.
- Optimize transport mode mix and carrier-route cost-to-serve.
- Surface the highest-impact supplier risks and prioritize action plans.

## Evidence Snapshots
![Procurement Order Value Trend](cases/procurement/reports/figures/order_value_trend_monthly.png)
![Supply Chain KPI Dashboard](cases/scm/reports/figures/kpi_dashboard.png)

## Quick Start
See each case README for exact run commands, inputs, and expected outputs.

## Data Availability
Large raw datasets are excluded from GitHub. Each case README includes sample data and guidance for full data runs.

## BI-Ready Exports
- SCM exports live under `cases/scm/data/processed` (facts, dims, flat pivots).
- Procurement exports live under `cases/procurement/data/processed/exports`.
- Flat pivots are in `data/processed/*_pivot_ready.csv` (or `data/processed/exports/*_pivot_ready.csv`).
- Data dictionary and schema are in `data/processed/data_dictionary.csv` and `data/processed/star_schema.md`.

## Conventions
- `snake_case` columns
- Surrogate keys for dimensions (`*_key`)
- `date_key` (YYYYMMDD int) for time joins
- Numeric measures typed as int/float with no currency symbols

## Ethics & Security
See `DATA_ETHICS.md` and `SECURITY.md` for data handling, privacy, and security expectations.

## Portfolio Summary
See `reports/PORTFOLIO_EXEC_SUMMARY.md` for cross-case highlights and recommendations.

## Repository Structure
```
operation-analytics/
  cases/
  shared/
  reports/
```
