# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.22.0 [Unreleased]

### Breaking changes

### GraphQL API
- Added support for filtering products by attribute value names. The `AttributeInput` now includes a `valueNames` field, enabling filtering by the names of attribute values, in addition to the existing filtering by value slugs.
- You can now filter and search orders using the new `where` and `search` fields on the `orders` query.
  - Use `where` to define complex conditions with `AND`/`OR` logic and operators like `eq`, `oneOf`, `range`.
  - Use `search` to perform full-text search across relevant fields.
  - Added filtering options for orders:
    - Filter by voucher codes.
    - Filter by invoice existence.
    - Filter by associated invoice creation date.
    - Filter by fulfillment existence.
    - Filter by associated fulfillment status.
    - Filter by number of lines in the order.
- Extend the `Page` type with an `attribute` field. Adds support for querying a specific attribute on a page by `slug`, returning the matching attribute and its assigned values, or null if no match is found.

### Webhooks

### Other changes
- Add JSON schemas for synchronous webhooks, now available in `saleor/json_schemas.py`. These schemas define the expected structure of webhook responses sent back to Saleor, enabling improved validation and tooling support for integrations. This change helps ensure that responses from webhook consumers meet Saleor’s expectations and can be reliably processed.
- deps: upgraded urllib3 from v1.x to v2.x
- Fix PAGE_DELETE webhook to include pageType in payload - #17697 by @Jennyyyy0212 and @CherineCho2016
- Stripe Plugin has been deprecated. It will be removed in the future. Please use [the Stripe App](https://docs.saleor.io/developer/app-store/apps/stripe/overview) instead
- App Extensions: Added new allowed extension target: NEW_TAB. Once handled in the Dashboard, an extension will be able to open a link in new tab
- App Extensions: New mount points for Dashboard categories, collections, gift cards, draft orders, discounts, vouchers, pages, pages types and menus
