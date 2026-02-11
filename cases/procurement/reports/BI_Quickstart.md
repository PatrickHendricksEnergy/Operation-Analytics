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