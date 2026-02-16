# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.23.0 [Unreleased]

### Breaking changes

- Fix missing denormalization of shipping methods metadata when creating an order.
  - Shipping method metadata is now copied to dedicated order fields (`shipping_method_metadata` and `shipping_method_private_metadata`) during checkout-to-order conversion. This ensures that order metadata remains consistent even if the original shipping method is modified or deleted. As a result, updates made to a shipping method's metadata after order creation will no longer be reflected in the order's `shippingMethod.metadata` field.
  - Shipping method metadata is now also denormalized during draft order finalization, ensuring consistent behavior across all order creation flows.
- Fields `options`, `mount` and `target` are removed from `AppExtension` and `AppManifestExtension` types. Use `mountName`, `targetName` and `settings`
- Deprecate the `hasVariants` field on `ProductType`. This setting is a legacy artifact from the former Simple/Configurable product distinction. Products can have multiple variants regardless of this flag. Previously, it only prevented assigning variant attributes to a product type; this restriction will no longer apply.
- Improved error handling in Federation - #18718 by @NyanKiyoshi

  The type for GraphQL field `representations` in `{ _entities(representations: [_Any!]!) { ... } }` was changed.

  Before: `[_Any]`
  After: `[_Any!]!`

  Make sure to adapt your GraphQL queries if you use the `_entities` query.
- Mutations `channelCreate` and `channelUpdate` now raise GraphQL errors instead `INVALID` when negative `MINUTE`/`HOUR`/`DAY` values are passed.

### GraphQL API

- Gift cards support as payment method within Transaction API (read more in the [docs](https://docs.saleor.io/developer/gift-cards#using-gift-cards-in-checkout)).
- `Attribute` fields `name`, `slug` and `type` are now non-nullable in schema.
- Added new scalar `NonNegativeInt` which allows integer values greater than or equal to zero.
- Scalars `Minute`, `Hour` and `Day` now inherit from `NonNegativeInt`, which mean GraphQL disallows negative values for time units.

### Webhooks
For order webhook events, sync webhooks (such as `ORDER_CALCULATE_TAXES` and `ORDER_FILTER_SHIPPING_METHODS`) are no longer pre-fired before sending async webhook events. Sync webhooks are now only triggered when their data is actually requested, improving performance and decoupling async event delivery from sync webhook execution.

### Other changes

- Enhanced search functionality across key entities (products, orders, gift cards, checkouts, pages, and users) with advanced query capabilities:
  - Prefix matching: partial word searches (e.g., "coff" matches "coffee")
  - Boolean operators: `AND`, `OR`, and `-` (NOT) for complex queries
  - Exact phrase matching: use quotation marks `" "` for precise searches
  - Relevance-based ranking: exact matches score higher than prefix matches and appear first by default (can be overridden with `sortBy` parameter)
  - New `RANK` sort field available when using search filters to sort by relevance score
- Improved page search with search vectors. Pages can now be searched by slug, title, content, attribute values, and page type information.
- Fix send order confirmation email to staff - #18342 by @Shaokun-X
- Validation on `AppExtension` is now removed. Saleor will accept string values for `mount` and `target` from Manifest during App installation and JSON value for `options` field.
Validation is now performed on the frontend (Dashboard). This change increases velocity of features related to apps and extensions, now Dashboard is only entity that ensures the contract
- Improve user search. Use search vector functionality to enable searching users by email address, first name, last name, and addresses.
- Improved checkout search with search vectors. The `search_index_dirty` flag is set whenever indexed checkout data changes, and a background task runs every minute to update search vectors for dirty checkouts, processing the oldest first. Search results are returned in order of best match relevance.
- Add optional usage telemetry. - #18789 by @wcislo-saleor
- The app can now be installed without providing a `tokenTargetUrl` in the manifest file.

### Deprecations

- Deprecate the `hasVariants` field on `ProductType`.
- Deprecate export mutations (`exportProducts`, `exportGiftCards`, `exportVoucherCodes`). All data can be fetched via the GraphQL API and parsed into the desired format by apps or external tools.
