# Star Schema: fact_inventory

## Fact Grain
One row per inventory_id + store

## Dimensions
- dim_product (inventory_id)
- dim_vendor (vendor_number)
- dim_store (store)

## Relationships
- fact_inventory.inventory_id -> dim_product.inventory_id
- fact_inventory.vendor_number -> dim_vendor.vendor_number
- fact_inventory.store -> dim_store.store