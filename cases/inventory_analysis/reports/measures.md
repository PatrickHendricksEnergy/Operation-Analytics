# Power BI Measures (DAX)

- m_total_sales = SUM(fact_inventory[sales_dollars])
- m_total_purchases = SUM(fact_inventory[purchase_dollars])
- m_avg_inventory_value = AVERAGE(fact_inventory[avg_inventory_value])
- m_inventory_turnover = DIVIDE([m_total_sales], [m_avg_inventory_value])
- m_carrying_cost = SUM(fact_inventory[carrying_cost])