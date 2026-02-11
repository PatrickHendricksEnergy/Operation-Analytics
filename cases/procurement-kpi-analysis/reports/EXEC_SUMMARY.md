# Executive Summary — procurement-kpi-analysis

## Headline Findings
- Dataset covers 777 purchase orders across 5 suppliers (Order_Date 2022-01-01 to 2024-01-01); Delivery_Date through 2024-01-12.
- Total negotiated spend is 45,373,696.39 with realized savings 3,931,126.47.
- Average savings rate is 7.97% and average defect rate 5.78%.
- Spend at risk from non-compliance is 6,986,051.38.
- Late delivery rate (p75 threshold 16.0 days) is 18.02%.
- Top 20% of suppliers account for ~22.6% of realized savings.

## Recommended Actions (Ranked by Impact/Effort)
- 1) Prioritize supplier remediation where spend at risk and defect exposure intersect.
- 2) Negotiate category-level pricing for suppliers with low savings rates and high defect costs.
- 3) Tighten governance for non-compliant suppliers with high order volumes.

## Watchlist
- Top suppliers to monitor: Delta_Logistics, Beta_Supplies, Epsilon_Group, Gamma_Co, Alpha_Inc

## Scenario Insights
- Eliminating non-compliant suppliers impacts 15.40% of negotiated spend.
- Reducing defect rate by 25% unlocks ~641,999.18 in defect-cost exposure.

## Methods & Assumptions
- Missing Defective_Units are treated as 0 for defect rate calculations and flagged via defective_units_missing.
- All metrics computed from provided fields; no forecasting is performed.
- Delivery lag chart includes a 10-day benchmark line for SLA context.

## Limitations & Next Steps
- Missing delivery dates on 11.20% of orders limit lead time analysis.
- Supplier risk score is a composite index, not a causal model.
