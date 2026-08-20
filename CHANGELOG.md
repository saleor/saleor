# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.24.0 [Unreleased]

### Breaking changes

- Removed the deprecated Authorize.Net payment gateway plugin (`mirumee.payments.authorize_net`).
- Removed the deprecated Razorpay payment gateway plugin (`mirumee.payments.razorpay`).
- Removed the deprecated Braintree payment gateway plugin (`mirumee.payments.braintree`).
- Removed the deprecated Dummy (`mirumee.payments.dummy`) and Dummy Credit Card (`mirumee.payments.dummy_credit_card`) payment gateway plugins.
- Apps will be no longer to be granted with `MANAGE_APPS` permission. In certain cases, this permission was able to be assigned by the authorized user.
  App with such permission was not able to *act* like an admin app, but permission technically was granted.

  From Saleor 3.24, this app installation with `MANAGE_APPS` permission will be rejected.
  To safely upgrade, ensure that all installed apps do not have this permission.
- Bulk delete mutations now limit the number of `ids` per call (default 100, configurable via the `BULK_DELETE_LIMIT` env var). Exceeding the limit returns an `INVALID` error. This applies to all bulk delete mutations, including `productBulkDelete`, `productVariantBulkDelete`, `categoryBulkDelete`, `collectionBulkDelete`, `productTypeBulkDelete`, `productMediaBulkDelete`, `attributeBulkDelete`, `attributeValueBulkDelete`, `customerBulkDelete`, `staffBulkDelete`, `pageBulkDelete`, `pageTypeBulkDelete`, `menuBulkDelete`, `menuItemBulkDelete`, `giftCardBulkDelete`, `saleBulkDelete`, `voucherBulkDelete`, `promotionBulkDelete`, `shippingPriceBulkDelete`, `shippingZoneBulkDelete`, `draftOrderBulkDelete`, and `draftOrderLinesBulkDelete`.
- Removed the deprecated `checkoutId` input argument from the `checkoutShippingAddressUpdate` and `checkoutBillingAddressUpdate` mutations. Use the `id` argument instead.
- `confirmAccount()` mutation no longer allows to confirm an account that was already confirmed. - #19459 by @NyanKiyosi
- Removed the deprecated `shopDomainUpdate` mutation. Use the `PUBLIC_URL` environment variable to configure the shop domain instead.
- Removed the deprecated `checkoutLineDelete` mutation. Use `checkoutLinesDelete` instead — it takes a `linesIds` list and only accepts the checkout `id` (the `token` and `checkoutId` arguments are gone).
- Removed the deprecated `shopFetchTaxRates` mutation, along with the `ShopFetchTaxRates` type. It was a no-op; configure taxes with the tax mutations (e.g. `taxConfigurationUpdate`) instead.
- Removed the deprecated `orderSettingsUpdate` mutation. Use the `channelUpdate` mutation with the `orderSettings` input to update order settings per channel instead.
- Removed the deprecated `orderSettings` query field. Use the `channel` query and read its `orderSettings` field instead.
- Removed the deprecated `orderAddNote` mutation, along with the `OrderAddNote` type and `OrderAddNoteInput` input. Use the `orderNoteAdd` mutation instead.
- Removed the deprecated `exportGiftCards` and `exportVoucherCodes` mutations, along with the `ExportGiftCards`, `ExportGiftCardsInput`, `ExportVoucherCodes` and `ExportVoucherCodesInput` types. Fetch the data with the `giftCards` and `voucher` queries and format it in your app instead.
- Removed the `GIFT_CARD_EXPORT_COMPLETED` and `VOUCHER_CODE_EXPORT_COMPLETED` webhook event types, along with the `GiftCardExportCompleted` and `VoucherCodeExportCompleted` subscription types. They were emitted only by the removed `exportGiftCards` and `exportVoucherCodes` mutations. Existing webhook subscriptions to these events are deleted by a migration; a webhook left with no other events will stop being triggered.
- Removed the `DIGITAL_LINKS` value from the `OrderEventsEmailsEnum` enum and the `DIGITAL_LINK_DOWNLOADED` value from the `CustomerEventsEnum` enum. Events with these types were deleted in 3.23, along with the legacy digital content feature that emitted them.
- Removed the always-empty `digital_lines` key from the fulfillment confirmation notification payload. Use `physical_lines`, which holds every line of the fulfillment.
- Attribute value and bulk attribute mutations now require the permission matching the attribute's type: `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES` for `PRODUCT_TYPE` attributes, `MANAGE_PAGE_TYPES_AND_ATTRIBUTES` for `PAGE_TYPE` attributes, and `MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES` for `CUSTOMER_TYPE` attributes. Previously each mutation required a single fixed permission regardless of the attribute's type, which let a requestor modify attributes of a type they were not authorized for.

  The affected mutations and their previously required permission:
  - `attributeValueCreate` — previously `MANAGE_PRODUCTS`; `PRODUCT_TYPE` attributes now require `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES` and `PAGE_TYPE` attributes now require `MANAGE_PAGE_TYPES_AND_ATTRIBUTES`
  - `attributeValueUpdate`, `attributeValueDelete`, `attributeReorderValues` — previously `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES`; unchanged for `PRODUCT_TYPE` attributes, but `PAGE_TYPE` attributes now require `MANAGE_PAGE_TYPES_AND_ATTRIBUTES`.
  - `attributeBulkDelete`, `attributeValueBulkDelete` — previously `MANAGE_PAGE_TYPES_AND_ATTRIBUTES`; unchanged for `PAGE_TYPE` attributes, but `PRODUCT_TYPE` attributes now require `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES`. When the call targets several types, every matching permission is required.
  - `attributeBulkCreate` and `attributeBulkUpdate` already resolved the permission from the attribute type. They now reject an attribute type that has no permission mapped, instead of falling back to `MANAGE_PAGE_TYPES_AND_ATTRIBUTES`.

  To upgrade, grant staff members and apps the permission matching the attribute types they operate on. A requestor holding only `MANAGE_PRODUCTS` can no longer create attribute values.
