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
- `confirmAccount()` mutation no longer allows to confirm an account that was already confirmed. - #19459 by @NyanKiyosi
- Removed the legacy Observability feature. The deprecated `OBSERVABILITY` webhook event type and the `MANAGE_OBSERVABILITY` permission no longer exist and have been dropped from the schema (`PermissionEnum`, `WebhookEventTypeEnum`, `WebhookEventTypeAsyncEnum`, and `WebhookSampleEventEnum`). App manifests requesting `MANAGE_OBSERVABILITY` will be rejected on install, and existing subscriptions to the `OBSERVABILITY` event are removed by a migration. Use OpenTelemetry for observability instead.

  #### For self-hosting

  The `OBSERVABILITY_BROKER_URL`, `OBSERVABILITY_ACTIVE`, `OBSERVABILITY_REPORT_ALL_API_CALLS`, `OBSERVABILITY_MAX_PAYLOAD_SIZE`, `OBSERVABILITY_BUFFER_SIZE_LIMIT`, `OBSERVABILITY_BUFFER_BATCH_SIZE`, `OBSERVABILITY_REPORT_PERIOD`, and `OBSERVABILITY_BUFFER_TIMEOUT` environment variables are no longer used and can be removed from your deployment. The dedicated `observability` Celery queue and its beat-scheduled reporter task have also been removed; any worker configured to consume the `observability` queue can be decommissioned.
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

### Deprecations
