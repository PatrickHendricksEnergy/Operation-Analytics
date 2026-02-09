# Case: inventory_analysis

## Overview
- Business question(s): How can inventory levels be optimized to reduce stockouts, excess inventory, and carrying costs?
- Audience: Operations, supply chain, and finance leadership.
- Decision impact: EOQ, reorder points, and procurement/production process changes.

## Data
- Source files: `Inventory Analysis data set/*.csv`
- Key datasets: sales, purchases, beginning/ending inventory, invoices
- Large raw files are excluded from GitHub. Use the sample data in `data_sample/` or supply the full dataset locally.

## Approach
- Ingest + cleaning (dates and numeric checks)
- Demand analysis and ABC classification
- EOQ + reorder point calculations
- Inventory turnover and carrying cost analysis
- BI exports (star schema + flat)

## BI Model
- Fact grain: One row per inventory_id + store
- Measures: sales_dollars, purchase_dollars, avg_inventory_value, inventory_turnover, carrying_cost
- Dimensions: dim_product, dim_vendor, dim_store
- Join keys: inventory_id, vendor_number, store

## Exports
- `exports/fact_inventory.csv` + `.parquet`
- `exports/dim_product.csv`, `exports/dim_vendor.csv`, `exports/dim_store.csv`
- `exports/flat_inventory_pivot_ready.csv`
- `exports/data_dictionary.csv`
- `exports/star_schema.md`
- `exports/abc_classification.csv`
- `exports/forecast_inventory_sales.csv`

## Reports
- `reports/EXEC_SUMMARY.md`
- `reports/BI_Quickstart.md`
- `reports/measures.md`
- `reports/figures/`

## How To Run
```bash
python -m cases.inventory_analysis.src.pipeline --input "Inventory Analysis data set" --out reports --exports exports
python -m cases.inventory_analysis.src.pipeline --input "data_sample" --out reports --exports exports
```

## Methods & Assumptions
- Carrying cost rate assumed at 20% of average inventory value.
- Lead time computed from PODate to ReceivingDate.

## Limitations & Next Steps
- Service level targets are not provided; safety stock not modeled.
- Ordering cost is approximated using average invoice freight.
