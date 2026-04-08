# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.24.0 [Unreleased]

### Breaking changes

- Made `refundSettings` field on `RefundSettingsUpdate` mutation nullable to correctly reflect that it can be `null` when errors occur.
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
- `AppInstallInput` for `appInstall` mutation now requires `appName` and `manifestUrl` fields in the schema, matching the validation that was always enforced by the mutation logic.
- Removed Adyen plugin (payment gateway). [Switch to the app](https://docs.saleor.io/developer/app-store/apps/adyen/overview).
- Removed `partial` field from the `Payment` GraphQL type. This field was an Adyen-specific workaround and always returned `false` after the Adyen plugin removal. Ensure you are not relying on this field (on Adyen gateway in general) before upgrading.
- Removed the NP Atobarai payment gateway plugin (`saleor.payment.gateways.np_atobarai`). Use the [App](https://docs.saleor.io/developer/app-store/apps/np-atobarai/overview) instead.
- Removed support for the legacy digital products API - #18952 by @NyanKiyoshi

  Important: digital products are still fully supported in Saleor. Only the legacy,
  undocumented digital content API has been removed, the supported approach is documented here: https://docs.saleor.io/recipes/digital-products
- Product media images from external URLs are now fetched asynchronously via background tasks in `productMediaCreate` and `productBulkCreate` mutations, improving response times. During download, the API returns HTTP 503 for the media image.
- Shipping-zone-based stock filtering is deprecated and will be removed in a future release. A new `useLegacyShippingZoneStockAvailability` shop setting controls the behavior: when disabled, stock availability across checkouts, orders, and product queries is resolved via the direct warehouse-channel link instead of shipping zones.

### GraphQL API

### Webhooks

### Other changes

#### Search improvements

- Improved page search with search vectors. Pages can now be searched by slug, title, content, attribute values, and page type information.
- Improve user search. Use search vector functionality to enable searching users by email address, first name, last name, and addresses.
- Improved checkout search with search vectors. The `search_index_dirty` flag is set whenever indexed checkout data changes, and a background task runs every minute to update search vectors for dirty checkouts, processing the oldest first. Search results are returned in order of best match relevance.
- Enhanced search functionality across key entities (products, orders, gift cards, checkouts, pages, and users) with advanced query capabilities:
  - Prefix matching: partial word searches (e.g., "coff" matches "coffee")
  - Boolean operators: `AND`, `OR`, and `-` (NOT) for complex queries
  - Exact phrase matching: use quotation marks `" "` for precise searches
  - Accent-insensitive search: queries automatically normalize diacritical marks, allowing searches to match regardless of accents (e.g., "cafe" matches "café")
  - Relevance-based ranking: exact matches score higher than prefix matches and appear first by default (can be overridden with `sortBy` parameter)
  - New `RANK` sort field available when using search filters to sort by relevance score

### Direct warehouse-channel stock availability

- Added `useLegacyShippingZoneStockAvailability` setting to `Shop` and `ShopSettingsInput`. When enabled (default for existing installations), stock availability is filtered through shipping zones and the destination address. When disabled stock availability is determined by the direct warehouse-channel link, ignoring shipping zones.
- Checkout mutations (`checkoutCreate`, `checkoutLinesAdd`, `checkoutLinesUpdate`, `checkoutShippingAddressUpdate`, `checkoutCreateFromOrder`) now respect the new setting during stock validation and reservation.
- Order mutations (`draftOrderCreate`, `draftOrderComplete`, `orderLinesCreate`, `orderLineUpdate`) and the fulfillment flow now respect the setting during stock allocation.
- Product filtering by stock availability and `Product.isAvailable` resolver now respect the setting.
- Webhook payloads for checkout and fulfillment events select the warehouse based on the setting.
- Deprecated the `address` argument on `ProductVariant.stocks`, `ProductVariant.quantityAvailable`, and `Product.isAvailable`. When `useLegacyShippingZoneStockAvailability` is disabled, the address argument is ignored.

### Deprecations
