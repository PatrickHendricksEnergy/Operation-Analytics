# Assumptions Log — inventory_analysis

- Raw materials are identified by the Description field (material_description).
- Items with sales are classified as finished goods; items with purchases but no sales are classified as raw materials; remaining items are treated as WIP.
- EOQ uses average invoice freight as an ordering cost proxy.
- Carrying cost rate assumed at 20% of average inventory value.
- Lead time is rounded up to whole days; negative lead times are excluded.