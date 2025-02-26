# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.23.0 [Unreleased]

### Breaking changes

### GraphQL API

### Webhooks

### Other changes
- Improved page search with search vectors. Pages can now be searched by slug, title, content, attribute values, and page type information.

- Fix send order confirmation email to staff - #18342 by @Shaokun-X

### Deprecations

Following plugins are now marked as deprecated:

| Plugin Name | Plugin ID | Possible replacements |
|-------------|-----------|-------------|
| Braintree | `mirumee.payments.braintree` | [JusPay Hyperswitch App](https://docs.hyperswitch.io/explore-hyperswitch/e-commerce-platform-plugins/saleor-app) or [Custom App](https://docs.saleor.io/developer/extending/apps/overview) |
| Razorpay | `mirumee.payments.razorpay` | [JusPay Hyperswitch App](https://docs.hyperswitch.io/explore-hyperswitch/e-commerce-platform-plugins/saleor-app) or [Custom App](https://docs.saleor.io/developer/extending/apps/overview) |
| Sendgrid | `mirumee.notifications.sendgrid_email` | [Saleor SMTP App](https://apps.saleor.io/apps/smtp) |
| Dummy | `mirumee.payments.dummy` | [Saleor Dummy Payment App](https://github.com/saleor/dummy-payment-app) |
| DummyCreditCard | `mirumee.payments.dummy_credit_card` | [Saleor Dummy Payment App](https://github.com/saleor/dummy-payment-app) |
| Avalara | `mirumee.taxes.avalara` | [Saleor Avalara AvaTax App](https://apps.saleor.io/apps/avatax) |

We plan to remove deprecated plugins in the future versions of Saleor.
- Add a new `variant` field on `AssignedVariantAttributeValue`. First part of a simplification of Attribute - ProductVariant relation from #12881. by @aniav
