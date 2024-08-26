
# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.21.0 [Unreleased]

### Highlights

### Breaking changes

- Drop the `manager.perform_mutation` method. - #16515 by @maarcingebala

### GraphQL API

- Add `CheckoutCustomerNoteUpdate` mutation - #16315 by @pitkes22
- Add `customerNote` field to `Checkout` type to make it consistent with `Order` model - #16561 by @Air-t

### Webhooks

### Other changes

- Added support for numeric and lower-case boolean environment variables - #16313 by @NyanKiyoshi
- Fixed a potential crash when Checkout metadata is accessed with high concurrency - #16411 by @patrys
- Fixed a crash when the Decimal scalar is passed a non-normal value - #16520 by @patrys
