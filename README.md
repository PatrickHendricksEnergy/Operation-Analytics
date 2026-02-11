# Operation Analytics Portfolio

## Overview
This repository contains executive-ready analytics cases with reproducible pipelines, BI-ready exports, and decision-oriented summaries.

### Cases
- `cases/procurement-kpi-analysis`: Supplier performance, compliance, and delivery timing KPIs.
- `cases/supply-chain-analysis`: Supply Chain Analytics & Optimization (end-to-end demand, inventory, logistics, and quality).

### Screenshots
![Procurement Order Value Trend](cases/procurement-kpi-analysis/reports/figures/order_value_trend_monthly.png)
![Supply Chain KPI Dashboard](cases/supply-chain-analysis/visuals/kpi_dashboard.png)

### Quick Run
See each case README for the exact run command and input expectations.

## Data Availability
Large raw datasets are excluded from GitHub. Each case README includes sample data and instructions to run with full data.

## BI-Ready Exports
Each case generates a star schema and flat pivot file:
- `exports/bi_fact_<case>.csv` + `.parquet`
- `exports/dim_*.csv` + `.parquet`
- `exports/flat_<case>_pivot_ready.csv`
- `exports/data_dictionary.csv`
- `exports/star_schema.md`

### Conventions
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
