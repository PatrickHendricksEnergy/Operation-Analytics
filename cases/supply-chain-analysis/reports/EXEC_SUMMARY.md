# Executive Summary — supply-chain-analysis

## Headline Findings
- Total revenue is 577,604.82 with total cost proxy 2,776,344.63.
- Top product type by revenue is skincare and top supplier is Supplier 1.
- Average defect rate is 2.28%.

## Recommended Actions (Ranked by Impact/Effort)
- 1) Optimize carrier/route combinations with the highest logistics cost per unit.
- 2) Prioritize quality improvement for suppliers driving the largest defect cost risk.
- 3) Rebalance inventory for SKUs with high demand signals but low stock cover.

## Watchlist
- Top SKUs to monitor: SKU37; SKU4; SKU67; SKU36; SKU9

## Top Controllable Levers
- availability
- stock levels
- price
- order quantities
- transportation modes: Sea

## Methods & Assumptions
- Columns standardized to snake_case. Lead time ambiguity resolved via lead_time_canonical. Derived cost and margin proxies computed from provided fields.

## Limitations & Next Steps
- No time column in dataset, so trend analysis and forecasting are not included.
- Cost proxies assume manufacturing_costs scale with production volumes where available.
