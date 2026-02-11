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
