# Supply Chain Analytics & Optimization (End-to-End Case Study)

## One-liner
A decision-focused analytics project that links demand, inventory, supplier performance, logistics, and quality to reduce stockouts, lower carrying costs, and improve service levels.

## Business Problem
Manufacturing and distribution operations face stockouts, excess inventory, long lead times, and avoidable logistics/quality costs. This project identifies root causes and prioritizes actions.

## Dataset
Includes product/SKU, price, availability, units sold, revenue, stock levels, lead times, order quantities, shipping time and shipping cost per order (SKU batch), carrier, suppliers, manufacturing cost/lead time, inspection and defect rates, transportation modes/routes.

## Key Questions
- Which SKUs drive revenue but are at stockout risk?
- Where are we holding excess inventory with low demand?
- Which suppliers create the most lead-time risk or quality cost?
- What carrier/mode/route combinations are high cost without speed benefit?
- Which defects drive most quality loss (Pareto)?

## Approach
- Data quality + standardization (SKU, supplier, lead time fields)
- Demand & revenue segmentation
- Inventory: ABC + turnover + stockout risk flags
- Supplier scorecard: cost/quality/delivery and risk matrix
- Logistics: cost vs speed trade-offs by carrier/mode/route
- Quality: defect Pareto + cost impact
- Recommendations: prioritized actions + expected impact

## Key Insights (placeholders)
- A small share of SKUs generates most revenue; several are understocked → stockout risk.
- A large set of C-items ties up stock with slow turnover → working capital opportunity.
- Supplier X and Y show higher lead time + defect rates → reliability risk concentration.
- Certain routes/modes cost more without faster delivery → optimization potential.
- Top defect sources explain the majority of quality issues → focused improvement ROI.

## Deliverables
- Executive KPI dashboard
- ABC classification + inventory policy recommendations
- Supplier risk matrix + scorecard
- Logistics optimization findings
- Defect Pareto + quality action plan
- Final prioritized roadmap

## How To Run
```bash
pip install -r requirements.txt
python -m cases.supply-chain-analysis.src.pipeline --input data/raw/supply_chain_data.csv --out reports --exports data/processed --visuals visuals
```

## Project Outputs
![Executive KPI Dashboard](visuals/kpi_dashboard.png)
![Revenue vs Availability (Stockout Risk)](visuals/stockout_risk_scatter.png)
![Revenue by Price Band](visuals/price_vs_revenue.png)
![Revenue by Product Type](visuals/revenue_by_product_type.png)
![ABC Value Curve](visuals/abc_value_curve.png)
![Inventory Turnover by SKU](visuals/inventory_turnover_by_sku.png)
![Unit Margin Proxy by Product Type](visuals/margin_proxy_distribution.png)
![Pareto Revenue by Supplier](visuals/pareto_revenue_by_supplier.png)
![Supplier Risk Matrix](visuals/supplier_risk_matrix.png)
![Lead Time Breakdown by Supplier](visuals/lead_time_breakdown_by_supplier.png)
![Logistics Cost vs Time](visuals/logistics_cost_vs_time.png)
![Cost per Order by Carrier and Route](visuals/cost_to_serve_by_carrier_route.png)
![Shipping Cost Distribution by Transportation Mode](visuals/costs_by_transportation_mode.png)
![Defect Cost Pareto](visuals/defect_pareto.png)
![Defect Rate by Supplier](visuals/defect_rate_by_supplier.png)
![Defect Rate Heatmap](visuals/defect_rate_heatmap.png)
![Defect Rate by Supplier (Lollipop)](visuals/defect_rate_by_supplier_lollipop.png)

## Author
Patrick Hendricks | Supply Chain & Data Analytics
