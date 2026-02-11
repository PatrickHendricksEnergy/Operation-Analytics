# Executive Summary — procurement-kpi-analysis

## Headline Findings
- Dataset covers 777 purchase orders across 5 suppliers (Order_Date 2022-01-01 to 2024-01-01); Delivery_Date through 2024-01-12.
- Total negotiated spend is 45,373,696.39 with realized savings 3,931,126.47.
- Average savings rate is 7.97% and average defect rate 5.78%.
- Spend at risk from non-compliance is 6,986,051.38.
- Late delivery rate (p75 threshold 16.0 days) is 18.02%.
- Top 20% of suppliers account for ~22.6% of realized savings.

## Figure Insights & Recommendations (All Charts)
1. `order_value_by_supplier.png` — The top 3 suppliers (Beta_Supplies $9.86M, Epsilon_Group $9.85M, Delta_Logistics $9.24M) represent 63.8% of total spend. Recommendation: lock annual pricing + SLAs with these three, and require quarterly business reviews tied to delivery and defect KPIs.
2. `order_value_trend_monthly.png` — Peak spend occurred in March 2023 at ~$2.74M. Recommendation: pre‑negotiate pricing and capacity in Q1, and pre‑approve sourcing runs ahead of March to avoid rush premiums.
3. `savings_by_supplier.png` — Savings are concentrated in Beta_Supplies ($0.89M), Epsilon_Group ($0.85M), and Delta_Logistics ($0.78M). Recommendation: codify and replicate the deal structures from these suppliers across Alpha_Inc and Gamma_Co.
4. `savings_by_category.png` — Highest savings come from MRO ($0.90M), Office Supplies ($0.84M), and Electronics ($0.74M). Recommendation: run the next sourcing wave exclusively on these three categories to maximize ROI.
5. `pareto_savings.png` — The top 20% of suppliers (1 supplier) account for 22.6% of savings. Recommendation: shift strategic sourcing bandwidth to the top two suppliers and aim to raise the top‑tier savings share above 35%.
6. `defect_cost_vs_savings.png` — Delta_Logistics and Beta_Supplies sit in the “False Savings” quadrant (high savings + high defect exposure: Delta $1.03M, Beta $0.76M). Recommendation: tie rebates to defect reduction or re‑bid portions of their spend. Gamma_Co sits in “Replace/Exit.” Recommendation: reassign Gamma_Co volume to lower‑defect suppliers.
7. `lead_time_distribution.png` — Median lead times are highest in MRO (12 days) and Electronics/Packaging (11 days). Recommendation: set category‑specific lead‑time SLAs (MRO ≤10 days; Electronics ≤9 days) and add safety stock where SLA gaps persist.
8. `lead_time_heatmap.png` — Worst supplier‑category pairs are Delta_Logistics × MRO (13.3 days), Beta_Supplies × Raw Materials (11.9), and Epsilon_Group × Office Supplies (11.9). Recommendation: create targeted improvement plans for these three lanes with 30‑day milestones.
9. `avg_delivery_lag_by_supplier.png` — All suppliers exceed the 10‑day benchmark (Beta 11.27, Epsilon 10.87, Delta 10.85, Alpha 10.74, Gamma 10.19). Recommendation: apply SLA penalties for suppliers above 10 days and approve expedited lanes for the top 2 spend suppliers until lag drops below target.
10. `order_status_distribution.png` — 27.9% of orders are not fully delivered (Pending 10.4%, Partially Delivered 9.4%, Cancelled 8.1%). Recommendation: implement a weekly exception review for non‑delivered POs and set a target to cut cancellations below 5%.
11. `order_status_impact.png` — $12.97M (28.6%) of spend is tied up in non‑delivered statuses: Pending $5.31M, Partially Delivered $4.07M, Cancelled $3.59M. Recommendation: escalate top 20 pending POs by value and resolve within 14 days.
12. `compliance_spend.png` — Non‑compliant spend totals $6.99M (15.4%). Recommendation: require pre‑approval for any non‑compliant PO and enforce supplier onboarding before issuing new POs.
13. `supplier_risk_score.png` — Highest risk scores are Delta_Logistics (0.90) and Beta_Supplies (0.76). Recommendation: launch 90‑day risk remediation plans for these two, with monthly check‑ins and KPI penalties.
14. `supplier_risk_matrix.png` — High‑risk suppliers by spend‑at‑risk + defect rate are Delta_Logistics (10.9% defects; $18.6k spend‑at‑risk), Beta_Supplies (8.3%; $11.0k), and Gamma_Co (4.5%; $10.1k). Recommendation: reallocate 10–20% of volume away from these suppliers until defect rates fall below 5%.

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
