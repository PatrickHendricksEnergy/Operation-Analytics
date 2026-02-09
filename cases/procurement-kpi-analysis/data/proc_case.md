You are an AI agent working in this repository:
Operation Analytics/operation-analytics

and this is the case:

This dataset captures procurement operations for a global enterprise, anonymized to protect company and supplier identities. It includes 700 real-world purchase orders from 2022–2023, reflecting challenges like supplier delays, compliance gaps, and defects. Ideal for analyzing supply chain efficiency, cost optimization, and vendor performance.

Key Features:

Supplier Diversity: 5 suppliers with varying reliability and compliance rates.
Real-World Complexity: Missing delivery dates, partial orders, and outliers.
Price Trends: Reflects inflationary pressures over time.
Actionable KPIs: Built-in metrics for cost savings, defect rates, and on-time delivery.


Use Cases:

Supplier Risk Analysis: Identify high-risk vendors (e.g., frequent defects or delays).
Cost Optimization: Quantify savings from price negotiations.
Compliance Audits: Investigate policy violations and their root causes.
Trend Forecasting: Analyze price changes over time.

FOCUS CASE
/cases/procurement-kpi-analysis
Primary dataset:
Procurement KPI Analysis Dataset.csv

STEP 1 — UNDERSTAND THE DATA (NO ASSUMPTIONS)
Columns to analyze:
PO_ID, Supplier, Order_Date, Delivery_Date, Item_Category, Order_Status,
Quantity, Unit_Price, Negotiated_Price, Defective_Units, Compliance

Actions:
- Parse dates correctly
- Treat missing Defective_Units explicitly (document assumption: 0 vs unknown)
- Standardize column names to snake_case
- Validate quantities, prices, negative or illogical values
- Produce a data_dictionary.csv (% missing, type, description)

STEP 2 — CREATE EXECUTIVE-CRITICAL KPIs
Create derived metrics:
- gross_po_value = quantity * unit_price
- negotiated_po_value = quantity * negotiated_price
- realized_savings = gross_po_value - negotiated_po_value
- savings_rate_pct = realized_savings / gross_po_value
- defect_rate_pct = defective_units / quantity
- defective_cost_exposure = defective_units * negotiated_price
- procurement_lead_time_days = delivery_date - order_date
- non_compliant_flag = compliance == "No"
- spend_at_risk = negotiated_po_value where non_compliant_flag is true

STEP 3 — PERFORMANCE & RISK ANALYSIS
Analyze and visualize:
- Savings effectiveness by supplier and category
- Defect cost exposure vs savings (identify “false savings”)
- Lead time distribution and late delivery risk
- Order_Status impact (Cancelled, Pending, Partial)
- Compliance vs spend concentration
- Supplier risk score combining:
  - non_compliance
  - defect_rate
  - lead_time
  - order_status risk

STEP 4 — ADVANCED INSIGHTS (NO FORECASTING)
Build:
- Supplier segmentation (Strategic / Cost Trap / Operational Risk / Governance Risk)
- Pareto analysis (top 20% suppliers driving 80% of risk or savings)
- Scenario insights:
  - “If non-compliant suppliers were eliminated, % spend affected”
  - “If defect rate reduced by 25%, estimated savings unlocked”
Only compute scenarios if supported by data; otherwise state limitation.

STEP 5 — EXECUTIVE OUTPUTS
Create in /cases/
