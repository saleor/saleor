# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.21.0 [Unreleased]

### Highlights
- Introduced a configurable customer address strategy, allowing control over whether shipping or billing addresses are saved in the customer’s address book - #17364 by @IKarbowiak
	- Applies when a checkout or draft order is completed for a logged-in user.
	- Default behavior remains unchanged: addresses are saved for checkouts but not for draft orders.
	- The new save address setting is available in:
      - `checkoutCreate`
      - `checkoutShippingAddressUpdate`
      - `checkoutBillingAddressUpdate`
      - `draftOrderCreate`
      - `draftOrderUpdate`
	- The flag must be provided as part of an address; otherwise, an error is raised.
	- Does not apply to Click & Collect delivery methods — shipping address is not saved in such case.

### Breaking changes

- Drop the `manager.perform_mutation` method. - #16515 by @maarcingebala
- Dropped the invoicing plugin. For an example of a replacement, see https://docs.saleor.io/developer/app-store/apps/invoices - #16631 by @patrys
- Dropped the deprecated "Stripe (Deprecated)" payment plugin. If your codebase refers to `mirumee.payments.stripe`, you will need to migrate to the supported plugin, `saleor.payments.stripe` - #17539 by @patrys
- Change error codes related to user enumeration bad habbit. Included mutations will now not reveal information in error codes if email was already registered:
  - `AccountRegister`,
    `AccountRegister` mutation will additionaly not return `ID` of the user.
  - `ConfirmAccount`,
  - `RequestPasswordReset`,
    `RequestPasswordReset` will now require `channel` as input for staff users,
  - `SetPassword` - #16243 by @kadewu
- Require `MANAGE_ORDERS` for updating order and order line metadata - #17223 by @IKarbowiak
  - The `updateMetadata` for `Order` and `OrderLine` types requires the `MANAGE_ORDERS` permission
- Fix updating `metadata` and `privateMetadata` in `transactionUpdate` - #17261 by @IKarbowiak
  - The provided data in the input field are merged with the existing one (previously the existing data was overridden by the new one).
- Fixed `invoiceRequest` no longer throws an error, when only app with webhook `INVOICE_REQUESTED` is installed, without invoice plugin - #17355 by @witoszekdev
- Queries: `checkouts`, `checkoutLines`, and `me.checkouts` will no longer trigger external calls to calculate taxes: the `CHECKOUT_CALCULATE_TAXES` webhooks and plugins (including AvataxPlugin) - #17268 by @korycins
- Queries `checkouts`, `checkoutLines`, and `me.checkouts` will no longer trigger external calls to fetch shipping methods (`SHIPPING_LIST_METHODS_FOR_CHECKOUT`) or to filter the available shipping methods (`CHECKOUT_FILTER_SHIPPING_METHODS`) - #17387 by @korycins
- Queries: `orders`, `draftOrders` and `me.orders` will no longer trigger external calls to calculate taxes: the `ORDER_CALCULATE_TAXES` webhooks and plugins (including AvataxPlugin) - #17421 by @korycins
- Queries: `orders`, `draftOrders` and `me.orders` will no longer trigger external calls to filter the available shipping methods (`ORDER_FILTER_SHIPPING_METHODS`) - #17425 by @korycins
- Drop `change_user_address` method from plugin manager - #17495 by @IKarbowiak
- `DraftOrderUpdate` do not call `DRAFT_ORDER_UPDATED` anymore in case nothing changed - #17532 by @IKarbowiak
- `OrderUpdate` mutation do not call `ORDER_UPDATED` anymore in case nothing changed - #17507 by @IKarbowiak

### GraphQL API

- Add `CheckoutCustomerNoteUpdate` mutation - #16315 by @pitkes22
- Add `customerNote` field to `Checkout` type to make it consistent with `Order` model - #16561 by @Air-t
- Add `type` field to `TaxableObjectDiscount` type - #16630 by @zedzior
- Add `productVariants` field to `Product` instead of `variants`. Mark `Product.variants` as deprecated - #16998 by @kadewu
- Fix checkout `line.undiscountedTotalPrice` and `line.undiscountedUnitPrice` calculation. - #17193 by @IKarbowiak
  - Return the normalized price in case the checkout prices are not expired, otherwise fetch the price from variant channel listing.
- Add prior price fields to `VariantPricingInfo`, `ProductPricingInfo` and `CheckoutLine` - #17202 by @delemeator
- Fix undiscounted price taxation inside an order calculations when the Avatax plugin is used - #17253 by @zedzior
- The `checkoutShippingAddressUpdate` mutation anymore does not raise an error when a shipping address is updated for a checkout that does not require shipping - #17341 by @IKarbowiak
- Add `appReenableSyncWebhooks` mutation - #16658 by @tomaszszymanski129
- Add `breakerState` and `breakerLastStateChange` to the `App` type - #16658 by @tomaszszymanski129
- Mutation `draftOrderCreate` and `draftOrderUpdate` now supports adding metadata & privateMetadata (via `DraftOrderCreateInput`) - #17358 by @lkostrowski
- Deprecate `draftOrderInput.discount` field - #17294 by @zedzior
- `GiftCardCreate` and `GiftCardUpdate` mutations now allows to set `metadata` and `privateMetadata` fields via `GiftCardCreateInput` and `GiftCardUpdateInput` - #17399 by @lkostrowski
- Improved error handling when trying to set invalid metadata. Now, invalid metadata should properly return `error.field` containing `metadata` or `privateMetadata`, instead generic `input` - #17470 by @lkostrowski
- `CheckoutLinesUpdate` now accepts `metadata` for each line in the input. That means updating checkout lines and metadata of checkout lines can be done in single mutations - #17523 by @lkostrowski
- `CheckoutLinesAdd` now properly validates `metadata` provided in input - #17523 by @lkostrowski
- `CheckoutCreateInput` now accepts `metadata` and `privateMetadata` fields, so `checkoutCreate` can now create checkout with metadata in a single call - #17503 by @lkostrowski
- `orderUpdate` mutation now allows to update `metadata` and `privateMetadata` via `OrderUpdateInput` - #1508 by @lkostrowski
- `DraftOrderInput`, `OrderUpdateInput` and `DraftOrderCreateInput` now allow to provide `languageCode` - #17553 by @lkostrowski

