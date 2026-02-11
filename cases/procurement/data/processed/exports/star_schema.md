# Star Schema: bi_fact_procurement_kpi_analysis

## Fact Grain
One row per purchase order line

## Dimensions
- dim_date (date_key)
- dim_supplier (supplier_key)
- dim_item_category (item_category_key)
- dim_order_status (order_status_key)
- dim_compliance (compliance_key)

## Relationships
- bi_fact_procurement_kpi_analysis.order_date_key -> dim_date.date_key
- bi_fact_procurement_kpi_analysis.delivery_date_key -> dim_date.date_key
- bi_fact_procurement_kpi_analysis.supplier_key -> dim_supplier.supplier_key
- bi_fact_procurement_kpi_analysis.item_category_key -> dim_item_category.item_category_key
- bi_fact_procurement_kpi_analysis.order_status_key -> dim_order_status.order_status_key
- bi_fact_procurement_kpi_analysis.compliance_key -> dim_compliance.compliance_key