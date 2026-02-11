# Power BI Measures (DAX)

- m_total_revenue = SUM(fact_supply_chain[revenue_generated])
- m_total_cost_proxy = SUM(fact_supply_chain[total_cost_proxy])
- m_gross_margin_proxy = [m_total_revenue] - [m_total_cost_proxy]
- m_avg_defect_rate = AVERAGE(fact_supply_chain[defect_rate_scaled])
- m_logistics_cost_per_unit = AVERAGE(fact_supply_chain[logistics_cost_per_unit])