# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.23.0 [Unreleased]

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

### Webhooks

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

- Fix Google OAuth OIDC login failing with `invalid_scope` error when `enable_refresh_token` is enabled. Google does not support the `offline_access` scope; use `access_type=offline` authorization parameter instead. - #18919 by @dnplkndll
- Add `saleor.graphql.field.usage` OTel metric to track GraphQL field resolver call counts. The metric is emitted for deprecated fields (detected automatically) and for fields explicitly opted in with `monitor_usage=True` on a `BaseField` declaration.
- Fix send order confirmation email to staff - #18342 by @Shaokun-X
- Validation on `AppExtension` is now removed. Saleor will accept string values for `mount` and `target` from Manifest during App installation and JSON value for `options` field.
Validation is now performed on the frontend (Dashboard). This change increases velocity of features related to apps and extensions, now Dashboard is only entity that ensures the contract
- Add optional usage telemetry. - #18789 by @wcislo-saleor
- The app can now be installed without providing a `tokenTargetUrl` in the manifest file.
- Removed the setting `JWT_EXPIRE` which allowed to configure Saleor to ignore the JWT token expiration. - #18856 by @NyanKiyoshi
- Removed support for custom `User` DB models in `./manage.py createsuperuser` command. - #18890 by @NyanKiyoshi
- OIDC: When an existing user is claimed by an OIDC provider for the first time, their password is now invalidated to prevent login with stale credentials. This covers the case where a previously deleted staff account is recreated via OIDC.

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

- Deprecate the `hasVariants` field on `ProductType`.
- Deprecate export mutations (`exportProducts`, `exportGiftCards`, `exportVoucherCodes`). All data can be fetched via the GraphQL API and parsed into the desired format by apps or external tools.
- Deprecate `voucher` input field on `DraftOrderInput` and `DraftOrderCreateInput`. Use `voucherCode` instead.
