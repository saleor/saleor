# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.21.0 [Unreleased]

### Highlights

### Breaking changes

- Drop the `manager.perform_mutation` method. - #16515 by @maarcingebala
- Dropped the invoicing plugin. For an example of a replacement, see https://docs.saleor.io/developer/app-store/apps/invoices - #16631 by @patrys
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

### Webhooks

- Fixed webhookTrigger payload type for events related to ProductVariant - #16956 by @delemeator
- Truncate lenghty responses in `EventDeliveryAttempt` objects - #17044 by @wcislo-saleor
- Webhooks `CHECKOUT_FILTER_SHIPPING_METHODS` & `ORDER_FILTER_SHIPPING_METHODS` are no longer executed when not needed (no available shipping methods, e.g. due to lack of shipping address) - #17328 by @lkostrowski

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
- Fixed pycurl dependency and required system libraries to fix Celery worker issues when using SQS by @mariobrgomes
