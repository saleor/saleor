
# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.21.0 [Unreleased]

### Highlights

### Breaking changes
- Change error codes related to user enumeration bad habbit. Included mutations will now not reveal information in error codes if email was already registered:
  - `AccountRegister`,
    `AccountRegister` mutation will additionaly not return `ID` of the user.
  - `ConfirmAccount`,
  - `RequestPasswordReset`,
  - `SetPassword`, #16243 by @kadewu

### GraphQL API
- Add `translatableContent` to all translation types; add translated object id to all translatable content types - #15617 by @zedzior
- Add a `taxConfiguration` to a `Channel` - #15610 by @Air-t
- Add `stocks` to a `Warehouse` - #15771 by @teddyondieki
- Deprecate the `taxTypes` query - #15802 by @maarcingebala
- Change permissions for `checkout` and `checkouts` queries. Add `HANDLE_PAYMENTS` to required permissions - #16010 by @Air-t
- Change the `CheckoutRemovePromoCode` mutation behavior to throw a `ValidationError` when the promo code is not detached from the checkout. - #16109 by @Air-t

### Saleor Apps

### Other changes
- Remove `prefetched_for_webhook` to legacy payload generators - #15369 by @AjmalPonneth
- Don't raise InsufficientStock for track_inventory=False variants #15475 by @carlosa54
- DB performance improvements in attribute dataloaders - #15474 by @AjmalPonneth
- Calculate order promotions in draft orders - #15459 by @zedzior
- Prevent name overwriting of Product Variants when Updating Product Types - #15670 by @teddyondieki
- Added support for the `BrokerProperties` custom header to webhooks to support Azure Service Bus - #15899 by @patrys
- Extend valid address values - #15877 by @zedzior
- Fixed a rare crash in the introspection query detection code - #15966 by @patrys
- Added HTTP compression telemetry - #16125 by @patrys
- Rewrite `productVariants` resolvers to use JOINs instead of subqueries - #16262 by @maarcingebala
- Implement login throttling - #16219 by @zedzior

# 3.19.0

### Highlights
- Introduce `order` promotion rules that allow applying discounts during checkout calculations when the checkout meets certain conditions. - #14696 by @IKarbowiak, @zedzior
- Introduce gift reward as `order` promotion rule reward - #15259 by @zedzior, @IKarbowiak
- New environment variable `EVENT_PAYLOAD_DELETE_TASK_TIME_LIMIT` to control time limit of `delete_event_payloads_task` - #15396 by @wcislo-saleor

### Breaking changes
- Drop `OrderBulkCreateInput.voucher` field. Use `OrderBulkCreateInput.voucherCode` instead. - #14553 by @zedzior
- Add new `type` field to `PromotionCreateInput`, the field will be required from 3.20 - #14696 by @IKarbowiak, @zedzior
- Do not stack promotion rules within the promotion. Only the best promotion rule will be applied within the promotion. Previously discounts from all rules within the promotion that gives the best discount were applied to the variant's price - #15309 by @korycins
- Disable the `order.discounts` field in sync events to prevent circular calls - #16111 by @zedzior

### GraphQL API

- Add taxes to undiscounted prices - #14095 by @jakubkuc
- Mark as deprecated: `ordersTotal`, `reportProductSales` and `homepageEvents` - #14806 by @8r2y5
- Add `identifier` field to App graphql object. Identifier field is the same as Manifest.id field (explicit ID set by the app).
- Add `skipValidation` field to `AddressInput` - #15985 by @zedzior

### Saleor Apps

### Other changes
- Add missing descriptions to order module - #14845 by @DevilsAutumn
- Unify how undiscounted prices are handled in orders and checkouts - #14780 by @jakubkuc
- Drop demo - #14835 by @fowczarek
- Add JSON serialization immediately after creating observability events to eliminate extra cPickle serialization and deserialization steps - #14992 by @przlada
- Added caching of GraphQL documents for common queries to improve performance - #14843 by @patrys
- Added `VOUCHER_CODES_CREATED` and `VOUCHER_CODES_DELETED` webhooks events. - #14652 by @SzymJ
- Fixed validation for streetAddress1 or streetAddress2 are too long - #13973 by sonbui00
- Clear db leftovers after attribute refactor - #15372 by @IKarbowiak

- Added possibility to break checkout/draft order completion: #15292 by @kadewu
  - Added new field `Shop.availableTaxApps`.
  - Added new input `taxAppId` for `TaxConfigurationUpdateInput` and `TaxConfigurationPerCountryInput`.
  - Added new field `taxAppId` in `TaxConfiguration` and `TaxConfigurationPerCountry`.
  - Added new input `AppInput.identifier`.
  - Added new parameter `identifier` for `create_app` command.
  - When `taxAppId` is provided for `TaxConfiguration` do not allow to finalize `checkoutComplete` or `draftOrderComplete` mutations if Tax App or Avatax plugin didn't respond.
- Add `unique_type` to `OrderLineDiscount` and `CheckoutLineDiscount` models - #15774 by @zedzior
- Allow to skip address validation - #15985 by @zedzior
  - Added new field `Address.validation_skipped`.

# 3.18.0

### Highlights

### Breaking changes

- Drop the `manager.perform_mutation` method. - #16515 by @maarcingebala

### GraphQL API

- Add `CheckoutCustomerNoteUpdate` mutation - #16315 by @pitkes22

### Webhooks

### Other changes

- Added support for numeric and lower-case boolean environment variables - #16313 by @NyanKiyoshi
- Fixed a potential crash when Checkout metadata is accessed with high concurrency - #16411 by @patrys
- Add slugs to product/category/collection/page translations. Allow to query by translated slug - #16449 by @delemeator
- Fixed a crash when the Decimal scalar is passed a non-normal value - #16520 by @patrys
