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

### Webhooks

### Other changes

- Log an error when a sync webhook is triggered inside a database transaction, to help locate callers that need to be moved outside of transactions - #15138 by @ayesha-waris

#### Search improvements

### Deprecations
