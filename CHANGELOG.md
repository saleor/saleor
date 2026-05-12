# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.24.0 [Unreleased]

### Breaking changes

- Removed the deprecated Authorize.Net payment gateway plugin (`mirumee.payments.authorize_net`).
- Apps will be no longer to be granted with `MANAGE_APPS` permission. In certain cases, this permission was able to be assigned by the authorized user.
  App with such permission was not able to *act* like an admin app, but permission technically was granted.

  From Saleor 3.24, this app installation with `MANAGE_APPS` permission will be rejected.
  To safely upgrade, ensure that all installed apps do not have this permission.

### GraphQL API

### Webhooks

### Other changes

#### Search improvements

### Deprecations

- Deprecated `Order.paymentStatus` and `Order.paymentStatusDisplay` fields. These fields attempt to consolidate both payment and refund state into a single flag, but cannot accurately represent certain edge cases — for example, an overcharged order that has been partially refunded yet still fully covers the order total. Use `authorizeStatus` and `chargeStatus` instead.
