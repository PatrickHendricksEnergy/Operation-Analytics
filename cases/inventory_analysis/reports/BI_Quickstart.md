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