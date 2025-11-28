# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.23.0 [Unreleased]

### Breaking changes
- Fix missing denormalization of shipping methods metadata when creating an order.
    - Shipping method metadata is now copied to dedicated order fields (`shipping_method_metadata` and `shipping_method_private_metadata`) during checkout-to-order conversion. This ensures that order metadata remains consistent even if the original shipping method is modified or deleted. As a result, updates made to a shipping method's metadata after order creation will no longer be reflected in the order's `shippingMethod.metadata` field.
    - Shipping method metadata is now also denormalized during draft order finalization, ensuring consistent behavior across all order creation flows.
- Fields `options`, `mount` and `target` are removed from `AppExtension` and `AppManifestExtension` types. Use `mountName`, `targetName` and `settings`


### GraphQL API

### Webhooks

### Other changes
- Improved page search with search vectors. Pages can now be searched by slug, title, content, attribute values, and page type information.

- Fix send order confirmation email to staff - #18342 by @Shaokun-X

### Deprecations
