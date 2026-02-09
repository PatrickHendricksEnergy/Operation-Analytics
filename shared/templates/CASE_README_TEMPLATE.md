# Case: {{case_name}}

## Overview
- Business question(s):
- Audience:
- Decision impact:

## Data
- Source file: `{{source_file}}`
- Rows/columns: {{rows}} / {{columns}}
- Time coverage (if applicable): {{time_coverage}}

## Approach
- Ingest + cleaning
- KPI calculations
- Modeling/forecasting (if applicable)
- BI exports (star schema + flat)

## BI Model
- Fact grain: {{fact_grain}}
- Measures: {{measures}}
- Dimensions: {{dimensions}}
- Join keys: {{join_keys}}

## Exports
- `exports/bi_fact_{{case_slug}}.csv` + `.parquet`
- `exports/dim_*.csv` + `.parquet`
- `exports/flat_{{case_slug}}_pivot_ready.csv`
- `exports/data_dictionary.csv`
- `exports/star_schema.md`

## Notebooks
- `notebooks/01_eda.ipynb`
- `notebooks/02_modeling_forecast.ipynb`
- `notebooks/03_executive_dashboard.ipynb`

## Reports
- `reports/EXEC_SUMMARY.md`
- `reports/BI_Quickstart.md`
- `reports/measures.md`
- `reports/figures/`

## How To Run
```bash
python -m shared.src.run_case --case {{case_slug}}
```

## Methods & Assumptions
- {{methods}}

## Limitations & Next Steps
- {{limitations}}
