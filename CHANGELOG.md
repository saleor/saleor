# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.23.0 [Unreleased]

### Breaking changes
- Fix missing denormalization of shipping methods metadata when creating an order.
    - Shipping method metadata is now copied to dedicated order fields (`shipping_method_metadata` and `shipping_method_private_metadata`) during checkout-to-order conversion. This ensures that order metadata remains consistent even if the original shipping method is modified or deleted. As a result, updates made to a shipping method's metadata after order creation will no longer be reflected in the order's `shippingMethod.metadata` field.
    - Shipping method metadata is now also denormalized during draft order finalization, ensuring consistent behavior across all order creation flows.
- Fields `options`, `mount` and `target` are removed from `AppExtension` and `AppManifestExtension` types. Use `mountName`, `targetName` and `settings`
- Deprecate the `hasVariants` field on `ProductType`. This setting is a legacy artifact from the former Simple/Configurable product distinction. Products can have multiple variants regardless of this flag. Previously, it only prevented assigning variant attributes to a product type; this restriction will no longer apply.
- Removed Adyen plugin (payment gateway). [Switch to the app](https://docs.saleor.io/developer/app-store/apps/adyen/overview)

### GraphQL API
- Gift cards support as payment method within Transaction API (read more in the [docs](https://docs.saleor.io/developer/gift-cards#using-gift-cards-in-checkout)).
- `Attribute` fields `name`, `slug` and `type` are now non-nullable in schema.

### Webhooks

### Other changes
- Improved page search with search vectors. Pages can now be searched by slug, title, content, attribute values, and page type information.

- Fix send order confirmation email to staff - #18342 by @Shaokun-X

- Validation on `AppExtension` is now removed. Saleor will accept string values for `mount` and `target` from Manifest during App installation and JSON value for `options` field.
Validation is now performed on the frontend (Dashboard). This change increases velocity of features related to apps and extensions, now Dashboard is only entity that ensures the contract
- Improve user search. Use search vector functionality to enable searching users by email address, first name, last name, and addresses.

### Deprecations
- Deprecate the `hasVariants` field on `ProductType`.
