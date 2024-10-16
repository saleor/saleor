# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.21.0 [Unreleased]

### Highlights

### Breaking changes

- Drop the `manager.perform_mutation` method. - #16515 by @maarcingebala
- Dropped the invoicing plugin. For an example of a replacement, see https://docs.saleor.io/developer/app-store/apps/invoices - #16631 by @patrys

### GraphQL API

- Add `CheckoutCustomerNoteUpdate` mutation - #16315 by @pitkes22
- Add `customerNote` field to `Checkout` type to make it consistent with `Order` model - #16561 by @Air-t
- Add `type` field to `TaxableObjectDiscount` type - #16630 by @zedzior
- Add error handling for invalid channel slugs in `products` query to return an appropriate error when the channel does not exist - #16530 by @nghiapham1026

### Webhooks

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
