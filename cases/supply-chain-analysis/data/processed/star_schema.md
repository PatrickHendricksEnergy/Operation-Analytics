# Star Schema — Supply Chain

## Fact Grain
One row per SKU/location/supplier record

## Dimensions
- dim_product (product_key, sku, product_type)
- dim_supplier (supplier_key, supplier_name)
- dim_location (location_key, location)
- dim_carrier (carrier_key, shipping_carriers)
- dim_route (route_key, routes)
- dim_mode (mode_key, transportation_modes)

## Relationships
- fact_supply_chain.product_key -> dim_product.product_key
- fact_supply_chain.supplier_key -> dim_supplier.supplier_key
- fact_supply_chain.location_key -> dim_location.location_key
- fact_supply_chain.carrier_key -> dim_carrier.carrier_key
- fact_supply_chain.route_key -> dim_route.route_key
- fact_supply_chain.mode_key -> dim_mode.mode_key