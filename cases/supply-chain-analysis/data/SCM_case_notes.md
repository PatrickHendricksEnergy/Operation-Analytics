You are an AI agent working in this repo: Operation Analytics/operation-analytics.

CONTEXT
We are analyzing a supply-chain dataset with these columns (focus on them exactly):
Product type, SKU, Price, Availability, Number of products sold, Revenue generated,
Customer demographics, Stock levels, Lead times, Order quantities, Shipping times,
Shipping carriers, Shipping costs, Supplier name, Location, Lead time,
Production volumes, Manufacturing lead time, Manufacturing costs,
Inspection results, Defect rates, Transportation modes, Routes, Costs.

IMPORTANT: There is both "Lead times" and "Lead time" — treat this as a duplicate/ambiguity.
Detect whether both exist; if both do, document the difference (or merge safely) and keep a final canonical column name.

SAFETY + TRANSPARENCY
- Never read, print, or expose .env or any secret tokens/keys.
- Do not fabricate values. Compute everything from the CSV.
- Every output must have a “Methods & Assumptions” and “Limitations & Next Steps”.

WHAT TO BUILD (EXECUTIVE-FRIENDLY + ADVANCED ANALYTICS)
Target case folder: /cases/supply-chain-analysis/
Assume the CSV is /cases/supply-chain-analysis/supply_chain_data.csv (if file name differs, auto-detect from the case root).

1) Data quality & semantics
- Validate schema, datatypes, missingness, duplicates, outliers.
- Standardize column names to snake_case.
- Create a data dictionary table with: column, inferred_type, %missing, min/max (numeric), top categories (categorical).
- Create derived metrics:
  - unit_margin_proxy = (Revenue generated / Number of products sold) - Price  (guard against zero sold)
  - demand_signal = Number of products sold / max(Availability, 1)
  - stock_cover_proxy = Stock levels / max(Number of products sold, 1)
  - total_logistics_cost = Shipping costs + Costs (if Costs is transport/route cost)
  - total_manufacturing_cost = Manufacturing costs (and include production volume effects)
  - total_cost_proxy = total_logistics_cost + total_manufacturing_cost
  - defect_cost_risk_proxy = Defect rates * total_cost_proxy
- Detect suspicious records: negative/zero where illogical, extreme costs, lead time mismatches.

2) Executive KPIs & insights (decision-oriented)
Compute and visualize:
- Revenue and sold units by Product type, Supplier, Location, Carrier, Route, Transport mode.
- Cost-to-serve: total_logistics_cost per unit and per revenue segment.
- Stock health: items at risk (low stock_cover_proxy + high demand_signal).
- Lead time performance: shipping_times vs manufacturing_lead_time vs lead_time (and variance by supplier/carrier/route).
- Quality: inspection_results and defect_rates — map hotspots by supplier/location/mode/route.
- Profitability proxy: unit_margin_proxy distributions and drivers.

3) Advanced modeling (no time column assumed)
Build driver models to explain outcomes + recommend actions:
A) Regression model: predict Revenue generated (or Number of products sold) using:
   product_type, price, availability, stock_levels, order_quantities, lead_times, shipping_times,
   carrier, route, transport_mode, supplier, location, manufacturing_costs, defect_rates, inspection_results.
B) Classification model: risk of inspection failure (Inspection results == "Fail") and/or high defects (defect_rates above p75).
- Use a robust preprocessing pipeline (OneHotEncode categoricals, scale numerics if needed).
- Use train/validation split with stratification for classification.
- Provide feature importance and partial dependence (or SHAP if available).
- Output “Top controllable levers” for decision makers (e.g., carrier/route changes, supplier changes, pricing, order quantity tuning).

4) Segmentation & scenario analysis
- Segment SKUs into quadrants:
  - High demand_signal vs low demand_signal
  - High total_cost_proxy vs low total_cost_proxy
  - High defect risk vs low defect risk
- Produce scenario tables:
  - “If we move Carrier B → Carrier A for similar lanes, expected shipping cost/lead time change”
  - “If we reduce defect rates by 25% for top 3 suppliers, estimated cost-risk reduction”
  (Only do if data supports comparisons; otherwise state insufficient evidence.)

5) Executive report + BI outputs
Create these outputs under /cases/supply-chain-analysis/:

A) /reports/EXEC_SUMMARY.md (executive tone)
- 3–5 headline findings with numbers
- 3 recommended actions (ranked by impact/effort)
- “Watchlist” (top SKUs/suppliers/routes to monitor)
- Methods & Assumptions
- Limitations & Next Steps

B) /reports/figures/*.png
Minimum charts:
- Pareto of revenue by supplier
- Cost-to-serve by carrier/route
- Lead time breakdown (manufacturing vs shipping) by supplier
- Defect rate heatmap by supplier x location (or mode/route)
- Margin proxy distribution by product type

C) /exports/ (Excel/Power BI/Tableau friendly)
- fact_supply_chain.csv + .parquet (one row per SKU, or per SKU+supplier+route if appropriate)
- dim_supplier.csv, dim_product.csv, dim_location.csv, dim_carrier.csv, dim_route.csv, dim_mode.csv
- flat_supply_chain_pivot_ready.csv (denormalized for Excel pivots)
- data_dictionary.csv
- star_schema.md explaining keys and grain

D) /notebooks/
- 01_eda.ipynb
- 02_driver_models.ipynb
- 03_executive_dashboard.ipynb (loads exports + renders key visuals)

E) /src/ (production-quality modules)
- pipeline.py (single entry point)
- data_loading.py, cleaning.py, features.py, kpis.py, modeling.py, viz.py, bi_model.py

6) Runner command
Add a runnable command in the case README:
- python -m cases.supply-chain-analysis.src.pipeline --input <csv> --out reports --exports exports

STYLE
- Keep everything executive-friendly, concise, and visually clean.
- Use consistent naming, docstrings, type hints, and minimal dependencies.

NOW EXECUTE
Scan the case directory, load the CSV, infer schema, implement the pipeline/modules, generate exports, notebooks, charts, and the EXEC_SUMMARY.md. Ensure no secrets are exposed and outputs are reproducible.