- Providing an empty `attributes` list (`null` or `[]`) in `where` filters for pages, products, and product variants now matches no objects instead of being ignored. The same now applies to a no-op attribute filter that builds no condition, such as an empty reference container (`reference: { pageSlugs: {} }`) - previously such a filter matched all product variants.

### GraphQL API

- Added `stockAvailability` and `stocks` filters to the `productVariants` query `where` input, allowing variants to be filtered by their stock status and stock quantity for a given channel - #17689 by @ayesha-waris
- Added `createdAt` and `createdBy` fields to the `AppToken` type, and an `installedBy` field to the `AppInstallation` type, recording the staff user who created the token or requested the installation. `createdBy` and `installedBy` require the `MANAGE_STAFF` permission and are null for records created before this was tracked or when the user has been deleted.
- `lines` input on the `checkoutCreate` mutation is no longer required. When omitted, a checkout with no lines is created.
- Removed the deprecated `availableShippingMethods` field from the `Order` type. Use `shippingMethods` instead.
- Removed the deprecated `variant` field from the `Product` type. Use the top-level `variant` query instead.
- Removed the deprecated `note` field from the `Checkout` type. Use `customerNote` instead.
- Removed the deprecated `isDigital` field from the `ProductType` type, the `isDigital` input from `ProductTypeInput`, the `DIGITAL` value from the `ProductTypeEnum` filter, and the `DIGITAL` value from `ProductTypeSortField`. These had no effect; use metadata or attributes instead (or `SHIPPING_REQUIRED` for sorting).
- Fixed `productVariantBulkUpdate` returning a 500 error when `channelListings.create` targeted a channel the variant was already listed in. The mutation now returns a `DUPLICATED_INPUT_ITEM` error recommending the `update` field, and respects the selected `errorPolicy` - #19355 by @ayesha-waris

### Webhooks

- Added `PRODUCT_TYPE_CREATED`, `PRODUCT_TYPE_UPDATED`, and `PRODUCT_TYPE_DELETED` webhook events, dispatched when a product type is created, updated, or deleted - #17574 by @ayesha-waris

### Other changes

- Dropped the database leftovers of the legacy digital content feature removed in 3.23: the `product_digitalcontent` and `product_digitalcontenturl` tables, and the `automatic_fulfillment_digital_products`, `default_digital_max_downloads` and `default_digital_url_valid_days` columns of `site_sitesettings`. Files uploaded through the legacy API are not removed from the media storage — the `digital_contents/` directory can be deleted manually.
- `ProductType.is_digital` was removed from the ORM model; the column itself will be dropped in 3.25.
- Removed the `is_digital` field from the `populatedb` sample data.

#### Search improvements

### Fixes

- Fixed `appCreate` and `appUpdate` failing with an unhandled error when `permissions` was `null` or omitted. `appCreate` now creates an app with no permissions, and `appUpdate` leaves the app's existing permissions untouched. Passing an empty list to `appUpdate` still clears them.

### Deprecations
