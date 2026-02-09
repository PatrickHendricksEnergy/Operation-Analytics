# Executive Summary — inventory_analysis

## Headline Findings
- Total sales are 32,843,306.74 with total purchases 313,511,502.07.
- Average inventory value is 73,879,315.65 with average turnover 0.83.
- Estimated annual carrying cost is 14,775,863.13.
- Items flagged for stockout risk: 5641.

## Recommended Actions (Ranked by Impact/Effort)
- 1) Prioritize A-class items with low stock cover and high lead times for tighter replenishment.
- 2) Reduce excess inventory for low-turnover items through reorder point and EOQ tuning.
- 3) Align procurement lead times with demand variability to reduce stockouts and carrying costs.

## Watchlist
- High-risk items: 38_GOULCREST_3045, 11_CARDEND_6552, 50_MOUNTMEND_25021, 10_HORNSEY_6593, 73_DONCASTER_19376, 64_CESTERFIELD_8475, 19_WINTERVALE_36874, 73_DONCASTER_19392, 15_WANBORNE_44943, 57_LANTEGLOS_3608

## Charts Included
- abc_distribution.png
- monthly_sales_trend.png
- lead_time_distribution.png
- inventory_turnover_top.png

## Methods & Assumptions
- Carrying cost rate assumed at 20% of average inventory value.
- Lead time calculated from PODate to ReceivingDate and rounded up to whole days.
- Raw materials are identified by the Description field; items with sales are treated as finished goods, purchases-only as raw materials, and remaining as WIP.

## Limitations & Next Steps
- Dataset lacks explicit service level targets; reorder points exclude safety stock for variability.
- Ordering cost is approximated from invoice freight where available; refine with actual procurement costs.
