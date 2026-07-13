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

### GraphQL API

- Added `stockAvailability` and `stocks` filters to the `productVariants` query `where` input, allowing variants to be filtered by their stock status and stock quantity for a given channel - #17689 by @ayesha-waris

### Webhooks

- Added `PRODUCT_TYPE_CREATED`, `PRODUCT_TYPE_UPDATED`, and `PRODUCT_TYPE_DELETED` webhook events, dispatched when a product type is created, updated, or deleted - #17574 by @ayesha-waris
- Gift cards support as payment method within Transaction API (read more in the [docs](https://docs.saleor.io/developer/gift-cards#using-gift-cards-in-checkout)).
- `Attribute` fields `name`, `slug` and `type` are now non-nullable in schema.
- Added new scalar `NonNegativeInt` which allows integer values greater than or equal to zero.
- Scalars `Minute`, `Hour` and `Day` now inherit from `NonNegativeInt`, which mean GraphQL disallows negative values for time units.
- Removed `partial` field from the `Payment` GraphQL type.
- Added sorting and filtering support for `transactions` query:
  - sort by `CREATED_AT`, `MODIFIED_AT`;
  - filter by `createdAt`, `modifiedAt` date ranges and by transaction events (`type`, `createdAt`).
- Added `PasswordLoginMode` setting to control password-based authentication. When set to `DISABLED`, all password authentication mutations (`tokenCreate`, `setPassword`, `passwordChange`, `requestPasswordReset`, `tokenRefresh`) return errors. When set to `CUSTOMERS_ONLY`, staff users who log in with a password are treated as customers without staff
permissions.
- `staffDelete` mutation now always deletes the staff user. Previously, staff members with existing orders were only deactivated (`is_staff` set to `False`); now they are fully removed regardless of order history.
- Deprecated the `MANAGE_OBSERVABILITY` permission (`PermissionEnum`). The observability feature is no longer supported and the permission will be removed in Saleor 3.24.

### Webhooks

- Deprecated the `OBSERVABILITY` webhook event type (`WebhookEventTypeEnum`, `WebhookEventTypeAsyncEnum`, `WebhookSampleEventTypeEnum`). The observability feature is no longer supported and the event will be removed in Saleor 3.24.
- For order webhook events, sync webhooks (such as `ORDER_CALCULATE_TAXES` and `ORDER_FILTER_SHIPPING_METHODS`) are no longer pre-fired before sending async webhook events. Sync webhooks are now only triggered when their data is actually requested, improving performance and decoupling async event delivery from sync webhook execution.
-  Building payloads for webhook order events (including draft orders and fulfillments) is now delegated to a separate background task. This speeds up the execution of most order mutations by deferring the expensive payload serialization out of the request path.

### Explicit delivery options
 - Introduced `deliveryOptionsCalculate` mutation to give storefronts explicit, deterministic control over when shipping webhook calls happen. Previously `SHIPPING_LIST_METHODS_FOR_CHECKOUT` and `CHECKOUT_FILTER_SHIPPING_METHODS` webhooks were fired implicitly, inside checkout mutations (e.g., on address change) and while resolving query fields, causing unpredictable latency, uncontrolled webhook traffic, and increased costs. Developers can now decide exactly when to fetch delivery options by calling `deliveryOptionsCalculate`, which returns a list of `Delivery` objects.

   The selected delivery method is available on the new `Checkout.delivery` field, which replaces the deprecated `Checkout.shippingMethod` and `Checkout.deliveryMethod` fields.

   To help storefronts detect when the delivery method requires attention, two new problem types are introduced in `Checkout.problems`:
   - `CheckoutProblemDeliveryMethodStale`: the currently selected method may be outdated due to checkout changes (e.g., a different shipping address, an applied voucher). This problem does not block checkout completion but triggers re-validation of the delivery method when `checkoutComplete` is called. Calling `deliveryOptionsCalculate` will re-validate the assigned delivery.
   - `CheckoutProblemDeliveryMethodInvalid`: the selected delivery method is no longer valid (e.g., the shipping address no longer falls within it). This problem blocks `checkoutComplete` until a valid delivery method is assigned via `checkoutDeliveryMethodUpdate`.

   See the [upgrading guide](https://docs.saleor.io/upgrade-guides/3-22-to-3-23##explicit-delivery-options-calculation) to learn more.
  - `checkoutDeliveryMethodUpdate` mutation now accepts `CheckoutDelivery` ID as `deliveryMethodId` (ID returned by `deliveryOptionsCalculate` mutation). Usage of `ShippingMethod` ID is deprecated in favor of `CheckoutDelivery` ID.

### EditorJS (Rich Text Editor)

- Made the EditorJS parser stricter. We no longer accept unknown/extra fields. - #18969 by @NyanKiyoshi
- Removed the following deprecated behaviors:

  - `EDITOR_JS_LINK_REL` configuration behavior has changed.
    Links rendered by EditorJS (`<a href="..." rel="...">`) now default to
    `rel="noopener noreferrer"` instead of an empty value.
    Learn more in the [documentation][EDITOR_JS_LINK_REL].
  - `UNSAFE_EDITOR_JS_ALLOWED_URL_SCHEMES` has been removed.
    It's no longer possible to extend the list of allowed URL schemes via settings.

    If you require support for additional URL schemes, open a request:
    https://github.com/saleor/saleor/issues

  (Via #18976 by @NyanKiyoshi)

[EDITOR_JS_LINK_REL]: https://docs.saleor.io/setup/configuration#editor_js_link_rel

### Other changes

#### Search improvements

### Deprecations
