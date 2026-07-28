# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.24.0 [Unreleased]

### Breaking changes

- Removed the deprecated Authorize.Net payment gateway plugin (`mirumee.payments.authorize_net`).
- Apps will be no longer to be granted with `MANAGE_APPS` permission. In certain cases, this permission was able to be assigned by the authorized user.
  App with such permission was not able to *act* like an admin app, but permission technically was granted.

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
  From Saleor 3.24, this app installation with `MANAGE_APPS` permission will be rejected.
  To safely upgrade, ensure that all installed apps do not have this permission.
- Bulk delete mutations now limit the number of `ids` per call (default 100, configurable via the `BULK_DELETE_LIMIT` env var). Exceeding the limit returns an `INVALID` error. This applies to all bulk delete mutations, including `productBulkDelete`, `productVariantBulkDelete`, `categoryBulkDelete`, `collectionBulkDelete`, `productTypeBulkDelete`, `productMediaBulkDelete`, `attributeBulkDelete`, `attributeValueBulkDelete`, `customerBulkDelete`, `staffBulkDelete`, `pageBulkDelete`, `pageTypeBulkDelete`, `menuBulkDelete`, `menuItemBulkDelete`, `giftCardBulkDelete`, `saleBulkDelete`, `voucherBulkDelete`, `promotionBulkDelete`, `shippingPriceBulkDelete`, `shippingZoneBulkDelete`, `draftOrderBulkDelete`, and `draftOrderLinesBulkDelete`.
- Removed the deprecated `checkoutId` input argument from the `checkoutShippingAddressUpdate` and `checkoutBillingAddressUpdate` mutations. Use the `id` argument instead.
- `confirmAccount()` mutation no longer allows to confirm an account that was already confirmed. - #19459 by @NyanKiyosi
- Removed the deprecated `shopDomainUpdate` mutation. Use the `PUBLIC_URL` environment variable to configure the shop domain instead.
- Removed the deprecated `orderSettingsUpdate` mutation. Use the `channelUpdate` mutation with the `orderSettings` input to update order settings per channel instead.
- Removed the deprecated `orderSettings` query field. Use the `channel` query and read its `orderSettings` field instead.

### GraphQL API

- Added `stockAvailability` and `stocks` filters to the `productVariants` query `where` input, allowing variants to be filtered by their stock status and stock quantity for a given channel - #17689 by @ayesha-waris
- `lines` input on the `checkoutCreate` mutation is no longer required. When omitted, a checkout with no lines is created.
- Removed the deprecated `availableShippingMethods` field from the `Order` type. Use `shippingMethods` instead.
- Removed the deprecated `variant` field from the `Product` type. Use the top-level `variant` query instead.
- Removed the deprecated `note` field from the `Checkout` type. Use `customerNote` instead.
- Removed the deprecated `isDigital` field from the `ProductType` type, the `isDigital` input from `ProductTypeInput`, the `DIGITAL` value from the `ProductTypeEnum` filter, and the `DIGITAL` value from `ProductTypeSortField`. These had no effect; use metadata or attributes instead (or `SHIPPING_REQUIRED` for sorting).

### Webhooks

- Added `PRODUCT_TYPE_CREATED`, `PRODUCT_TYPE_UPDATED`, and `PRODUCT_TYPE_DELETED` webhook events, dispatched when a product type is created, updated, or deleted - #17574 by @ayesha-waris

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
