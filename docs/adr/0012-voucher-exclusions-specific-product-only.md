# Voucher exclusions win over includes and exist only on SPECIFIC_PRODUCT vouchers

**Tags:** discounts, vouchers, checkout, orders

## Context

A merchant gives 2% off everything except recycling-fee lines. The fees are product variants, so
they carry VAT, and the law forbids discounting them. Vouchers could only *include* catalogue
items, so the only workaround was a hand-maintained "eligible" collection holding every non-fee
product.

## Decision

`SPECIFIC_PRODUCT` vouchers get an exclude list per dimension, and product type becomes a new
dimension on both sides.

| Dimension    | Include          | Exclude                  |
| ------------ | ---------------- | ------------------------ |
| Product      | `products`       | `excluded_products`      |
| Variant      | `variants`       | `excluded_variants`      |
| Collection   | `collections`    | `excluded_collections`   |
| Category     | `categories`     | `excluded_categories`    |
| Product type | `product_types`  | `excluded_product_types` |

A line is discounted when both hold:

1. It matches any include, or the voucher has no includes.
2. It matches no exclusion.

### Rules

| Situation                                                      | Outcome                                           |
| -------------------------------------------------------------- | ------------------------------------------------- |
| Include category C, exclude product P in C                     | Allowed. Everything in C except P is discounted.  |
| Same item in include and exclude of one dimension              | Rejected. It can only be a mistake.               |
| Excluded category has subcategories                            | Subcategories are not excluded (exact match, as for includes). |
| Exclusions on `ENTIRE_ORDER` or `SHIPPING` voucher             | Rejected on create, update and `voucherCataloguesAdd`. |
| Changing type away from `SPECIFIC_PRODUCT` with exclusions set | Rejected.                                         |
| Include lists on `ENTIRE_ORDER` or `SHIPPING` voucher          | Unchanged: stored and ignored.                    |

The merchant's case becomes a percentage `SPECIFIC_PRODUCT` voucher with no includes and the fee
product type excluded.

### Why reject instead of ignore

`ENTIRE_ORDER` and `SHIPPING` vouchers spread their discount over every line. If exclusions were
stored and ignored there, the merchant would believe fee lines are protected while they are being
discounted. That is the exact outcome the feature exists to prevent. Include lists keep their old
silent behaviour because nothing legal depends on them.

## Known gap

These order-level discounts still spread proportionally across all lines, fee lines included:

| Discount                | Exclusion support |
| ----------------------- | ----------------- |
| `ENTIRE_ORDER` voucher  | None              |
| Order promotion         | None              |
| Manual order discount   | None              |

A merchant who needs fee lines untouched must use a `SPECIFIC_PRODUCT` voucher. Revisit if
exclusions are needed for order-level discounts.
