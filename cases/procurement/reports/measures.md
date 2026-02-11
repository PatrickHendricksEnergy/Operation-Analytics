# Power BI Measures (DAX)

- m_total_negotiated_spend = SUM(bi_fact_procurement_kpi_analysis[negotiated_po_value])
- m_total_savings = SUM(bi_fact_procurement_kpi_analysis[realized_savings])
- m_savings_rate = DIVIDE([m_total_savings], SUM(bi_fact_procurement_kpi_analysis[gross_po_value]))
- m_defect_rate = DIVIDE(SUM(bi_fact_procurement_kpi_analysis[defective_units_filled]), SUM(bi_fact_procurement_kpi_analysis[quantity]))
- m_spend_at_risk = SUM(bi_fact_procurement_kpi_analysis[spend_at_risk])