### Webhooks

- Fixed webhookTrigger payload type for events related to ProductVariant - #16956 by @delemeator
- Truncate lenghty responses in `EventDeliveryAttempt` objects - #17044 by @wcislo-saleor
- Webhooks `CHECKOUT_FILTER_SHIPPING_METHODS` & `ORDER_FILTER_SHIPPING_METHODS` are no longer executed when not needed (no available shipping methods, e.g. due to lack of shipping address) - #17328 by @lkostrowski
- New feature: sync webhooks circuit breaker - #16658 by @tomaszszymanski129
- Fixed webhook `PRODUCT_VARIANT_METADATA_UPDATED` not being sent when `productVariantUpdate` mutation was called. Now, when `metadata` or `privateMetadata` is included in `ProductVariantUpdateInput`, both `PRODUCT_VARIANT_METADATA_UPDATED` and `PRODUCT_VARIANT_UPDATED` will be emitted (if subscribed) - #17406 by @lkostrowski
- Update Draft Order shipping via `orderUpdateShipping` will emit `DRAFT_ORDER_UPDATED` webhook. Previously it was `ORDER_UPDATED` - #17480 by @lkostrowski
- Update editable Order shipping via `orderUpdateShipping` will emit `ORDER_UPDATED` webhook when `shippingMethod` will be cleared (by passing `null` to graphQL input). - #17480 by @lkostrowski

### Other changes
- Added support for numeric and lower-case boolean environment variables - #16313 by @NyanKiyoshi
- Fixed a potential crash when Checkout metadata is accessed with high concurrency - #16411 by @patrys
- Add slugs to product/category/collection/page translations. Allow to query by translated slug - #16449 by @delemeator
- Fixed a crash when the Decimal scalar is passed a non-normal value - #16520 by @patrys
- Fixed a bug when saving webhook payload to Azure Storage - #16585 by @delemeator
- Added validation for tax data received from tax app - #16720 by @zedzior
- Fixed order-level discounts handling when using tax app for tax calculation - #16696 by @zedzior
- Fixed bug when manual line discount doesn't override line-level vouchers - #16738 by @zedzior
- Skipped obsolete payload save and cleanup for successful sync webhooks - #16632 by @cmiacz
- Removed support for the django-debug-toolbar debugging tool and the `ENABLE_DEBUG_TOOLBAR` env variable - #16902 by @patrys
- Fixed playground not displaying docs if api is hidden behind reverse proxy - #16810 by @jqob
- Drop tax data line number validation for Avatax plugin - #16917 by @zedzior
- Fix decreasing voucher code usage after changing `includeDraftOrderInVoucherUsage` to false - #17028 by @zedzior
- Fix undiscounted price taxation when prices are entered with taxes - #16992 by @zedzior
- Fix `products` sorting when using `sortBy: {field: COLLECTION}` - #17189 by @korycins
- Fix checkout funds releasing task - #17198 by @IKarbowiak
- Fixed 'healthcheck' middleware (`/health/` endpoint) not forwarding incoming traffic whenever the protocol wasn't HTTP (such as WebSocket or Lifespan) - #17248 by @NyanKiyoshi
- Added support for the AWS_S3_URL_PROTOCOL environment variable - #17305 by @p-febis
- Fixed Celery worker issues when using SQS by using celery[sqs] extras instead of direct pycurl dependency - by @mariobrgomes
- Added [`alg`](https://datatracker.ietf.org/doc/html/rfc7517#section-4.4) key to JWKS available at `/.well-known/jwks.json` - #17363 by @lkostrowski
- `checkout.shippingMethods` and `checkout.availableShippingMethods` will no longer return external shipping methods if their currency differs from the checkout's currency - #17350 by @korycins
- Use denormalized base prices during order update - #17160 by @zedzior
  - `UNCONFIRMED` orders will never refresh its base prices
  - `DRAFT` orders will refresh its base prices after default 24 hours
- Fix bug which, in some cases, caused product name translations to be empty in order lines - #17504 by @delemeator
- Added a warning to metadata input fields in GraphQL schema informing to never store sensitive data.
  This ensures user awareness of potential security policy violations and compliance risks of storing
  certain types of data. - #17506 by @NyanKiyoshi
- Improve status calculation for orders with waiting-for-approval fulfillments - #17471 by @delemeator
- Allow to change Admin email plugin custom templates back to default - #17563 by @wcislo-saleor
- Fixes incorrect gift card balances after covering the full order total - #17566 by @korycins
