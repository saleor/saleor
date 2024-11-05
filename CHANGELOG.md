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

### GraphQL API

- Add `CheckoutCustomerNoteUpdate` mutation - #16315 by @pitkes22
- Add `customerNote` field to `Checkout` type to make it consistent with `Order` model - #16561 by @Air-t
- Add `type` field to `TaxableObjectDiscount` type - #16630 by @zedzior

### Webhooks

- Fixed webhookTrigger payload type for events related to ProductVariant - #16956 by @delemeator

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
