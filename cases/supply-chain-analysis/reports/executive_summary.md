# Executive Summary — Supply Chain Analytics & Optimization

## Executive Snapshot
- Coverage: 100 SKUs, 3 product types, 5 suppliers, 3 carriers, 4 transportation modes.
- Total revenue: $577.6K. Total cost proxy (manufacturing + logistics): $2.78M.
- Service level (availability): 48.4%.
- Inventory turnover (median sold/stock proxy): 8.69.
- Avg lead time: 17.1 days (P90 28 days, CV 52%).
- Cost per unit (proxy): $156.88.
- Defect rate: 2.28%.
- On-time delivery proxy: 86.0%.

## Headline Findings
- Revenue concentration: 59 A-class SKUs generate ~79.6% of revenue (ABC curve).
- ~60% of SKUs generate ~80% of revenue, so tight control of A-items is critical.
- Stockout risk: SKU67, SKU52, SKU60 combine high revenue with very low availability.
- Overstock/low-turnover: SKU45, SKU48, SKU49, SKU97, SKU89 show the weakest turnover ratios.
- Supplier risk concentration: Supplier 3 and Supplier 5 show the highest combined lead time + defect risk; Supplier 4 and Supplier 2 drive the largest defect cost risk.
- Logistics trade-off: Cost vs speed correlation is weak (r≈0.05). Air is fastest but highest cost; Sea is cheapest but slowest.
- Quality impact: Haircare has the highest defect rate, while skincare drives the largest defect cost risk due to spend concentration.

## KPI Dashboard
![Executive KPI Dashboard](../visuals/kpi_dashboard.png)

## Priority Actions (Ranked)
1. Protect A-class and stockout-risk SKUs with higher reorder points and safety stock.
2. Reduce capital tied up in low-turnover SKUs and align order quantities to demand.
3. Engage Supplier 3/5 on lead-time and quality improvement; prioritize Supplier 4/2 quality audits based on defect cost risk.
4. Rebalance transportation modes to reduce cost where service impact is low (Air → Road/Sea on non-critical lanes).
5. Focus defect reduction on haircare and top defect-cost suppliers using Pareto priorities.

## Caveats
- No time column is present, so results are cross-sectional (no trend/seasonality).
- Inventory turnover is a proxy (units sold ÷ stock level), not a time-based turnover.
- Cost per unit and defect cost are proxies derived from available fields.
- Shipping cost represents the cost to ship one order (or one SKU batch).
