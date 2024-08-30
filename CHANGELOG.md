# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.21.0 [Unreleased]

### Highlights

### Breaking changes

- Drop the `manager.perform_mutation` method - #16515 by @maarcingebala
- Drop manager methods used by WebhookPlugin - #16487 by @maarcingebala

  Webhook functionality is moved from plugin to core. As a result the following manager methods are removed:

  - `get_shipping_methods_for_checkout`
  - `product_created`

  See [the migration guide](https://docs.saleor.io/upgrade-guides/3-20-to-3-21#deprecated-webhookplugin-and-webhook-related-plugin-hooks) for more details.

### GraphQL API

- Add `CheckoutCustomerNoteUpdate` mutation - #16315 by @pitkes22
- Add `customerNote` field to `Checkout` type to make it consistent with `Order` model - #16561 by @Air-t

### Webhooks

### Other changes

- Added support for numeric and lower-case boolean environment variables - #16313 by @NyanKiyoshi
- Fixed a potential crash when Checkout metadata is accessed with high concurrency - #16411 by @patrys
- Add slugs to product/category/collection/page translations. Allow to query by translated slug - #16449 by @delemeator
- Fixed a crash when the Decimal scalar is passed a non-normal value - #16520 by @patrys
- Fixed a bug when saving webhook payload to Azure Storage - #16585 by @delemeator
