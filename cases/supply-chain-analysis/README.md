# Case: supply-chain-analysis

## Overview
- Business question(s): Which products, suppliers, and logistics choices drive revenue, costs, and quality?
- Audience: Supply chain leadership and operations.
- Decision impact: Transportation optimization, supplier quality programs, and inventory strategy.

## Data
- Source file: `supply_chain_data.csv`
- Rows/columns: 100 / 24
- Time coverage (if applicable): N/A (no date column)

## Approach
- Ingest + cleaning (lead time ambiguity resolved)
- KPI calculations (revenue, costs, defect rates, cost-to-serve)
- Driver models (regression + classification)
- BI exports (star schema + flat)

## BI Model
- Fact grain: One row per SKU/location/supplier record
- Measures: revenue_generated, total_cost_proxy, defect_rate_scaled, logistics_cost_per_unit
- Dimensions: dim_product, dim_supplier, dim_location, dim_carrier, dim_route, dim_mode
- Join keys: product_key, supplier_key, location_key, carrier_key, route_key, mode_key

## Exports
- `exports/fact_supply_chain.csv` + `.parquet`
- `exports/dim_*.csv` + `.parquet`
- `exports/flat_supply_chain_pivot_ready.csv`
- `exports/data_dictionary.csv`
- `exports/star_schema.md`
- `exports/segmentation_supply_chain.csv`
- `exports/scenario_carrier_change.csv`
- `exports/scenario_defect_reduction.csv`

## Notebooks
- `notebooks/01_eda.ipynb`
- `notebooks/02_driver_models.ipynb`
- `notebooks/03_executive_dashboard.ipynb`

## Reports
- `reports/EXEC_SUMMARY.md`
- `reports/BI_Quickstart.md`
- `reports/measures.md`
- `reports/figures/`

## How To Run
```bash
python -m cases.supply-chain-analysis.src.pipeline --input supply_chain_data.csv --out reports --exports exports
```

## Methods & Assumptions
- Cost proxies assume manufacturing_costs scale with production volumes where available.
- Lead time ambiguity resolved via lead_time_canonical.

## Limitations & Next Steps
- No time dimension limits trend analysis and forecasting.
- Carrier/route scenario results are observational, not causal.
