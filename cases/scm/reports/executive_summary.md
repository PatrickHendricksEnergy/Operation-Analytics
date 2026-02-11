# Executive Summary — Supply Chain Analytics & Optimization

## Executive Snapshot
- Coverage: 100 SKUs, 3 product types, 5 suppliers, 3 carriers, 4 transportation modes.
- Total revenue: $577.6K. Total cost proxy (manufacturing + logistics): $2.78M.
- Service level (availability): 48.4%.
- Inventory turnover (median revenue ÷ inventory value proxy): 3.38.
- Avg lead time: 17.1 days (P90 28 days, CV 52%).
- Cost per unit (proxy): $156.88.
- Defect rate: 2.28%.
- On-time delivery proxy: 86.0%.

## Headline Findings
- Revenue concentration is high: A items (60 SKUs) generate 80.5% of revenue; B adds 14.7%; C contributes 4.8%.
- Supplier concentration is material: Supplier 1 contributes 27.3% of revenue and Supplier 2 adds 21.7%; the remaining suppliers contribute 51.0%.
- Stockout risk is concentrated: revenue P75 ≥ $8.25K and availability P25 ≤ 22.8% flag SKU67, SKU52, SKU99, SKU60, and SKU64 as critical.
- Overstock risk is visible: SKU45, SKU48, SKU49, SKU97, and SKU89 have the weakest turnover (0.26–1.49).
- Lead time risk is supplier-driven: Supplier 5 (22.6 days) and Supplier 2 (21.1 days) have the highest total lead time, dominated by manufacturing time.
- Logistics trade-off is weak: shipping time vs cost correlation is ~0.05. Road is fastest and low cost, while Air and Rail are higher cost without a speed advantage over Road.
- Quality risk is concentrated: Supplier 2 in Delhi shows the highest defect hotspot (3.34%), and the top 4 suppliers account for ~85.9% of defect cost risk.
- Margin proxy is negative across categories; Haircare shows the widest dispersion, indicating the largest pricing or cost inconsistency.

## Priority Actions (Ranked)
1. Protect A-class SKUs and top stockout-risk SKUs with higher ROP and safety stock.
2. Reduce capital tied in low-turnover SKUs via order-quantity resets and SKU rationalization.
3. Launch supplier improvement plans for Supplier 2, 3, and 5 focused on manufacturing lead time and defect reduction.
4. Shift non-critical lanes from Air and Rail to Road or Sea where service impact is minimal.
5. Focus quality mitigation on the top 4 defect-cost suppliers and the Supplier 2–Delhi hotspot.

**Supporting Figures (All Charts)**

**Executive KPI Dashboard**
![Executive KPI Dashboard](figures/kpi_dashboard.png)
Insight: Service level is 48.4% with 86.0% on-time delivery; lead time P90 is 28 days and CV is 52%. Cost per unit is $156.88 and defect rate is 2.28%.
Recommendation: Use these KPI baselines as operational targets; prioritize service-level recovery and lead-time variability reduction.

**ABC Value Curve (Cumulative Revenue)**
![ABC Value Curve](figures/abc_value_curve.png)
Insight: A items (60 SKUs) drive 80.5% of revenue; B adds 14.7%; C contributes 4.8%.
Recommendation: Protect A items with tighter control policies and re-evaluate or bundle C items to reduce carrying cost.

**Pareto: Revenue by Supplier Tier**
![Pareto Revenue by Supplier](figures/pareto_revenue_by_supplier.png)
Insight: Supplier 1 contributes 27.3% of revenue, Supplier 2 contributes 21.7%, and the long-tail contributes 51.0%.
Recommendation: Secure capacity and reliability for the top two suppliers and consolidate long-tail sourcing where possible.

**Revenue by Price Band**
![Revenue by Price Band](figures/price_vs_revenue.png)
Insight: The $0–10 band contributes the highest revenue at ~$81.6K, indicating volume-led contribution in low price points.
Recommendation: Protect availability and margin for the top price band through cost-to-serve control and demand planning.

**Revenue by Product Type**
![Revenue by Product Type](figures/revenue_by_product_type.png)
Insight: Skincare drives 41.8% of revenue ($241.6K), followed by Haircare at 30.2% ($174.5K) and Cosmetics at 28.0% ($161.5K).
Recommendation: Prioritize service levels and forecasting accuracy in Skincare to protect the largest revenue pool.

