# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.24.0 [Unreleased]

### Breaking changes

- Removed the deprecated Authorize.Net payment gateway plugin (`mirumee.payments.authorize_net`).
- Apps will be no longer to be granted with `MANAGE_APPS` permission. In certain cases, this permission was able to be assigned by the authorized user.
  App with such permission was not able to *act* like an admin app, but permission technically was granted.

  From Saleor 3.24, this app installation with `MANAGE_APPS` permission will be rejected.
  To safely upgrade, ensure that all installed apps do not have this permission.
- Bulk delete mutations now limit the number of `ids` per call (default 100, configurable via the `BULK_DELETE_LIMIT` env var). Exceeding the limit returns an `INVALID` error. This applies to all bulk delete mutations, including `productBulkDelete`, `productVariantBulkDelete`, `categoryBulkDelete`, `collectionBulkDelete`, `productTypeBulkDelete`, `productMediaBulkDelete`, `attributeBulkDelete`, `attributeValueBulkDelete`, `customerBulkDelete`, `staffBulkDelete`, `pageBulkDelete`, `pageTypeBulkDelete`, `menuBulkDelete`, `menuItemBulkDelete`, `giftCardBulkDelete`, `saleBulkDelete`, `voucherBulkDelete`, `promotionBulkDelete`, `shippingPriceBulkDelete`, `shippingZoneBulkDelete`, `draftOrderBulkDelete`, and `draftOrderLinesBulkDelete`.
- Removed the deprecated `checkoutId` input argument from the `checkoutShippingAddressUpdate` and `checkoutBillingAddressUpdate` mutations. Use the `id` argument instead.

### GraphQL API

- Added `stockAvailability` and `stocks` filters to the `productVariants` query `where` input, allowing variants to be filtered by their stock status and stock quantity for a given channel - #17689 by @ayesha-waris
- Fixed `productVariantBulkUpdate` returning a 500 error when `channelListings.create` targeted a channel the variant was already listed in. The mutation now returns a `DUPLICATED_INPUT_ITEM` error recommending the `update` field, and respects the selected `errorPolicy`.

### Webhooks

- Added `PRODUCT_TYPE_CREATED`, `PRODUCT_TYPE_UPDATED`, and `PRODUCT_TYPE_DELETED` webhook events, dispatched when a product type is created, updated, or deleted - #17574 by @ayesha-waris

### Other changes

#### Search improvements

### Deprecations