**Revenue vs Availability (Stockout Risk)**
![Revenue vs Availability](figures/stockout_risk_scatter.png)
Insight: High-risk SKUs are identified where revenue ≥ $8.25K and availability ≤ 22.8%; top risk SKUs are SKU67, SKU52, SKU99, SKU60, and SKU64.
Recommendation: Elevate safety stock and expedite replenishment for these SKUs immediately.

**Inventory Turnover by SKU**
![Inventory Turnover by SKU](figures/inventory_turnover_by_sku.png)
Insight: Lowest turnover SKUs include SKU45 (0.26), SKU48 (0.97), SKU49 (1.02), SKU97 (1.35), and SKU89 (1.49).
Recommendation: Reduce order quantities, clear slow movers, and reassess demand for these SKUs.

**Logistics Cost vs Time by Transportation Mode**
![Logistics Cost vs Time](figures/logistics_cost_vs_time.png)
Insight: Median shipping cost and time are Road $4.95 / 4 days, Sea $4.86 / 8 days, Air $6.27 / 5 days, Rail $6.38 / 7 days.
Recommendation: Shift non-critical lanes from Air and Rail to Road or Sea to reduce cost without a service penalty.

**Shipping Cost Variability by Transport Mode**
![Shipping Cost Variability](figures/costs_by_transportation_mode.png)
Insight: Air and Rail have the largest cost variability (IQR $4.89 and $4.38), while Sea and Road are more stable.
Recommendation: Tighten carrier contracts and lane governance on Air and Rail to reduce volatility.

**Cost per Order by Carrier and Route**
![Cost per Order by Carrier and Route](figures/cost_to_serve_by_carrier_route.png)
Insight: Carrier B on Route B is lowest cost at ~$1.47 per order, while Carrier C on Route B is highest at ~$10.04 per order.
Recommendation: Renegotiate or reroute away from the highest-cost carrier-route pair and expand usage of the lowest-cost pairing.

**Lead Time Breakdown by Supplier**
![Lead Time Breakdown by Supplier](figures/lead_time_breakdown_by_supplier.png)
Insight: Supplier 5 totals 22.6 days (16.3 manufacturing + 6.2 shipping) and Supplier 2 totals 21.1 days (15.6 + 5.5).
Recommendation: Focus supplier improvement plans on manufacturing lead time reductions for Suppliers 5 and 2.

**Supplier Risk Matrix**
![Supplier Risk Matrix](figures/supplier_risk_matrix.png)
Insight: High-risk suppliers above median lead time and defect rate are Suppliers 2, 5, and 3; Supplier 2 has the largest exposure (~$616K).
Recommendation: Prioritize corrective action plans and dual-sourcing for these high-risk suppliers.

**Supplier Quality Performance vs Target**
![Supplier Quality Performance vs Target](figures/defect_rate_by_supplier.png)
Insight: Target defect rate is 2%; Suppliers 2–5 exceed this target, with Supplier 5 highest at 2.67%.
Recommendation: Launch corrective action plans starting with Supplier 5 and enforce tighter quality gates on inbound lots.

**Defect Rate Heatmap (Supplier × Location)**
![Defect Rate Heatmap](figures/defect_rate_heatmap.png)
Insight: The highest defect hotspot is Supplier 2 in Delhi at ~3.34%.
Recommendation: Audit this supplier-location lane and implement process control and inspection upgrades.

**Supplier Concentration of Defect Cost Risk**
![Supplier Concentration of Defect Cost Risk](figures/defect_pareto.png)
Insight: The top 4 suppliers account for ~85.9% of defect cost risk.
Recommendation: Focus defect mitigation on these suppliers for the fastest financial impact.

**Unit Margin Proxy by Product Type**
![Unit Margin Proxy by Product Type](figures/margin_proxy_distribution.png)
Insight: All categories have negative median margin; Haircare shows the widest dispersion (largest IQR), indicating inconsistent pricing or cost-to-serve.
Recommendation: Reprice or reduce cost-to-serve for Haircare SKUs, then apply learnings to Cosmetics and Skincare.

## Caveats
- No time column is present, so results are cross-sectional rather than time-based trends.
- Inventory turnover is a proxy based on revenue and inventory value, not a time-indexed turnover measure.
- Cost per unit and defect cost are proxies derived from available fields.
- Shipping cost represents the cost to ship one order (or one SKU batch) via the selected mode.
