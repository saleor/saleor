# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/mirumee/saleor/releases) page.

# 3.12.0 [Unreleased]

### Breaking changes

### GraphQL API
- Move `orderSettings` query to `Channel` type - #11417 by @kadewu:
  - Mutation `Channel.channelCreate` and `Channel.channelUpdate` have new `orderSettings` input.
  - Deprecate `Shop.orderSettings` query. Use `Channel.orderSettings` query instead.
  - Deprecate `Shop.orderSettingsUpdate` mutation. Use `Channel.channelUpdate` instead.


### Other changes

- Enhance webhook's subscription query validation. Apply the validation and event inheritance to manifest validation - #11797 by @zedzior
- Fix GraphQL playground when the `operationName` is set across different tabs - #11936 by @zaiste

# 3.11.0

### Highlights

Just so you know, changes mentioned in this section are in a preview state and can be subject to changes in the future.

- Bulk mutations for creating and updating multiple product variants in one mutation call - #11392 by @SzymJ
- Ability to run subscription webhooks in a dry-run mode - #11548 by @zedzior
- Preview of new `where` filtering API which allows joining multiple filters with `AND`/`OR` operators; currently available only in the `attributes` query - #11737 by @IKarbowiak

### GraphQL API

- [Preview] Add `productVariantBulkUpdate` mutation - #11392 by @SzymJ
- [Preview] Add new error handling policies in `productVariantBulkCreate` mutation - #11392 by @SzymJ
- [Preview] Add `webhookDryRun` mutation - #11548 by @zedzior
- [Preview] Add `webhookTrigger` mutation - #11687 by @zedzior
- Fix adding an invalid label to meta fields - #11718 by @IKarbowiak
- Add filter by `checkoutToken` to `Query.orders`. - #11689 by @kadewu
- [Preview] Attribute filters improvement - #11737 by @IKarbowiak
  - introduce `where` option on `attributes` query
  - add `search` option on `attributes` query
  - deprecate `product.variant` field
  - deprecate the following `Attribute` fields: `filterableInStorefront`, `storefrontSearchPosition`, `availableInGrid`.

### Other changes

- Allow `webhookCreate` and `webhookUpdate` mutations to inherit events from `query` field - #11736 by @zedzior
- Add new `PRODUCT_VARIANT_STOCK_UPDATED` event - #11665 by @jakubkuc
- Disable websocket support by default in `uvicorn` worker configuration - #11785 by @NyanKiyoshi
- Fix send user email change notification - #11840 by @jakubkuc

# 3.10.0 [Unreleased]

### Breaking changes

### GraphQL API
- Add ability to filter and sort products of a category - #10917 by @yemeksepeti-cihankarluk, @ogunheper
  - Add `filter` argument to `Category.products`
  - Add `sortBy` argument to `Category.products`
- Extend invoice object types with `Order` references - #11505 by @przlada
  - Add `Invoice.order` field
  - Add `InvoiceRequested.order`, `InvoiceDeleted.order` and `InvoiceSent.order` fields
- Add support for metadata for `Address` model - #11701 by @IKarbowiak
- Allow to mutate objects, by newly added `externalReference` field, instead of Saleor-assigned ID. Apply to following models: #11410 by @zedzior
  - `Product`
  - `ProductVariant`
  - `Attribute`
  - `AttributeValue`
  - `Order`
  - `User`
  - `Warehouse`

### Other changes

- Fix fetching the `checkout.availableCollectionPoints` - #11489 by @IKarbowiak
- Move checkout metadata to separate model - #11264 by @jakubkuc
- Add ability to set a custom Celery queue for async webhook - #11511 by @NyanKiyoshi
- Remove `CUSTOMER_UPDATED` webhook trigger from address mutations - #11395 by @jakubkuc
- Drop `Django.Auth` - #11305 by @fowczarek
- Add address validation to AddressCreate - #11639 by @jakubkuc
- Propagate voucher discount between checkout lines when charge_taxes is disabled - #11632 by @maarcingebala
- Fix stock events triggers - #11714 by @jakubkuc
- Accept the gift card code provided in the input - by @mociepka

# 3.9.0

### Highlights

- Flat tax rates - #9784 by @maarcingebala

### Breaking changes

- Drop Vatlayer plugin - #9784 by @maarcingebala
  - The following fields are no longer used:
    - `Product.chargeTaxes` - from now on, presence of `Product.taxClass` instance decides whether to charge taxes for a product. As a result, the "Charge Taxes" column in CSV product exports returns empty values.
    - `Shop.chargeTaxesOnShipping` - from now on, presence of `ShippingMethod.taxClass` decides whether to charge taxes for a shipping method.
    - `Shop.includeTaxesInPrices`, `Shop.displayGrossPrices` - configuration moved to `Channel.taxConfiguration`.
  - Removed the following plugin manager methods:
    - `assign_tax_code_to_object_meta`
    - `apply_taxes_to_product`
    - `fetch_taxes_data`
    - `get_tax_rate_percentage_value`
    - `update_taxes_for_order_lines`

### GraphQL API

- Add `attribute` field to `AttributeValueTranslatableContent` type. #11028 by @zedzior
- Add new properties in the `Product` type - #10537 by @kadewu
  - Add new fields: `Product.attribute`, `Product.variant`
  - Add `sortBy` argument to `Product.media`
- Allow assigning attribute value using its ID. Add to `AttributeValueInput` dedicated field for each input type. #11206 by @zedzior

### Other changes

- Re-enable 5 minute database connection persistence by default - #11074 + #11100 by @NyanKiyoshi
  <br/>Set `DB_CONN_MAX_AGE=0` to disable this behavior (adds overhead to requests)
- Bump cryptography to 38.0.3: use OpenSSL 3.0.7 - #11126 by @NyanKiyoshi
- Add exif image validation - #11224 by @IKarbowiak
- Include fully qualified API URL `Saleor-Api-Url` in communication with Apps. #11223 by @przlada
- Add metadata on order line payload notifications. #10954 by @CarlesLopezMagem
- Make email authentication case-insensitive. #11284 by @zedzior
- Fix the observability reporter to obfuscate URLs. #11282 by @przlada
- Add HTTP headers filtering to observability reporter. #11285 by @przlada
- Deactivate Webhook before deleting and handle IntegrityErrors - #11239 @jakubkuc

# 3.8.0

### Highlights

- Add tax exemption API for checkouts (`taxExemptionManage` mutation) - #10344 by @SzymJ
- Switch GraphQL Playground to GraphiQL V2

### Breaking changes

- Verify JWT tokens whenever they are provided with the request. Before, they were only validated when an operation required any permissions. For example: when refreshing a token, the request shouldn't include the expired one.

### GraphQL API

- Add the ability to filter by slug. #10578 by @kadewu
  - Affected types: Attribute, Category, Collection, Menu, Page, Product, ProductType, Warehouse
  - Deprecated `slug` in filter for `menus`. Use `slugs` instead
- Add new `products` filters. #10784 by @kadewu
  - `isAvailable`
  - `publishedFrom`
  - `availableFrom`
  - `isVisibleInListing`
- Add the ability to filter payments by a list of ids. #10821 by @kadewu
- Add the ability to filter customers by ids. #10694 by @kadewu
- Add `User.checkouts` field. #10862 by @zedzior
- Add optional field `audience` to mutation `tokenCreate`. If provided, the created tokens will have key `aud` with value: `custom:{audience-input-value}` - #10845 by @korycins
- Use `AttributeValue.name` instead of `AttributeValue.slug` to determine uniqueness of a value instance for dropdown and multi-select attributes. - #10881 by @jakubkuc
- Allow sorting products by `CREATED_AT` field. #10900 by @zedzior
- Add ability to pass metadata directly in create/update mutations for product app models - #10689 by @SzymJ
- Add ability to use SKU argument in `productVariantUpdate`, `productVariantDelete`, `productVariantBulkDelete`, `productVariantStocksUpdate`, `productVariantStocksDelete`, `productVariantChannelListingUpdate` mutations - #10861 by @SzymJ
- Add sorting by `CREATED_AT` field. #10911 by @zedzior
  - Affected types: GiftCard, Page.
  - Deprecated `CREATION_DATE` sort field on Page type. Use `CREATED_AT` instead.

### Other changes

- Reference attribute linking to product variants - #10468 by @IKarbowiak
- Add base shipping price to `Order` - #10771 by @fowczarek
- GraphQL view no longer generates error logs when the HTTP request doesn't contain a GraphQL query - #10901 by @NyanKiyoshi
- Add `iss` field to JWT tokens - #10842 by @korycins
- Drop `py` and `tox` dependencies from dev requirements - #11054 by @NyanKiyoshi

### Saleor Apps

- Add `iss` field to JWT tokens - #10842 by @korycins
- Add new field `audience` to App manifest. If provided, App's JWT access token will have `aud` field. - #10845 by @korycins
- Add new asynchronous events for objects metadata updates - #10520 by @rafalp
  - `CHECKOUT_METADATA_UPDATED`
  - `COLLECTION_METADATA_UPDATED`
  - `CUSTOMER_METADATA_UPDATED`
  - `FULFILLMENT_METADATA_UPDATED`
  - `GIFT_CARD_METADATA_UPDATED`
  - `ORDER_METADATA_UPDATED`
  - `PRODUCT_METADATA_UPDATED`
  - `PRODUCT_VARIANT_METADATA_UPDATED`
  - `SHIPPING_ZONE_METADATA_UPDATED`
  - `TRANSACTION_ITEM_METADATA_UPDATED`
  - `WAREHOUSE_METADATA_UPDATED`
  - `VOUCHER_METADATA_UPDATED`

# 3.7.0

### Highlights

- Allow explicitly setting the name of a product variant - #10456 by @SzymJ
  - Added `name` parameter to the `ProductVariantInput` input
- Add a new stock allocation strategy based on the order of warehouses within a channel - #10416 by @IKarbowiak
  - Add `channelReorderWarehouses` mutation to sort warehouses to set their priority
  - Extend the `Channel` type with the `stockSettings` field
  - Extend `ChannelCreateInput` and `ChannelUpdateInput` with `stockSettings`

### Breaking changes

- Refactor warehouse mutations - #10239 by @IKarbowiak
  - Providing the value in `shippingZone` filed in `WarehouseCreate` mutation will raise a ValidationError.
    Use `WarehouseShippingZoneAssign` to assign shipping zones to a warehouse.

### GraphQL API

- Hide Subscription type from Apollo Federation (#10439) (f5132dfd3)
- Mark `Webhook.secretKey` as deprecated (#10436) (ba445e6e8)

### Saleor Apps

- Trigger the `SALE_DELETED` webhook when deleting sales in bulk (#10461) (2052841e9)
- Add `FULFILLMENT_APPROVED` webhook - #10621 by @IKarbowiak

### Other changes

- Add support for `bcrypt` password hashes - #10346 by @pkucmus
- Add the ability to set taxes configuration per channel in the Avatax plugin - #10445 by @mociepka

# 3.6.0

### Breaking changes

- Drop `django-versatileimagefield` package; add a proxy view to generate thumbnails on-demand - #9988 by @IKarbowiak
  - Drop `create_thumbnails` command
- Change return type from `CheckoutTaxedPricesData` to `TaxedMoney` in plugin manager methods `calculate_checkout_line_total`, `calculate_checkout_line_unit_price` - #9526 by @fowczarek, @mateuszgrzyb, @stnatic

### Saleor Apps

- Add GraphQL subscription support for synchronous webhook events - #9763 by @jakubkuc
- Add support for the CUSTOMER\_\* app mount points (#10163) by @krzysztofwolski
- Add permission group webhooks: `PERMISSION_GROUP_CREATED`, `PERMISSION_GROUP_UPDATED`, `PERMISSION_GROUP_DELETED` - #10214 by @SzymJ
- Add `ACCOUNT_ACTIVATED` and `ACCOUNT_DEACTIVATED` events - #10136 by @tomaszszymanski129
- Allow apps to query data protected by MANAGE_STAFF permission (#10103) (4eb93d3f5)
- Fix returning sale's GraphQL ID in the `SALE_TOGGLE` payload (#10227) (0625c43bf)
- Add descriptions to async webhooks event types (#10250) (7a906bf7f)

### GraphQL API

- Add `CHECKOUT_CALCULATE_TAXES` and `ORDER_CALCULATE_TAXES` to `WebhookEventTypeSyncEnum` #9526 by @fowczarek, @mateuszgrzyb, @stnatic
- Add `forceNewLine` flag to lines input in `CheckoutLinesAdd`, `CheckoutCreate`, `DraftOrderCreate`, `OrderCreate`, `OrderLinesCreate` mutations to support same variant in multiple lines - #10095 by @SzymJ
- Add `VoucherFilter.ids` filter - #10157 by @Jakubkuc
- Add API to display shippable countries for a channel - #10111 by @korycins
- Improve filters' descriptions - #10240 by @dekoza
- Add query for transaction item and extend transaction item type with order (#10154) (b19423a86)

### Plugins

- Add a new method to plugin manager: `get_taxes_for_checkout`, `get_taxes_for_order` - #9526 by @fowczarek, @mateuszgrzyb, @stnatic
- Allow promoting customer users to staff (#10115) (2d56af4e3)
- Allow values of different attributes to share the same slug (#10138) (834d9500b)
- Fix payment status for orders with total 0 (#10147) (ec2c9a820)
- Fix failed event delivery request headers (#10108) (d1b652115)
- Fix create_fake_user ID generation (#10186) (86e2c69a9)
- Fix returning values in JSONString scalar (#10124) (248d2b604)
- Fix problem with updating draft order with active Avalara (#10183) (af270b8c9)
- Make API not strip query params from redirect URL (#10116) (75176e568)
- Update method for setting filter descriptions (#10240) (65643ec7c)
- Add expires option to CELERY_BEAT_SCHEDULE (#10205) (c6c5e46bd)
- Recalculate order prices on marking as paid mutations (#10260) (4e45b83e7)
- Fix triggering `ORDER_CANCELED` event at the end of transaction (#10242) (d9eecb2ca)
- Fix post-migrate called for each app module (#10252) (60205eb56)
- Only handle known URLs (disable appending slash to URLs automatically) - #10290 by @patrys

### Other changes

- Add synchronous tax calculation via webhooks - #9526 by @fowczarek, @mateuszgrzyb, @stnatic
- Allow values of different attributes to share the same slug - #10138 by @IKarbowiak
- Add query for transaction item and extend transaction item type with order - #10154 by @IKarbowiak
- Populate the initial database with default warehouse, channel, category, and product type - #10244 by @jakubkuc
- Fix inconsistent beat scheduling and compatibility with DB scheduler - #10185 by @NyanKiyoshi<br/>
  This fixes the following bugs:
  - `tick()` could decide to never schedule anything else than `send-sale-toggle-notifications` if `send-sale-toggle-notifications` doesn't return `is_due = False` (stuck forever until beat restart or a `is_due = True`)
  - `tick()` was sometimes scheduling other schedulers such as observability to be run every 5m instead of every 20s
  - `is_due()` from `send-sale-toggle-notifications` was being invoked every 5s on django-celery-beat instead of every 60s
  - `send-sale-toggle-notifications` would crash on django-celery-beat with `Cannot convert schedule type <saleor.core.schedules.sale_webhook_schedule object at 0x7fabfdaacb20> to model`
    Usage:
  - Database backend: `celery --app saleor.celeryconf:app beat --scheduler saleor.schedulers.schedulers.DatabaseScheduler`
  - Shelve backend: `celery --app saleor.celeryconf:app beat --scheduler saleor.schedulers.schedulers.PersistentScheduler`
- Fix problem with updating draft order with active Avalara - #10183 by @IKarbowiak
- Fix stock validation and allocation for order with local collection point - #10218 by @IKarbowiak
- Fix stock allocation for order with global collection point - #10225 by @IKarbowiak
- Fix assigning an email address that does not belong to an existing user to draft order (#10320) (97129cf0c)
- Fix gift cards automatic fulfillment (#10325) (6a528259e)

# 3.5.4 [Unreleased]

- Fix ORM crash when generating hundreds of search vector in SQL - #10261 by @NyanKiyoshi
- Fix "stack depth limit exceeded" crash when generating thousands of search vector in SQL - #10279 by @NyanKiyoshi

# 3.5.3 [Released]

- Use custom search vector in order search - #10247 by @fowczarek
- Optimize filtering attributes by dates - #10199 by @tomaszszymanski129

# 3.5.2 [Released]

- Fix stock allocation for order with global collection point - #10225 by @IKarbowiak
- Fix stock validation and allocation for order with local collection point - #10218 @IKarbowiak
- Fix returning GraphQL IDs in the `SALE_TOGGLE` webhook - #10227 by @IKarbowiak

# 3.5.1 [Released]

- Fix inconsistent beat scheduling and compatibility with db scheduler - #10185 by @NyanKiyoshi<br/>
  This fixes the following bugs:

  - `tick()` could decide to never schedule anything else than `send-sale-toggle-notifications` if `send-sale-toggle-notifications` doesn't return `is_due = False` (stuck forever until beat restart or a `is_due = True`)
  - `tick()` was sometimes scheduling other schedulers such as observability to be ran every 5m instead of every 20s
  - `is_due()` from `send-sale-toggle-notifications` was being invoked every 5s on django-celery-beat instead of every 60s
  - `send-sale-toggle-notifications` would crash on django-celery-beat with `Cannot convert schedule type <saleor.core.schedules.sale_webhook_schedule object at 0x7fabfdaacb20> to model`

  Usage:

  - Database backend: `celery --app saleor.celeryconf:app beat --scheduler saleor.schedulers.schedulers.DatabaseScheduler`
  - Shelve backend: `celery --app saleor.celeryconf:app beat --scheduler saleor.schedulers.schedulers.PersistentScheduler`

- Fix problem with updating draft order with active avalara - #10183 by @IKarbowiak
- Fix stock validation and allocation for order with local collection point - #10218 by @IKarbowiak
- Fix stock allocation for order with global collection point - #10225 by @IKarbowiak

# 3.5.0

### GraphQL API

- Allow skipping address validation for checkout mutations (#10084) (7de33b145)
- Add `OrderFilter.numbers` filter - #9967 by @SzymJ
- Expose manifest in the `App` type (#10055) (f0f944066)
- Deprecate `configurationUrl` and `dataPrivacy` fields in apps (#10046) (68bd7c8a2)
- Fix `ProductVariant.created` resolver (#10072) (6c77053a9)
- Add `schemaVersion` field to `Shop` type. #11275 by @zedzior

### Saleor Apps

- Add webhooks `PAGE_TYPE_CREATED`, `PAGE_TYPE_UPDATED` and `PAGE_TYPE_DELETED` - #9859 by @SzymJ
- Add webhooks `ADDRESS_CREATED`, `ADDRESS_UPDATED` and `ADDRESS_DELETED` - #9860 by @SzymJ
- Add webhooks `STAFF_CREATED`, `STAFF_UPDATED` and `STAFF_DELETED` - #9949 by @SzymJ
- Add webhooks `ATTRIBUTE_CREATED`, `ATTRIBUTE_UPDATED` and `ATTRIBUTE_DELETED` - #9991 by @SzymJ
- Add webhooks `ATTRIBUTE_VALUE_CREATED`, `ATTRIBUTE_VALUE_UPDATED` and `ATTRIBUTE_VALUE_DELETED` - #10035 by @SzymJ
- Add webhook `CUSTOMER_DELETED` - #10060 by @SzymJ
- Add webhook for starting and ending sales - #10110 by @IKarbowiak
- Fix returning errors in subscription webhooks payloads - #9905 by @SzymJ
- Build JWT signature when secret key is an empty string (#10139) (c47de896c)
- Use JWS to sign webhooks with secretKey instead of obscure signature (ac065cdce)
- Sign webhook payload using RS256 and private key used JWT infrastructure (#9977) (df7c7d4e8)
- Unquote secret access when calling SQS (#10076) (3ac9714b5)

### Performance

- Add payment transactions data loader (#9940) (799a9f1c9)
- Optimize 0139_fulfil_orderline_token_old_id_created_at migration (#9935) (63073a86b)

### Other changes

- Introduce plain text attribute - #9907 by @IKarbowiak
- Add `metadata` fields to `OrderLine` and `CheckoutLine` models - #10040 by @SzymJ
- Add full-text search for Orders (#9937) (61aa89f06)
- Stop auto-assigning default addresses to checkout - #9933 by @SzymJ
- Fix inaccurate tax calculations - #9799 by @IKarbowiak
- Fix incorrect default value used in `PaymentInput.storePaymentMethod` - #9943 by @korycins
- Improve checkout total base calculations - #10048 by @IKarbowiak
- Improve click & collect and stock allocation - #10043 by @IKarbowiak
- Fix product media reordering (#10118) (de8a1847f)
- Add custom SearchVector class (#10109) (bf74f5efb)
- Improve checkout total base calculations (527b67f9b)
- Fix invoice download URL in send-invoice email (#10014) (667837a09)
- Fix invalid undiscounted total on order line (22ccacb59)
- Fix Avalara for free shipping (#9973) (90c076e33)
- Fix Avalara when voucher with `apply_once_per_order` settings is used (#9959) (fad5cdf46)
- Use Saleor's custom UvicornWorker to avoid lifespan warnings (#9915) (9090814b9)
- Add Azure blob storage support (#9866) (ceee97e83)

# 3.4.0

### Breaking changes

- Hide private metadata in notification payloads - #9849 by @maarcingebala
  - From now on, the `private_metadata` field in `NOTIFY_USER` webhook payload is deprecated and it will return an empty dictionary. This change also affects `AdminEmailPlugin`, `UserEmailPlugin`, and `SendgridEmailPlugin`.

### Other changes

#### GraphQL API

- Add new fields to `Order` type to show authorize/charge status #9795
  - Add new fields to Order type:
    - `totalAuthorized`
    - `totalCharged`
    - `authorizeStatus`
    - `chargeStatus`
  - Add filters to `Order`:
    - `authorizeStatus`
    - `chargeStatus`
- Add mutations for managing a payment transaction attached to order/checkout. - #9564 by @korycins
  - add fields:
    - `order.transactions`
    - `checkout.transactions`
  - add mutations:
    - `transactionCreate`
    - `transactionUpdate`
    - `transactionRequestAction`
  - add new webhook event:
    - `TRANSACTION_ACTION_REQUEST`
- Unify checkout's ID fields. - #9862 by @korycins
  - Deprecate `checkoutID` and `token` in all Checkout's mutations. Use `id` instead.
  - Deprecate `token` in `checkout` query. Use `id` instead.
- Add `unitPrice`, `undiscountedUnitPrice`, `undiscountedTotalPrice` fields to `CheckoutLine` type - #9821 by @fowczarek
- Fix invalid `ADDED_PRODUCTS` event parameter for `OrderLinesCreate` mutation - #9653 by @IKarbowiak
- Update sorting field descriptions - add info where channel slug is required (#9695) (391743098)
- Fix using enum values in permission descriptions (#9697) (dbb783e1f)
- Change gateway validation in `checkoutPaymentCreate` mutation (#9530) (cf1d49bdc)
- Fix invalid `ADDED_PRODUCTS` event parameter for `OrderLinesCreate` mutation (#9653) (a0d8aa8f1)
- Fix resolver for `Product.created` field (#9737) (0af00cb70)
- Allow fetching by id all order data for new orders (#9728) (71c19c951)
- Provide a reference for the rich text format (#9744) (f2207c408)
- Improve event schema field descriptions - #9880 by @patrys

#### Saleor Apps

- Add menu webhooks: `MENU_CREATED`, `MENU_UPDATED`, `MENU_DELETED`, `MENU_ITEM_CREATED`, `MENU_ITEM_UPDATED`, `MENU_ITEM_DELETED` - #9651 by @SzymJ
- Add voucher webhooks: `VOUCHER_CREATED`, `VOUCHER_UPDATED`, `VOUCHER_DELETED` - #9657 by @SzymJ
- Add app webhooks: `APP_INSTALLED`, `APP_UPDATED`, `APP_DELETED`, `APP_STATUS_CHANGED` - #9698 by @SzymJ
- Add warehouse webhoks: `WAREHOUSE_CREATED`, `WAREHOUSE_UPDATED`, `WAREHOUSE_DELETED` - #9746 by @SzymJ
- Expose order alongside fulfillment in fulfillment-based subscriptions used by webhooks (#9847)
- Fix webhooks payload not having field for `is_published` (#9800) (723f93c50)
- Add support for `ORDER_*` mounting points for Apps (#9694) (cc728ef7e)
- Add missing shipping method data in order and checkout events payloads. (#9692) (dabd1a221)
- Use the human-readable order number in notification payloads (#9863) (f10c5fd5f)

#### Models

- Migrate order discount id from int to UUID - #9729 by @IKarbowiak
  - Changed the order discount `id` from `int` to `UUID`, the old ids still can be used
    for old order discounts.
- Migrate order line id from int to UUID - #9637 by @IKarbowiak
  - Changed the order line `id` from `int` to `UUID`, the old ids still can be used
    for old order lines.
- Migrate checkout line id from int to UUID - #9675 by @IKarbowiak
  - Changed the checkout line `id` from `int` to `UUID`, the old ids still can be used
    for old checkout lines.

#### Performance

- Fix memory consumption of `delete_event_payloads_task` (#9806) (2823edc68)
- Add webhook events dataloader (#9790) (e88eef35e)
- Add dataloader for fulfillment warehouse resolver (#9740) (9d14fadb2)
- Fix order type resolvers performance (#9723) (13b5a95e7)
- Improve warehouse filtering performance (#9622) (a1a7a223b)
- Add dataloader for fulfillment lines (#9707) (68fb4bf4a)

#### Other

- Observability reporter - #9803 by @przlada
- Update sample products set - #9796 by @mirekm
- Fix for sending incorrect prices to Avatax - #9633 by @korycins
- Fix tax-included flag sending to Avatax - #9820
- Fix AttributeError: 'Options' object has no attribute 'Model' in `search_tasks.py` - #9824
- Fix Braintree merchant accounts mismatch error - #9778
- Stricter signatures for resolvers and mutations - #9649

# 3.3.1

- Drop manual calls to emit post_migrate in migrations (#9647) (b32308802)
- Fix search indexing of empty variants (#9640) (31833a717)

# 3.3.0

### Breaking changes

- PREVIEW_FEATURE: replace error code `NOT_FOUND` with `CHECKOUT_NOT_FOUND` for mutation `OrderCreateFromCheckout` - #9569 by @korycins

### Other changes

- Fix filtering product attributes by date range - #9543 by @IKarbowiak
- Fix for raising Permission Denied when anonymous user calls `checkout.customer` field - #9573 by @korycins
- Use fulltext search for products (#9344) (4b6f25964) by @patrys
- Precise timestamps for publication dates - #9581 by @IKarbowiak
  - Change `publicationDate` fields to `publishedAt` date time fields.
    - Types and inputs where `publicationDate` is deprecated and `publishedAt` field should be used instead:
      - `Product`
      - `ProductChannelListing`
      - `CollectionChannelListing`
      - `Page`
      - `PublishableChannelListingInput`
      - `ProductChannelListingAddInput`
      - `PageCreateInput`
      - `PageInput`
  - Change `availableForPurchaseDate` fields to `availableForPurchaseAt` date time field.
    - Deprecate `Product.availableForPurchase` field, the `Product.availableForPurchaseAt` should be used instead.
    - Deprecate `ProductChannelListing.availableForPurchase` field, the `ProductChannelListing.availableForPurchaseAt` should be used instead.
  - Deprecate `publicationDate` on `CollectionInput` and `CollectionCreateInput`.
  - Deprecate `PUBLICATION_DATE` in `CollectionSortField`, the `PUBLISHED_AT` should be used instead.
  - Deprecate `PUBLICATION_DATE` in `PageSortField`, the `PUBLISHED_AT` should be used instead.
  - Add a new column `published at` to export products. The new field should be used instead of `publication_date`.
- Add an alternative API for fetching metadata - #9231 by @patrys
- New webhook events related to gift card changes (#9588) (52adcd10d) by @SzymJ
- New webhook events for changes related to channels (#9570) (e5d78c63e) by @SzymJ
- Tighten the schema types for output fields (#9605) (81418cb4c) by @patrys
- Include permissions in schema descriptions of protected fields (#9428) (f0a988e79) by @maarcingebala
- Update address database (#9585) (1f5e84e4a) by @patrys
- Handle pagination with invalid cursor that is valid base64 (#9521) (3c12a1e95) by @jakubkuc
- Handle all Braintree errors (#9503) (20f21c34a) by @L3str4nge
- Fix `recalculate_order` dismissing weight unit (#9527) (9aea31774)
- Fix filtering product attributes by date range - #9543 by @IKarbowiak
- Fix for raising Permission Denied when anonymous user calls `checkout.customer` field - #9573 by @korycins
- Optimize stock warehouse resolver performance (955489bff) by @tomaszszymanski129
- Improve shipping zone filters performance (#9540) (7841ec536) by @tomaszszymanski129

# 3.2.0

### Breaking changes

- Convert IDs from DB to GraphQL format in all notification payloads (email plugins and the `NOTIFY` webhook)- #9388 by @L3str4nge
- Migrate order id from int to UUID - #9324 by @IKarbowiak
  - Changed the order `id` changed from `int` to `UUID`, the old ids still can be used
    for old orders.
  - Deprecated the `order.token` field, the `order.id` should be used instead.
  - Deprecated the `token` field in order payload, the `id` field should be used
    instead.
- Enable JWT expiration by default - #9483 by @maarcingebala

### Other changes

#### Saleor Apps

- Introduce custom prices - #9393 by @IKarbowiak
  - Add `HANDLE_CHECKOUTS` permission (only for apps)
- Add subscription webhooks (#9394) @jakubkuc
- Add `language_code` field to webhook payload for `Order`, `Checkout` and `Customer` - #9433 by @rafalp
- Refactor app tokens - #9438 by @IKarbowiak
  - Store app tokens hashes instead of plain text.
- Add category webhook events - #9490 by @SzymJ
- Fix access to own resources by App - #9425 by @korycins
- Add `handle_checkouts` permission - #9402 by @korycins
- Return `user_email` or order user's email in order payload `user_email` field (#9419) (c2d248655)
- Mutation `CategoryBulkDelete` now trigger `category_delete` event - #9533 by @SzymJ
- Add webhooks `SHIPPING_PRICE_CREATED`, `SHIPPING_PRICE_UPDATED`, `SHIPPING_PRICE_DELETED`, `SHIPPING_ZONE_CREATED`, `SHIPPING_ZONE_UPDATED`, `SHIPPING_ZONE_DELETED` - #9522 by @SzymJ

#### Plugins

- Add OpenID Connect Plugin - #9406 by @korycins
- Allow plugins to create their custom error code - #9300 by @LeOndaz

#### Other

- Use full-text search for products search API - #9344 by @patrys

- Include required permission in mutations' descriptions - #9363 by @maarcingebala
- Make GraphQL list items non-nullable - #9391 by @maarcingebala
- Port a better schema printer from GraphQL Core 3.x - #9389 by @patrys
- Fix failing `checkoutCustomerAttach` mutation - #9401 by @IKarbowiak
- Add new mutation `orderCreateFromCheckout` - #9343 by @korycins
- Assign missing user to context - #9520 by @korycins
- Add default ordering to order discounts - #9517 by @fowczarek
- Raise formatted error when trying to assign assigned media to variant - #9496 by @L3str4nge
- Update `orderNumber` field in `OrderEvent` type - #9447 by @IKarbowiak
- Do not create `AttributeValues` when values are not provided - #9446 @IKarbowiak
- Add response status code to event delivery attempt - #9456 by @przlada
- Don't rely on counting objects when reindexing - #9442 by @patrys
- Allow filtering attribute values by ids - #9399 by @IKarbowiak
- Fix errors handling for `orderFulfillApprove` mutation - #9491 by @SzymJ
- Fix shipping methods caching - #9472 by @tomaszszymanski129
- Fix payment flow - #9504 by @IKarbowiak
- Fix etting external methods did not throw an error when that method didn't exist - #9498 by @SethThoburn
- Reduce placeholder image size - #9484 by @jbergstroem
- Improve menus filtering performance - #9539 by @tomaszszymanski129
- Remove EventDeliveries without webhooks and make webhook field non-nullable - #9507 by @jakubkuc
- Improve discount filters performance - #9541 by @tomaszszymanski129
- Change webhooks to be called on commit in atomic transactions - #9532 by @jakubkuc
- Drop distinct and icontains in favor of ilike in apps filtering - #9534 by @tomaszszymanski129
- Refactor csv filters to improve performance - #9535 by @tomaszszymanski129
- Improve attributes filters performance - #9542 by @tomaszszymanski129
- Rename models fields from created to created_at - #9537 by @IKarbowiak

# 3.1.10

- Migration dependencies fix - #9590 by @SzymJ

# 3.1.9

- Use ordering by PK in `queryset_in_batches` (#9493) (4e49c52d2)

# 3.1.8

- Fix shipping methods caching (#9472) (0361f40)
- Fix logging of excessive logger informations (#9441) (d1c5d26)

# 3.1.7

- Handle `ValidationError` in metadata mutations (#9380) (75deaf6ea)
- Fix order and checkout payload serializers (#9369) (8219b6e9b)
- Fix filtering products ordered by collection (#9285) (57aed02a2)
- Cast `shipping_method_id` to int (#9364) (8d0584710)
- Catch "update_fields did not affect any rows" errors and return response with message (#9225) (29c7644fc)
- Fix "str object has no attribute input type" error (#9345) (34c64b5ee)
- Fix `graphene-django` middleware imports (#9360) (2af1cc55d)
- Fix preorders to update stock `quantity_allocated` (#9308) (8cf83df81)
- Do not drop attribute value files when value is deleted (#9320) (57b2888bf)
- Always cast database ID to int in data loader (#9340) (dbc5ec3e3)
- Fix removing references when user removes the referenced object (#9162) (68b33d95a)
- Pass correct list of order lines to `order_added_products_event` (#9286) (db3550f64)
- Fix flaky order payload serializer test (#9387) (d73bd6f9d)

# 3.1.6

- Fix unhandled GraphQL errors after removing `graphene-django` (#9398) (4090e6f2a)

# 3.1.5

- Fix checkout payload (#9333) (61b928e33)
- Revert "3.1 Add checking if given attributes are variant attributes in ProductVariantCreate mutation (#9134)" (#9334) (dfee09db3)

# 3.1.4

- Add `CREATED_AT` and `LAST_MODIFIED_AT` sorting to some GraphQL fields - #9245 by @rafalp
  - Added `LAST_MODIFIED_AT` sort option to `ExportFileSortingInput`
  - Added `CREATED_AT` and `LAST_MODIFIED_AT` sort options to `OrderSortingInput` type
  - Added `LAST_MODIFIED_AT` and `PUBLISHED_AT` sort options to `ProductOrder` type
  - Added `CREATED_AT` and `LAST_MODIFIED_AT` sort options to `SaleSortingInput` type
  - Added `CREATED_AT` and `LAST_MODIFIED_AT` sort options to `UserSortingInput` type
  - Added `ProductVariantSortingInput` type with `LAST_MODIFIED_AT` sort option
  - Deprecated `UPDATED_AT` sort option on `ExportFileSortingInput`
  - Deprecated `LAST_MODIFIED` and `PUBLICATION_DATE` sort options on `ProductOrder` type
  - Deprecated `CREATION_DATE` sort option on `OrderSortingInput` type
- Fix sending empty emails (#9317) (3e8503d8a)
- Add checking if given attributes are variant attributes in ProductVariantCreate mutation (#9134) (409ca7d23)
- Add command to update search indexes (#9315) (fdd81bbfe)
- Upgrade required Node and NPM versions used by release-it tool (#9293) (3f96a9c30)
- Update link to community pages (#9291) (2d96f5c60)
- General cleanup (#9282) (78f59c6a3)
- Fix `countries` resolver performance (#9318) (dc58ef2c4)
- Fix multiple refunds in NP Atobarai - #9222
- Fix dataloaders, filter out productmedia to be removed (#9299) (825ec3cad)
- Fix migration issue between 3.0 and main (#9323) (fec80cd63)
- Drop wishlist models (#9313) (7c9576925)

# 3.1.3

- Add command to update search indexes (#9315) (6be8461c0)
- Fix countries resolver performance (#9318) (e177f3957)

# 3.1.2

### Breaking changes

- Require `MANAGE_ORDERS` permission in `User.orders` query (#9128) (521dfd639)
  - only staff with `manage orders` and can fetch customer orders
  - the customer can fetch his own orders, except drafts

### Other changes

- Fix failing `on_failure` export tasks method (#9160) (efab6db9d)
- Fix mutations breaks on partially invalid IDs (#9227) (e3b6df2eb)
- Fix voucher migrations (#9249) (3c565ba0c)
- List the missing permissions where possible (#9250) (f8df1aa0d)
- Invalidate stocks dataloader (#9188) (e2366a5e6)
- Override `graphene.JSONString` to have more meaningful message in error message (#9171) (2a0c5a71a)
- Small schema fixes (#9224) (932e64808)
- Support Braintree subaccounts (#9191) (035bf705c)
- Split checkout mutations into separate files (#9266) (1d37b0aa3)

# 3.1.1

- Drop product channel listings when removing last available variant (#9232) (b92d3b686)
- Handle product media deletion in a Celery task (#9187) (2b10fc236)
- Filter Customer/Order/Sale/Product/ProductVariant by datetime of last modification (#9137) (55a845c7b)
- Add support for hiding plugins (#9219) (bc9405307)
- Fix missing update of payment methods when using stored payment method (#9158) (ee4bf520b)
- Fix invalid paths in VCR cassettes (#9236) (f6c268d2e)
- Fix Razorpay comment to be inline with code (#9238) (de417af24)
- Remove `graphene-federation` dependency (#9184) (dd43364f7)

# 3.1.0

### Breaking changes

#### Plugins

- Don't run plugins when calculating checkout's total price for available shipping methods resolution - #9121 by @rafalp
  - Use either net or gross price depending on store configuration.

### Other changes

#### Saleor Apps

- Add API for webhook payloads and deliveries - #8227 by @jakubkuc
- Extend app by `AppExtension` - #7701 by @korycins
- Add webhooks for stock changes: `PRODUCT_VARIANT_OUT_OF_STOCK` and `PRODUCT_VARIANT_BACK_IN_STOCK` - #7590 by @mstrumeck
- Add `COLLECTION_CREATED`, `COLLECTION_UPDATED`, `COLLECTION_DELETED` events and webhooks - #8974 by @rafalp
- Add draft orders webhooks by @jakubkuc
- Add support for providing shipping methods by Saleor Apps - #7975 by @bogdal:
  - Add `SHIPPING_LIST_METHODS_FOR_CHECKOUT` sync webhook
- Add sales webhooks - #8157 @kuchichan
- Allow fetching unpublished pages by apps with manage pages permission - #9181 by @IKarbowiak

#### Metadata

- Add ability to use metadata mutations with tokens as an identifier for orders and checkouts - #8426 by @IKarbowiak

#### Attributes

- Introduce swatch attributes - #7261 by @IKarbowiak
- Add `variant_selection` to `ProductAttributeAssign` operations - #8235 by @kuchichan
- Refactor attributes validation - #8905 by @IKarbowiak
  - in create mutations: require all required attributes
  - in update mutations: do not require providing any attributes; when any attribute is given, validate provided values.

#### Other features and changes

- Add gift cards - #7827 by @IKarbowiak, @tomaszszymanski129
- Add Click & Collect - #7673 by @kuchichan
- Add fulfillment confirmation - #7675 by @tomaszszymanski129
- Make SKU an optional field on `ProductVariant` - #7633 by @rafalp
- Possibility to pass metadata in input of `checkoutPaymentCreate` - #8076 by @mateuszgrzyb
- Add `ExternalNotificationTrigger` mutation - #7821 by @mstrumeck
- Extend `accountRegister` mutation to consume first & last name - #8184 by @piotrgrundas
- Introduce sales/vouchers per product variant - #8064 by @kuchichan
- Batch loads in queries for Apollo Federation - #8273 by @rafalp
- Reserve stocks for checkouts - #7589 by @rafalp
- Add query complexity limit to GraphQL API - #8526 by @rafalp
- Add `quantity_limit_per_customer` field to ProductVariant #8405 by @kuchichan
- Make collections names non-unique - #8986 by @rafalp
- Add validation of unavailable products in the checkout. Mutations: `CheckoutShippingMethodUpdate`,
  `CheckoutAddPromoCode`, `CheckoutPaymentCreate` will raise a ValidationError when product in the checkout is
  unavailable - #8978 by @IKarbowiak
- Add `withChoices` flag for Attribute type - #7733 by @dexon44
- Update required permissions for attribute options - #9204 by @IKarbowiak
  - Product attribute options can be fetched by requestors with manage product types and attributes permission.
  - Page attribute options can be fetched by requestors with manage page types and attributes permission.
- Deprecate interface field `PaymentData.reuse_source` - #7988 by @mateuszgrzyb
- Deprecate `setup_future_usage` from `checkoutComplete.paymentData` input - will be removed in Saleor 4.0 - #7994 by @mateuszgrzyb
- Fix shipping address issue in `availableCollectionPoints` resolver for checkout - #8143 by @kuchichan
- Fix cursor-based pagination in products search - #8011 by @rafalp
- Fix crash when querying external shipping methods `translation` field - #8971 by @rafalp
- Fix crash when too long translation strings were passed to `translate` mutations - #8942 by @rafalp
- Raise ValidationError in `CheckoutAddPromoCode`, `CheckoutPaymentCreate` when product in the checkout is
  unavailable - #8978 by @IKarbowiak
- Remove `graphene-django` dependency - #9170 by @rafalp
- Fix disabled warehouses appearing as valid click and collect points when checkout contains only preorders - #9052 by @rafalp
- Fix failing `on_failure` export tasks method - #9160 by @IKarbowiak

# 3.0.0

### Breaking changes

#### Behavior

- Add multichannel - #6242 by @fowczarek @d-wysocki
- Add email interface as a plugin - #6301 by @korycins
- Add unconfirmed order editing - #6829 by @tomaszszymanski129
  - Removed mutations for draft order lines manipulation: `draftOrderLinesCreate`, `draftOrderLineDelete`, `draftOrderLineUpdate`
  - Added instead: `orderLinesCreate`, `orderLineDelete`, `orderLineUpdate` mutations instead.
  - Order events enums `DRAFT_ADDED_PRODUCTS` and `DRAFT_REMOVED_PRODUCTS` are now `ADDED_PRODUCTS` and `REMOVED_PRODUCTS`
- Remove resolving users location from GeoIP; drop `PaymentInput.billingAddress` input field - #6784 by @maarcingebala
- Always create new checkout in `checkoutCreate` mutation - #7318 by @IKarbowiak
  - deprecate `created` return field on `checkoutCreate` mutation
- Return empty values list for attribute without choices - #7394 by @fowczarek
  - `values` for attributes without choices from now are empty list.
  - attributes with choices - `DROPDOWN` and `MULTISELECT`
  - attributes without choices - `FILE`, `REFERENCE`, `NUMERIC` and `RICH_TEXT`
- Unify checkout identifier in checkout mutations and queries - #7511 by @IKarbowiak
- Propagate sale and voucher discounts over specific lines - #8793 by @korycins
  - Use a new interface for response received from plugins/pluginManager. Methods `calculate_checkout_line_unit_price`
    and `calculate_checkout_line_total` returns `TaxedPricesData` instead of `TaxedMoney`.
- Attach sale discount info to the line when adding variant to order - #8821 by @IKarbowiak
  - Use a new interface for the response received from plugins/pluginManager.
    Methods `calculate_order_line_unit` and `calculate_order_line_total` returns
    `OrderTaxedPricesData` instead of `TaxedMoney`.
  - Rename checkout interfaces: `CheckoutTaxedPricesData` instead of `TaxedPricesData`
    and `CheckoutPricesData` instead of `PricesData`
- Sign JWT tokens with RS256 instead of HS256 - #7990 by @korycins
- Add support for filtering available shipping methods by Saleor Apps - #8399 by @kczan, @stnatic
  - Introduce `ShippingMethodData` interface as a root object type for ShippingMethod object
- Limit number of user addresses - #9173 by @IKarbowiak

#### GraphQL Schema

- Drop deprecated meta mutations - #6422 by @maarcingebala
- Drop deprecated service accounts and webhooks API - #6431 by @maarcingebala
- Drop deprecated fields from the `ProductVariant` type: `quantity`, `quantityAllocated`, `stockQuantity`, `isAvailable` - #6436 by @maarcingebala
- Drop authorization keys API - #6631 by @maarcingebala
- Drop `type` field from `AttributeValue` type - #6710 by @IKarbowiak
- Drop deprecated `taxRate` field from `ProductType` - #6795 by @d-wysocki
- Drop deprecated queries and mutations - #7199 by @IKarbowiak
  - drop `url` field from `Category` type
  - drop `url` field from `Category` type
  - drop `url` field from `Product` type
  - drop `localized` fild from `Money` type
  - drop `permissions` field from `User` type
  - drop `navigation` field from `Shop` type
  - drop `isActive` from `AppInput`
  - drop `value` from `AttributeInput`
  - drop `customerId` from `checkoutCustomerAttach`
  - drop `stockAvailability` argument from `products` query
  - drop `created` and `status` arguments from `orders` query
  - drop `created` argument from `draftOrders` query
  - drop `productType` from `ProductFilter`
  - deprecate specific error fields `<TypeName>Errors`, typed `errors` fields and remove deprecation
- Drop top-level `checkoutLine` query from the schema with related resolver, use `checkout` query instead - #7623 by @dexon44
- Change error class in `CollectionBulkDelete` to `CollectionErrors` - #7061 by @d-wysocki
- Make quantity field on `StockInput` required - #7082 by @IKarbowiak
- Add description to shipping method - #7116 by @IKarbowiak
  - `ShippingMethod` was extended with `description` field.
  - `ShippingPriceInput` was extended with `description` field
  - Extended `shippingPriceUpdate`, `shippingPriceCreate` mutation to add/edit description
  - Input field in `shippingPriceTranslate` changed to `ShippingPriceTranslationInput`
- Split `ShippingMethod` into `ShippingMethod` and `ShippingMethodType` (#8399):
  - `ShippingMethod` is used to represent methods offered for checkouts and orders
  - `ShippingMethodType` is used to manage shipping method configurations in Saleor
  - Deprecate `availableShippingMethods` on `Order` and `Checkout`. Use `shippingMethods` and refer to the `active` field instead

#### Saleor Apps

- Drop `CHECKOUT_QUANTITY_CHANGED` webhook - #6797 by @d-wysocki
- Change the payload of the order webhook to handle discounts list - #6874 by @korycins:
  - added fields: `Order.discounts`, `OrderLine.unit_discount_amount`, `OrderLine.unit_discount_type`, `OrderLine.unit_discount_reason`,
  - removed fields: `Order.discount_amount`, `Order.discount_name`, `Order.translated_discount_name`
- Remove triggering a webhook event `PRODUCT_UPDATED` when calling `ProductVariantCreate` mutation. Use `PRODUCT_VARIANT_CREATED` instead - #6963 by @piotrgrundas
- Make `order` property of invoice webhook payload contain order instead of order lines - #7081 by @pdblaszczyk
  - Affected webhook events: `INVOICE_REQUESTED`, `INVOICE_SENT`, `INVOICE_DELETED`
- Added `CHECKOUT_FILTER_SHIPPING_METHODS`, `ORDER_FILTER_SHIPPING_METHODS` sync webhooks - #8399 by @kczan, @stnatic

#### Plugins

- Drop `apply_taxes_to_shipping_price_range` plugin hook - #6746 by @maarcingebala
- Refactor listing payment gateways - #7050 by @maarcingebala:
  - Breaking changes in plugin methods: removed `get_payment_gateway` and `get_payment_gateway_for_checkout`; instead `get_payment_gateways` was added.
- Improve checkout performance - introduce `CheckoutInfo` data class - #6958 by @IKarbowiak;
  - Introduced changes in plugin methods definitions in the following methods, the `checkout` parameter changed to `checkout_info`:
    - `calculate_checkout_total`
    - `calculate_checkout_subtotal`
    - `calculate_checkout_shipping`
    - `get_checkout_shipping_tax_rate`
    - `calculate_checkout_line_total`
    - `calculate_checkout_line_unit_price`
    - `get_checkout_line_tax_rate`
    - `preprocess_order_creation`
  - `preprocess_order_creation` was extend with `lines_info` parameter
- Fix Avalara caching - #7036 by @fowczarek:
  - Introduced changes in plugin methods definitions:
    - `calculate_checkout_line_total` was extended with `lines` parameter
    - `calculate_checkout_line_unit_price` was extended with `lines` parameter
    - `get_checkout_line_tax_rate` was extended with `lines` parameter
  - To get proper taxes we should always send the whole checkout to Avalara.
- Extend plugins manager to configure plugins for each plugins - #7198 by @korycins:
  - Introduce changes in API:
    - `paymentInitialize` - add `channel` parameter. Optional when only one channel exists.
    - `pluginUpdate` - add `channel` parameter.
    - `availablePaymentGateways` - add `channel` parameter.
    - `storedPaymentSources` - add `channel` parameter.
    - `requestPasswordReset` - add `channel` parameter.
    - `requestEmailChange` - add `channel` parameter.
    - `confirmEmailChange` - add `channel` parameter.
    - `accountRequestDeletion` - add `channel` parameter.
    - change structure of type `Plugin`:
      - add `globalConfiguration` field for storing configuration when a plugin is globally configured
      - add `channelConfigurations` field for storing plugin configuration for each channel
      - removed `configuration` field, use `globalConfiguration` and `channelConfigurations` instead
    - change structure of input `PluginFilterInput`:
      - add `statusInChannels` field
      - add `type` field
      - removed `active` field. Use `statusInChannels` instead
  - Change plugin webhook endpoint - #7332 by @korycins.
    - Use /plugins/channel/<channel_slug>/<plugin_id> for plugins with channel configuration
    - Use /plugins/global/<plugin_id> for plugins with global configuration
    - Remove /plugin/<plugin_id> endpoint
- Fix doubling price in checkout for products without tax - #7056 by @IKarbowiak:
  - Introduce changes in plugins method:
    - `calculate_checkout_subtotal` has been dropped from plugins;
    - for correct subtotal calculation, `calculate_checkout_line_total` must be set (manager method for calculating checkout subtotal uses `calculate_checkout_line_total` method)
- Deprecated Stripe plugin - will be removed in Saleor 4.0
  - rename `StripeGatewayPlugin` to `DeprecatedStripeGatewayPlugin`.
  - introduce new `StripeGatewayPlugin` plugin.

### Other changes

#### Features

- Migrate from Draft.js to Editor.js format - #6430, #6456 by @IKarbowiak
- Allow using `Bearer` as an authorization prefix - #6996 by @korycins
- Add product rating - #6284 by @korycins
- Add order confirmation - #6498 by @tomaszszymanski12
- Extend Vatlayer functionalities - #7101 by @korycins:
  - Allow users to enter a list of exceptions (country ISO codes) that will use the source country rather than the destination country for tax purposes.
  - Allow users to enter a list of countries for which no VAT will be added.
- Extend order with origin and original order values - #7326 by @IKarbowiak
- Allow impersonating user by an app/staff - #7754 by @korycins:
  - Add `customerId` to `checkoutCustomerAttach` mutation
  - Add new permission `IMPERSONATE_USER`
- Add possibility to apply a discount to order/order line with status `DRAFT` - #6930 by @korycins
- Implement database read replicas - #8516, #8751 by @fowczarek
- Propagate sale and voucher discounts over specific lines - #8793 by @korycins
  - The created order lines from checkout will now have fulfilled all undiscounted fields with a default price value
    (without any discounts).
  - Order line will now include a voucher discount (in the case when the voucher is for specific products or have a
    flag apply_once_per_order). In that case, `Order.discounts` will not have a relation to `OrderDiscount` object.
  - Webhook payload for `OrderLine` will now include two new fields, `sale_id` (graphql ID of applied sale) and
    `voucher_code` (code of the valid voucher applied to this line).
  - When any sale or voucher discount was applied, `line.discount_reason` will be fulfilled.
  - New interface for handling more data for prices: `PricesData` and `TaxedPricesData` used in checkout calculations
    and in plugins/pluginManager.
- Attach sale discount info to the line when adding variant to order - #8821 by @IKarbowiak
  - Rename checkout interfaces: `CheckoutTaxedPricesData` instead of `TaxedPricesData`
    and `CheckoutPricesData` instead of `PricesData`
  - New interface for handling more data for prices: `OrderTaxedPricesData` used in plugins/pluginManager.
- Add uploading video URLs to product gallery - #6838 by @GrzegorzDerdak
- Add generic `FileUpload` mutation - #6470 by @IKarbowiak

#### Metadata

- Allow passing metadata to `accountRegister` mutation - #7152 by @piotrgrundas
- Copy metadata fields when creating reissue - #7358 by @IKarbowiak
- Add metadata to shipping zones and shipping methods - #6340 by @maarcingebala
- Add metadata to menu and menu item - #6648 by @tomaszszymanski129
- Add metadata to warehouse - #6727 by @d-wysocki
- Added support for querying objects by metadata fields - #6683 by @LeOndaz, #7421 by @korycins
- Change metadata mutations to use token for order and checkout as an identifier - #8542 by @IKarbowiak
  - After changes, using the order `id` for changing order metadata is deprecated

#### Attributes

- Add rich text attribute input - #7059 by @piotrgrundas
- Support setting value for AttributeValue mutations - #7037 by @piotrgrundas
- Add boolean attributes - #7454 by @piotrgrundas
- Add date & date time attributes - #7500 by @piotrgrundas
- Add file attributes - #6568 by @IKarbowiak
- Add page reference attributes - #6624 by @IKarbowiak
- Add product reference attributes - #6711 by @IKarbowiak
- Add numeric attributes - #6790 by @IKarbowiak
- Add `withChoices` flag for Attribute type - #7733 by @CossackDex
- Return empty results when filtering by non-existing attribute - #7025 by @maarcingebala
- Add Page Types - #6261 by @IKarbowiak

#### Plugins

- Add interface for integrating the auth plugins - #6799 by @korycins
- Add Sendgrid plugin - #6793 by @korycins
- Trigger `checkout_updated` plugin method for checkout metadata mutations - #7392 by @maarcingebala

#### Saleor Apps

- Add synchronous payment webhooks - #7044 by @maarcingebala
- Add `CUSTOMER_UPDATED` webhook, add addresses field to customer `CUSTOMER_CREATED` webhook - #6898 by @piotrgrundas
- Add `PRODUCT_VARIANT_CREATED`, `PRODUCT_VARIANT_UPDATED`, `PRODUCT_VARIANT_DELETED` webhooks, fix attributes field for `PRODUCT_CREATED`, `PRODUCT_UPDATED` webhooks - #6963 by @piotrgrundas
- Trigger `PRODUCT_UPDATED` webhook for collections and categories mutations - #7051 by @d-wysocki
- Extend order webhook payload with fulfillment fields - #7364, #7347 by @korycins
  - fulfillments extended with:
    - `total_refund_amount`
    - `shipping_refund_amount`
    - `lines`
  - fulfillment lines extended with:
    - `total_price_net_amount`
    - `total_price_gross_amount`
    - `undiscounted_unit_price_net`
    - `undiscounted_unit_price_gross`
    - `unit_price_net`
- Extend order payload with undiscounted prices and add psp_reference to payment model - #7339 by @IKarbowiak
  - order payload extended with the following fields:
    - `undiscounted_total_net_amount`
    - `undiscounted_total_gross_amount`
    - `psp_reference` on `payment`
  - order lines extended with:
    - `undiscounted_unit_price_net_amount`
    - `undiscounted_unit_price_gross_amount`
    - `undiscounted_total_price_net_amount`
    - `undiscounted_total_price_gross_amount`
- Add `product_id`, `product_variant_id`, `attribute_id` and `page_id` when it is possible for `AttributeValue` translations webhook - #7783 by @fowczarek
- Add draft orders webhooks - #8102 by @jakubkuc
- Add page webhooks: `PAGE_CREATED`, `PAGE_UPDATED` and `PAGE_DELETED` - #6787 by @d-wysocki
- Add `PRODUCT_DELETED` webhook - #6794 by @d-wysocki
- Add `page_type_id` in translations webhook - #7825 by @fowczarek
- Fix failing account mutations for app - #7569 by @IKarbowiak
- Add app support for events - #7622 by @IKarbowiak
- Fix creating translations with app - #6804 by @krzysztofwolski
- Change the `app` query to return info about the currently authenticated app - #6928 by @d-wysocki
- Mark `X-` headers as deprecated and add headers without prefix. All deprecated headers will be removed in Saleor 4.0 - #8179 by @L3str4nge
  - X-Saleor-Event -> Saleor-Event
  - X-Saleor-Domain -> Saleor-Domain
  - X-Saleor-Signature -> Saleor-Signature
  - X-Saleor-HMAC-SHA256 -> Saleor-HMAC-SHA256

#### Other changes

- Add query contains only schema validation - #6827 by @fowczarek
- Add introspection caching - #6871 by @fowczarek
- Fix Sentry reporting - #6902 by @fowczarek
- Deprecate API fields `Order.discount`, `Order.discountName`, `Order.translatedDiscountName` - #6874 by @korycins
- Fix argument validation in page resolver - #6960 by @fowczarek
- Drop `data` field from checkout line model - #6961 by @fowczarek
- Fix `totalCount` on connection resolver without `first` or `last` - #6975 by @fowczarek
- Fix variant resolver on `DigitalContent` - #6983 by @fowczarek
- Fix resolver by id and slug for product and product variant - #6985 by @d-wysocki
- Add optional support for reporting resource limits via a stub field in `shop` - #6967 by @NyanKiyoshi
- Update checkout quantity when checkout lines are deleted - #7002 by @IKarbowiak
- Fix available shipping methods - return also weight methods without weight limits - #7021 by @IKarbowiak
- Validate discount value for percentage vouchers and sales - #7033 by @d-wysocki
- Add field `languageCode` to types: `AccountInput`, `AccountRegisterInput`, `CheckoutCreateInput`, `CustomerInput`, `Order`, `User`. Add field `languageCodeEnum` to `Order` type. Add new mutation `CheckoutLanguageCodeUpdate`. Deprecate field `Order.languageCode`. - #6609 by @korycins
- Extend `Transaction` type with gateway response and `Payment` type with filter - #7062 by @IKarbowiak
- Fix invalid tax rates for lines - #7058 by @IKarbowiak
- Allow seeing unconfirmed orders - #7072 by @IKarbowiak
- Raise `GraphQLError` when too big integer value is provided - #7076 by @IKarbowiak
- Do not update draft order addresses when user is changing - #7088 by @IKarbowiak
- Recalculate draft order when product/variant was deleted - #7085 by @d-wysocki
- Added validation for `DraftOrderCreate` with negative quantity line - #7085 by @d-wysocki
- Remove HTML tags from product `description_plaintext` - #7094 by @d-wysocki
- Fix failing product tasks when instances are removed - #7092 by @IKarbowiak
- Update GraphQL endpoint to only match exactly `/graphql/` without trailing characters - #7117 by @IKarbowiak
- Introduce `traced_resolver` decorator instead of Graphene middleware - #7159 by @tomaszszymanski129
- Fix failing export when exporting attribute without values - #7131 by @IKarbowiak
- Fix incorrect payment data for Klarna - #7150 by @IKarbowiak
- Drop deleted images from storage - #7129 by @IKarbowiak
- Fix export with empty assignment values - #7214 by @IKarbowiak
- Change exported file name - #7222 by @IKarbowiak
- Fix core sorting on related fields - #7195 by @tomaszszymanski129
- Use GraphQL IDs instead of database IDs in export - #7240 by @IKarbowiak
- Fix draft order tax mismatch - #7226 by @IKarbowiak
  - Introduce `calculate_order_line_total` plugin method
- Update core logging for better Celery tasks handling - #7251 by @tomaszszymanski129
- Raise `ValidationError` when refund cannot be performed - #7260 by @IKarbowiak
- Fix customer addresses missing after customer creation - #7327 by @tomaszszymanski129
- Fix invoice generation - #7376 by @tomaszszymanski129
- Allow defining only one field in translations - #7363 by @IKarbowiak
- Allow filtering pages by ids - #7393 by @IKarbowiak
- Fix validate `min_spent` on vouchers to use net or gross value depends on `settings.display_gross_prices` - #7408 by @d-wysocki
- Fix invoice generation - #7376 by tomaszszymanski129
- Add hash to uploading images #7453 by @IKarbowiak
- Add file format validation for uploaded images - #7447 by @IKarbowiak
- Fix attaching params for address form errors - #7485 by @IKarbowiak
- Update draft order validation - #7253 by @IKarbowiak
  - Extend Order type with errors: [OrderError!]! field
  - Create tasks for deleting order lines by deleting products or variants
- Fix doubled checkout total price for one line and zero shipping price - #7532 by @IKarbowiak
- Deprecate nested objects in `TranslatableContent` types - #7522 by @IKarbowiak
- Modify order of auth middleware calls - #7572 by @tomaszszymanski129
- Drop assigning cheapest shipping method in checkout - #7767 by @maarcingebala
- Deprecate `query` argument in `sales` and `vouchers` queries - #7806 by @maarcingebala
- Allow translating objects by translatable content ID - #7803 by @maarcingebala
- Configure a periodic task for removing empty allocations - #7885 by @fowczarek
- Fix missing transaction id in Braintree - #8110 by @fowczarek
- Fix GraphQL federation support - #7771 #8107 by @rafalp
- Fix cursor-based pagination in products search - #8011 #8211 by @rafalp
- Batch loads in queries for Apollo Federation - #8362 by @rafalp
- Add workaround for failing Avatax when line has price 0 - #8610 by @korycins
- Add option to set tax code for shipping in Avatax configuration view - #8596 by @korycins
- Fix Avalara tax fetching from cache - #8647 by @fowczarek
- Fix incorrect stock allocation - #8931 by @IKarbowiak
- Fix incorrect handling of unavailable products in checkout - #8978, #9119 by @IKarbowiak, @korycins
- Add draft orders webhooks - #8102 by @jakubkuc
- Handle `SameSite` cookie attribute in jwt refresh token middleware - #8209 by @jakubkuc
- Fix creating translations with app - #6804 by @krzysztofwolski
- Add possibility to provide external payment ID during the conversion draft order to order - #6320 by @korycins
- Add basic rating for `Products` - #6284 by @korycins
- Add metadata to shipping zones and shipping methods - #6340 by @maarcingebala
- Add Page Types - #6261 by @IKarbowiak
- Migrate draftjs content to editorjs format - #6430 by @IKarbowiak
- Add editorjs sanitizer - #6456 by @IKarbowiak
- Add generic FileUpload mutation - #6470 by @IKarbowiak
- Order confirmation backend - #6498 by @tomaszszymanski129
- Handle `SameSite` cookie attribute in JWT refresh token middleware - #8209 by @jakubkuc
- Add possibility to provide external payment ID during the conversion draft order to order - #6320 by @korycins9
- Fix password reset request - #6351 by @Manfred-Madelaine-pro, Ambroise and Pierre
- Refund products support - #6530 by @korycins
- Add possibility to exclude products from shipping method - #6506 by @korycins
- Add `Shop.availableShippingMethods` query - #6551 by @IKarbowiak
- Add delivery time to shipping method - #6564 by @IKarbowiak
- Shipping zone description - #6653 by @tomaszszymanski129
- Get tax rate from plugins - #6649 by @IKarbowiak
- Added support for querying user by email - #6632 @LeOndaz
- Add order shipping tax rate - #6678 by @IKarbowiak
- Deprecate field `descriptionJSON` from `Product`, `Category`, `Collection` and field `contentJSON` from `Page` - #6692 by @d-wysocki
- Fix products visibility - #6704 by @IKarbowiak
- Fix page `contentJson` field to return JSON - #6832 by @d-wysocki
- Add SearchRank to search product by name and description. New enum added to `ProductOrderField` - `RANK` - which returns results sorted by search rank - #6872 by @d-wysocki
- Allocate stocks for order lines in a bulk way - #6877 by @IKarbowiak
- Deallocate stocks for order lines in a bulk way - #6896 by @IKarbowiak
- Prevent negative available quantity - #6897 by @d-wysocki
- Add default sorting by rank for search products - #6936 by @d-wysocki
- Fix exporting product description to xlsx - #6959 by @IKarbowiak
- Add `Shop.version` field to query API version - #6980 by @maarcingebala
- Add new authorization header `Authorization-Bearer` - #6998 by @korycins
- Add field `paymentMethodType` to `Payment` object - #7073 by @korycins
- Unify Warehouse Address API - #7481 by @d-wysocki
  - deprecate `companyName` on `Warehouse` type
  - remove `companyName` on `WarehouseInput` type
  - remove `WarehouseAddressInput` on `WarehouseUpdateInput` and `WarehouseCreateInput`, and change it to `AddressInput`
- Fix passing incorrect customer email to payment gateways - #7486 by @korycins
- Add HTTP meta tag for Content-Security-Policy in GraphQL Playground - #7662 by @NyanKiyoshi
- Add additional validation for `from_global_id_or_error` function - #8780 by @CossackDex

# 2.11.1

- Add support for Apple Pay on the web - #6466 by @korycins

## 2.11.0

### Features

- Add products export - #5255 by @IKarbowiak
- Add external apps support - #5767 by @korycins
- Invoices backend - #5732 by @tomaszszymanski129
- Adyen drop-in integration - #5914 by @korycins, @IKarbowiak
- Add a callback view to plugins - #5884 by @korycins
- Support pushing webhook events to message queues - #5940 by @patrys, @korycins
- Send a confirmation email when the order is canceled or refunded - #6017
- No secure cookie in debug mode - #6082 by @patrys, @orzechdev
- Add searchable and available for purchase flags to product - #6060 by @IKarbowiak
- Add `TotalPrice` to `OrderLine` - #6068 @fowczarek
- Add `PRODUCT_UPDATED` webhook event - #6100 by @tomaszszymanski129
- Search orders by GraphQL payment ID - #6135 by @korycins
- Search orders by a custom key provided by payment gateway - #6135 by @korycins
- Add ability to set a default product variant - #6140 by @tomaszszymanski129
- Allow product variants to be sortable - #6138 by @tomaszszymanski129
- Allow fetching stocks for staff users only with `MANAGE_ORDERS` permissions - #6139 by @fowczarek
- Add filtering to `ProductVariants` query and option to fetch variant by SKU in `ProductVariant` query - #6190 by @fowczarek
- Add filtering by Product IDs to `products` query - #6224 by @GrzegorzDerdak
- Add `change_currency` command - #6016 by @maarcingebala
- Add dummy credit card payment - #5822 by @IKarbowiak
- Add custom implementation of UUID scalar - #5646 by @koradon
- Add `AppTokenVerify` mutation - #5716 by @korycins

### Breaking Changes

- Refactored JWT support. Requires handling of JWT token in the storefront (a case when the backend returns the exception about the invalid token). - #5734, #5816 by @korycins
- New logging setup will now output JSON logs in production mode for ease of feeding them into log collection systems like Logstash or CloudWatch Logs - #5699 by @patrys
- Deprecate `WebhookEventType.CHECKOUT_QUANTITY_CHANGED` - #5837 by @korycins
- Anonymize and update order and payment fields; drop `PaymentSecureConfirm` mutation, drop Payment type fields: `extraData`, `billingAddress`, `billingEmail`, drop `gatewayResponse` from `Transaction` type - #5926 by @IKarbowiak
- Switch the HTTP stack from WSGI to ASGI based on Uvicorn - #5960 by @patrys
- Add `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES` permission, which is now required to access all attributes and product types related mutations - #6219 by @IKarbowiak

### Fixes

- Fix payment fields in order payload for webhooks - #5862 by @korycins
- Fix specific product voucher in draft orders - #5727 by @fowczarek
- Explicit country assignment in default shipping zones - #5736 by @maarcingebala
- Drop `json_content` field from the `Menu` model - #5761 by @maarcingebala
- Strip warehouse name in mutations - #5766 by @koradon
- Add missing order events during checkout flow - #5684 by @koradon
- Update Google Merchant to get tax rate based by plugin manager - #5823 by @gabmartinez
- Allow unicode in slug fields - #5877 by @IKarbowiak
- Fix empty plugin object result after `PluginUpdate` mutation - #5968 by @gabmartinez
- Allow finishing checkout when price amount is 0 - #6064 by @IKarbowiak
- Fix incorrect tax calculation for Avatax - #6035 by @korycins
- Fix incorrect calculation of subtotal with active Avatax - #6035 by @korycins
- Fix incorrect assignment of tax code for Avatax - #6035 by @korycins
- Do not allow negative product price - #6091 by @IKarbowiak
- Handle None as attribute value - #6092 by @IKarbowiak
- Fix for calling `order_created` before the order was saved - #6095 by @korycins
- Update default decimal places - #6098 by @IKarbowiak
- Avoid assigning the same pictures twice to a variant - #6112 by @IKarbowiak
- Fix crashing system when Avalara is improperly configured - #6117 by @IKarbowiak
- Fix for failing finalising draft order - #6133 by @korycins
- Remove corresponding draft order lines when variant is removing - #6119 by @IKarbowiak
- Update required perms for apps management - #6173 by @IKarbowiak
- Raise an error for an empty key in metadata - #6176 by @IKarbowiak
- Add attributes to product error - #6181 by @IKarbowiak
- Allow to add product variant with 0 price to draft order - #6189 by @IKarbowiak
- Fix deleting product when default variant is deleted - #6186 by @IKarbowiak
- Fix get unpublished products, product variants and collection as app - #6194 by @fowczarek
- Set `OrderFulfillStockInput` fields as required - #6196 by @IKarbowiak
- Fix attribute filtering by categories and collections - #6214 by @fowczarek
- Fix `is_visible` when `publication_date` is today - #6225 by @korycins
- Fix filtering products by multiple attributes - #6215 by @GrzegorzDerdak
- Add attributes validation while creating/updating a product's variant - #6269 by @GrzegorzDerdak
- Add metadata to page model - #6292 by @dominik-zeglen
- Fix for unnecessary attributes validation while updating simple product - #6300 by @GrzegorzDerdak
- Include order line total price to webhook payload - #6354 by @korycins
- Fix for fulfilling an order when product quantity equals allocated quantity - #6333 by @GrzegorzDerdak
- Fix for the ability to filter products on collection - #6363 by @GrzegorzDerdak

## 2.10.2

- Add command to change currencies in the database - #5906 by @d-wysocki

## 2.10.1

- Fix multiplied stock quantity - #5675 by @fowczarek
- Fix invalid allocation after migration - #5678 by @fowczarek
- Fix order mutations as app - #5680 by @fowczarek
- Prevent creating checkout/draft order with unpublished product - #5676 by @d-wysocki

## 2.10.0

- OpenTracing support - #5188 by @tomaszszymanski129
- Account confirmation email - #5126 by @tomaszszymanski129
- Relocate `Checkout` and `CheckoutLine` methods into separate module and update checkout related plugins to use them - #4980 by @krzysztofwolski
- Fix problem with free shipping voucher - #4942 by @IKarbowiak
- Add sub-categories to random data - #4949 by @IKarbowiak
- Deprecate `localized` field in Money type - #4952 by @IKarbowiak
- Fix for shipping API not applying taxes - #4913 by @kswiatek92
- Query object translation with only `manage_translation` permission - #4914 by @fowczarek
- Add customer note to draft orders API - #4973 by @IKarbowiak
- Allow to delete category and leave products - #4970 by @IKarbowiak
- Remove thumbnail generation from migration - #3494 by @kswiatek92
- Rename 'shipping_date' field in fulfillment model to 'created' - #2433 by @kswiatek92
- Reduce number of queries for 'checkoutComplete' mutation - #4989 by @IKarbowiak
- Force PyTest to ignore the environment variable containing the Django settings module - #4992 by @NyanKiyoshi
- Extend JWT token payload with user information - #4987 by @salwator
- Optimize the queries for product list in the dashboard - #4995 by @IKarbowiak
- Drop dashboard 1.0 - #5000 by @IKarbowiak
- Fixed serialization error on weight fields when running `loaddata` and `dumpdb` - #5005 by @NyanKiyoshi
- Fixed JSON encoding error on Google Analytics reporting - #5004 by @NyanKiyoshi
- Create custom field to translation, use new translation types in translations query - #5007 by @fowczarek
- Take allocated stock into account in `StockAvailability` filter - #5019 by @simonbru
- Generate matching postal codes for US addresses - #5033 by @maarcingebala
- Update debug toolbar - #5032 by @IKarbowiak
- Allow staff member to receive notification about customers orders - #4993 by @kswiatek92
- Add user's global id to the JWT payload - #5039 by @salwator
- Make middleware path resolving lazy - #5041 by @NyanKiyoshi
- Generate slug on saving the attribute value - #5055 by @fowczarek
- Fix order status after order update - #5072 by @fowczarek
- Extend top-level connection resolvers with ability to sort results - #5018 by @fowczarek
- Drop storefront 1.0 - #5043 by @IKarbowiak
- Replace permissions strings with enums - #5038 by @kswiatek92
- Remove gateways forms and templates - #5075 by @IKarbowiak
- Add `Wishlist` models and GraphQL endpoints - #5021 by @derenio
- Remove deprecated code - #5107 by @IKarbowiak
- Fix voucher start date filtering - #5133 by @dominik-zeglen
- Search by sku in products query - #5117 by @fowczarek
- Send fulfillment update email - #5118 by @IKarbowiak
- Add address query - #5148 by @kswiatek92
- Add `checkout_quantity_changed` webhook - #5042 by @derenio
- Remove unnecessary `manage_orders` permission - #5142 by @kswiatek92
- Mutation to change the user email - #5076 by @kswiatek92
- Add MyPy checks - #5150 by @IKarbowiak
- Move extracting user or service account to utils - #5152 by @kswiatek92
- Deprecate order status/created arguments - #5076 by @kswiatek92
- Fix getting title field in page mutations #5160 by @maarcingebala
- Copy public and private metadata from the checkout to the order upon creation - #5165 by @dankolbman
- Add warehouses and stocks- #4986 by @szewczykmira
- Add permission groups - #5176, #5513 by @IKarbowiak
- Drop `gettext` occurrences - #5189 by @IKarbowiak
- Fix `product_created` webhook - #5187 by @dzkb
- Drop unused resolver `resolve_availability` - #5190 by @maarcingebala
- Fix permission for `checkoutCustomerAttach` mutation - #5192 by @maarcingebala
- Restrict access to user field - #5194 by @maarcingebala
- Unify permission for service account API client in test - #5197 by @fowczarek
- Add additional confirmation step to `checkoutComplete` mutation - #5179 by @salwator
- Allow sorting warehouses by name - #5211 by @dominik-zeglen
- Add anonymization to GraphQL's `webhookSamplePayload` endpoint - #5161 @derenio
- Add slug to `Warehouse`, `Product` and `ProductType` models - #5196 by @IKarbowiak
- Add mutation for assigning, unassigning shipping zones to warehouse - #5217 by @kswiatek92
- Fix passing addresses to `PaymentData` objects - #5223 by @maarcingebala
- Return `null` when querying `me` as an anonymous user - #5231 by @maarcingebala
- Added `PLAYGROUND_ENABLED` environment variable/setting to allow to enable the GraphQL playground when `DEBUG` is disabled - #5254 by @NyanKiyoshi
- Fix access to order query when request from service account - #5258 by @fowczarek
- Customer shouldn't be able to see draft orders by token - #5259 by @fowczarek
- Customer shouldn't be able to query checkout with another customer - #5268 by @fowczarek
- Added integration support of Jaeger Tracing - #5282 by @NyanKiyoshi
- Return `null` when querying `me` as an anonymous user - #5231 as @maarcingebala
- Add `fulfillment created` webhook - @szewczykmira
- Unify metadata API - #5178 by @fowczarek
- Add compiled versions of emails to the repository - #5260 by @tomaszszymanski129
- Add required prop to fields where applicable - #5293 by @dominik-zeglen
- Drop `get_absolute_url` methods - #5299 by @IKarbowiak
- Add `--force` flag to `cleardb` command - #5302 by @maarcingebala
- Require non-empty message in `orderAddNote` mutation - #5316 by @maarcingebala
- Stock management refactor - #5323 by @IKarbowiak
- Add discount error codes - #5348 by @IKarbowiak
- Add benchmarks to checkout mutations - #5339 by @fowczarek
- Add pagination tests - #5363 by @fowczarek
- Add ability to assign multiple warehouses in mutations to create/update a shipping zone - #5399 by @fowczarek
- Add filter by ids to the `warehouses` query - #5414 by @fowczarek
- Add shipping rate price validation - #5411 by @kswiatek92
- Remove unused settings and environment variables - #5420 by @maarcingebala
- Add product price validation - #5413 by @kswiatek92
- Add attribute validation to `attributeAssign` mutation - #5423 by @kswiatek92
- Add possibility to update/delete more than one item in metadata - #5446 by @koradon
- Check if image exists before validating - #5425 by @kswiatek92
- Fix warehouses query not working without id - #5441 by @koradon
- Add `accountErrors` to `CreateToken` mutation - #5437, #5465 by @koradon
- Raise `GraphQLError` if filter has invalid IDs - #5460 by @gabmartinez
- Use `AccountErrorCode.INVALID_CREDENTIALS` instead of `INVALID_PASSWORD` - #5495 by @koradon
- Add tests for pagination - #5468 by @koradon
- Add `Job` abstract model and interface - #5510 by @IKarbowiak
- Refactor implementation of allocation - #5445 by @fowczarek
- Fix `WeightScalar` - #5530 by @koradon
- Add `OrderFulfill` mutation - #5525 by @fowczarek
- Add "It Works" page - #5494 by @IKarbowiak and @dominik-zeglen
- Extend errors in `OrderFulfill` mutation - #5553 by @fowczarek
- Refactor `OrderCancel` mutation for multiple warehouses - #5554 by @fowczarek
- Add negative weight validation - #5564 by @fowczarek
- Add error when user pass empty object as address - #5585 by @fowczarek
- Fix payment creation without shipping method - #5444 by @d-wysocki
- Fix checkout and order flow with variant without inventory tracking - #5599 by @fowczarek
- Fixed JWT expired token being flagged as unhandled error rather than handled. - #5603 by @NyanKiyoshi
- Refactor read-only middleware - #5602 by @maarcingebala
- Fix availability for variants without inventory tracking - #5605 by @fowczarek
- Drop support for configuring Vatlayer plugin from settings file. - #5614 by @korycins
- Add ability to query category, collection or product by slug - #5574 by @koradon
- Add `quantityAvailable` field to `ProductVariant` type - #5628 by @fowczarek
- Use tags rather than time-based logs for information on requests - #5608 by @NyanKiyoshi

## 2.9.0

### API

- Add mutation to change customer's first name last name - #4489 by @fowczarek
- Add mutation to delete customer's account - #4494 by @fowczarek
- Add mutation to change customer's password - #4656 by @fowczarek
- Add ability to customize email sender address in emails sent by Saleor - #4820 by @NyanKiyoshi
- Add ability to filter attributes per global ID - #4640 by @NyanKiyoshi
- Add ability to search product types by value (through the name) - #4647 by @NyanKiyoshi
- Add queries and mutation for serving and saving the configuration of all plugins - #4576 by @korycins
- Add `redirectUrl` to staff and user create mutations - #4717 by @fowczarek
- Add error codes to mutations responses - #4676 by @Kwaidan00
- Add translations to countries in `shop` query - #4732 by @fowczarek
- Add support for sorting product by their attribute values through given attribute ID - #4740 by @NyanKiyoshi
- Add descriptions for queries and query arguments - #4758 by @maarcingebala
- Add support for Apollo Federation - #4825 by @salwator
- Add mutation to create multiple product variants at once - #4735 by @fowczarek
- Add default value to custom errors - #4797 by @fowczarek
- Extend `availablePaymentGateways` field with gateways' configuration data - #4774 by @salwator
- Change `AddressValidationRules` API - #4655 by @Kwaidan00
- Use search in a consistent way; add sort by product type name and publication status to `products` query. - #4715 by @fowczarek
- Unify `menuItemMove` mutation with other reordering mutations - #4734 by @NyanKiyoshi
- Don't create an order when the payment was unsuccessful - #4500 by @NyanKiyoshi
- Don't require shipping information in checkout for digital orders - #4573 by @NyanKiyoshi
- Drop `manage_users` permission from the `permissions` query - #4854 by @maarcingebala
- Deprecate `inCategory` and `inCollection` attributes filters in favor of `filter` argument - #4700 by @NyanKiyoshi & @khalibloo
- Remove `PaymentGatewayEnum` from the schema, as gateways now are dynamic plugins - #4756 by @salwator
- Require `manage_products` permission to query `costPrice` and `stockQuantity` fields - #4753 by @NyanKiyoshi
- Refactor account mutations - #4510, #4668 by @fowczarek
- Fix generating random avatars when updating staff accounts - #4521 by @maarcingebala
- Fix updating JSON menu representation in mutations - #4524 by @maarcingebala
- Fix setting variant's `priceOverride` and `costPrice` to `null` - #4754 by @NyanKiyoshi
- Fix fetching staff user without `manage_users` permission - #4835 by @fowczarek
- Ensure that a GraphQL query is a string - #4836 by @nix010
- Add ability to configure the password reset link - #4863 by @fowczarek
- Fixed a performance issue where Saleor would sometimes run huge, unneeded prefetches when resolving categories or collections - #5291 by @NyanKiyoshi
- uWSGI now forces the django application to directly load on startup instead of being lazy - #5357 by @NyanKiyoshi

### Core

- Add enterprise-grade attributes management - #4351 by @dominik-zeglen and @NyanKiyoshi
- Add extensions manager - #4497 by @korycins
- Add service accounts - backend support - #4689 by @korycins
- Add support for webhooks - #4731 by @korycins
- Migrate the attributes mapping from HStore to many-to-many relation - #4663 by @NyanKiyoshi
- Create general abstraction for object metadata - #4447 by @salwator
- Add metadata to `Order` and `Fulfillment` models - #4513, #4866 by @szewczykmira
- Migrate the tax calculations to plugins - #4497 by @korycins
- Rewrite payment gateways using plugin architecture - #4669 by @salwator
- Rewrite Stripe integration to use PaymentIntents API - #4606 by @salwator
- Refactor password recovery system - #4617 by @fowczarek
- Add functionality to sort products by their "minimal variant price" - #4416 by @derenio
- Add voucher's "once per customer" feature - #4442 by @fowczarek
- Add validations for minimum password length in settings - #4735 by @fowczarek
- Add form to configure payments in the dashboard - #4807 by @szewczykmira
- Change `unique_together` in `AttributeValue` - #4805 by @fowczarek
- Change max length of SKU to 255 characters - #4811 by @lex111
- Distinguish `OrderLine` product name and variant name - #4702 by @fowczarek
- Fix updating order status after automatic fulfillment of digital products - #4709 by @korycins
- Fix error when updating or creating a sale with missing required values - #4778 by @NyanKiyoshi
- Fix error filtering pages by URL in the dashboard 1.0 - #4776 by @NyanKiyoshi
- Fix display of the products tax rate in the details page of dashboard 1.0 - #4780 by @NyanKiyoshi
- Fix adding the same product into a collection multiple times - #4518 by @NyanKiyoshi
- Fix crash when placing an order when a customer happens to have the same address more than once - #4824 by @NyanKiyoshi
- Fix time zone based tests - #4468 by @fowczarek
- Fix serializing empty URLs as a string when creating menu items - #4616 by @maarcingebala
- The invalid IP address in HTTP requests now fallback to the requester's IP address. - #4597 by @NyanKiyoshi
- Fix product variant update with current attribute values - #4936 by @fowczarek
- Update checkout last field and add auto now fields to save with update_fields parameter - #5177 by @IKarbowiak

### Dashboard 2.0

- Allow selecting the number of rows displayed in dashboard's list views - #4414 by @benekex2
- Add ability to toggle visible columns in product list - #4608 by @dominik-zeglen
- Add voucher settings - #4556 by @benekex2
- Contrast improvements - #4508 by @benekex2
- Display menu item form errors - #4551 by @dominik-zeglen
- Do not allow random IDs to appear in snapshots - #4495 by @dominik-zeglen
- Input UI changes - #4542 by @benekex2
- Implement new menu design - #4476 by @benekex2
- Refetch attribute list after closing modal - #4615 by @dominik-zeglen
- Add config for Testcafe - #4553 by @dominik-zeglen
- Fix product type taxes select - #4453 by @benekex2
- Fix form reloading - #4467 by @dominik-zeglen
- Fix voucher limit value when checkbox unchecked - #4456 by @benekex2
- Fix searches and pickers - #4487 by @dominik-zeglen
- Fix dashboard menu styles - #4491 by @benekex2
- Fix menu responsiveness - #4511 by @benekex2
- Fix loosing focus while typing in the product description field - #4549 by @dominik-zeglen
- Fix MUI warnings - #4588 by @dominik-zeglen
- Fix bulk action checkboxes - #4618 by @dominik-zeglen
- Fix rendering user avatar when it's empty #4546 by @maarcingebala
- Remove Dashboard 2.0 files form Saleor repository - #4631 by @dominik-zeglen
- Fix CreateToken mutation to use NonNull on errors field #5415 by @gabmartinez

### Other notable changes

- Replace Pipenv with Poetry - #3894 by @michaljelonek
- Upgrade `django-prices` to v2.1 - #4639 by @NyanKiyoshi
- Disable reports from uWSGI about broken pipe and write errors from disconnected clients - #4596 by @NyanKiyoshi
- Fix the random failures of `populatedb` trying to create users with an existing email - #4769 by @NyanKiyoshi
- Enforce `pydocstyle` for Python docstrings over the project - #4562 by @NyanKiyoshi
- Move Django Debug Toolbar to dev requirements - #4454 by @derenio
- Change license for artwork to CC-BY 4.0
- New translations:
  - Greek

## 2.8.0

### Core

- Avatax backend support - #4310 by @korycins
- Add ability to store used payment sources in gateways (first implemented in Braintree) - #4195 by @salwator
- Add ability to specify a minimal quantity of checkout items for a voucher - #4427 by @fowczarek
- Change the type of start and end date fields from Date to DateTime - #4293 by @fowczarek
- Revert the custom dynamic middlewares - #4452 by @NyanKiyoshi

### Dashboard 2.0

- UX improvements in Vouchers section - #4362 by @benekex2
- Add company address configuration - #4432 by @benekex2
- Require name when saving a custom list filter - #4269 by @benekex2
- Use `esModuleInterop` flag in `tsconfig.json` to simplify imports - #4372 by @dominik-zeglen
- Use hooks instead of a class component in forms - #4374 by @dominik-zeglen
- Drop CSRF token header from API client - #4357 by @dominik-zeglen
- Fix various bugs in the product section - #4429 by @dominik-zeglen

### Other notable changes

- Fix error when creating a checkout with voucher code - #4292 by @NyanKiyoshi
- Fix error when users enter an invalid phone number in an address - #4404 by @NyanKiyoshi
- Fix error when adding a note to an anonymous order - #4319 by @NyanKiyoshi
- Fix gift card duplication error in the `populatedb` script - #4336 by @fowczarek
- Fix vouchers apply once per order - #4339 by @fowczarek
- Fix discount tests failing at random - #4401 by @korycins
- Add `SPECIFIC_PRODUCT` type to `VoucherType` - #4344 by @fowczarek
- New translations:
  - Icelandic
- Refactored the backend side of `checkoutCreate` to improve performances and prevent side effects over the user's checkout if the checkout creation was to fail. - #4367 by @NyanKiyoshi
- Refactored the logic of cleaning the checkout shipping method over the API, so users do not lose the shipping method when updating their checkout. If the shipping method becomes invalid, it will be replaced by the cheapest available. - #4367 by @NyanKiyoshi & @szewczykmira
- Refactored process of getting available shipping methods to make it easier to understand and prevent human-made errors. - #4367 by @NyanKiyoshi
- Moved 3D secure option to Braintree plugin configuration and update config structure mechanism - #4751 by @salwator

## 2.7.0

### API

- Create order only when payment is successful - #4154 by @NyanKiyoshi
- Order Events containing order lines or fulfillment lines now return the line object in the GraphQL API - #4114 by @NyanKiyoshi
- GraphQL now prints exceptions to stderr as well as returning them or not - #4148 by @NyanKiyoshi
- Refactored API resolvers to static methods with root typing - #4155 by @NyanKiyoshi
- Add phone validation in the GraphQL API to handle the library upgrade - #4156 by @NyanKiyoshi

### Core

- Add basic Gift Cards support in the backend - #4025 by @fowczarek
- Add the ability to sort products within a collection - #4123 by @NyanKiyoshi
- Implement customer events - #4094 by @NyanKiyoshi
- Merge "authorize" and "capture" operations - #4098 by @korycins, @NyanKiyoshi
- Separate the Django middlewares from the GraphQL API middlewares - #4102 by @NyanKiyoshi, #4186 by @cmiacz

### Dashboard 2.0

- Add navigation section - #4012 by @dominik-zeglen
- Add filtering on product list - #4193 by @dominik-zeglen
- Add filtering on orders list - #4237 by @dominik-zeglen
- Change input style and improve Storybook stories - #4115 by @dominik-zeglen
- Migrate deprecated fields in Dashboard 2.0 - #4121 by @benekex2
- Add multiple select checkbox - #4133, #4146 by @benekex2
- Rename menu items in Dashboard 2.0 - #4172 by @benekex2
- Category delete modal improvements - #4171 by @benekex2
- Close modals on click outside - #4236 - by @benekex2
- Use date localize hook in translations - #4202 by @dominik-zeglen
- Unify search API - #4200 by @dominik-zeglen
- Default default PAGINATE_BY - #4238 by @dominik-zeglen
- Create generic filtering interface - #4221 by @dominik-zeglen
- Add default state to rich text editor = #4281 by @dominik-zeglen
- Fix translation discard button - #4109 by @benekex2
- Fix draftail options and icons - #4132 by @benekex2
- Fix typos and messages in Dashboard 2.0 - #4168 by @benekex2
- Fix view all orders button - #4173 by @benekex2
- Fix visibility card view - #4198 by @benekex2
- Fix query refetch after selecting an object in list - #4272 by @dominik-zeglen
- Fix image selection in variants - #4270 by @benekex2
- Fix collection search - #4267 by @dominik-zeglen
- Fix quantity height in draft order edit - #4273 by @benekex2
- Fix checkbox clickable area size - #4280 by @dominik-zeglen
- Fix breaking object selection in menu section - #4282 by @dominik-zeglen
- Reset selected items when tab switch - #4268 by @benekex2

### Other notable changes

- Add support for Google Cloud Storage - #4127 by @chetabahana
- Adding a nonexistent variant to checkout no longer crashes - #4166 by @NyanKiyoshi
- Disable storage of Celery results - #4169 by @NyanKiyoshi
- Disable polling in Playground - #4188 by @maarcingebala
- Cleanup code for updated function names and unused argument - #4090 by @jxltom
- Users can now add multiple "Add to Cart" forms in a single page - #4165 by @NyanKiyoshi
- Fix incorrect argument in `get_client_token` in Braintree integration - #4182 by @maarcingebala
- Fix resolving attribute values when transforming them to HStore - #4161 by @maarcingebala
- Fix wrong calculation of subtotal in cart page - #4145 by @korycins
- Fix margin calculations when product/variant price is set to zero - #4170 by @MahmoudRizk
- Fix applying discounts in checkout's subtotal calculation in API - #4192 by @maarcingebala
- Fix GATEWAYS_ENUM to always contain all implemented payment gateways - #4108 by @koradon

## 2.6.0

### API

- Add unified filtering interface in resolvers - #3952, #4078 by @korycins
- Add mutations for bulk actions - #3935, #3954, #3967, #3969, #3970 by @akjanik
- Add mutation for reordering menu items - #3958 by @NyanKiyoshi
- Optimize queries for single nodes - #3968 @NyanKiyoshi
- Refactor error handling in mutations #3891 by @maarcingebala & @akjanik
- Specify mutation permissions through Meta classes - #3980 by @NyanKiyoshi
- Unify pricing access in products and variants - #3948 by @NyanKiyoshi
- Use only_fields instead of exclude_fields in type definitions - #3940 by @michaljelonek
- Prefetch collections when getting sales of a bunch of products - #3961 by @NyanKiyoshi
- Remove unnecessary dedents from GraphQL schema so new Playground can work - #4045 by @salwator
- Restrict resolving payment by ID - #4009 @NyanKiyoshi
- Require `checkoutId` for updating checkout's shipping and billing address - #4074 by @jxltom
- Handle errors in `TokenVerify` mutation - #3981 by @fowczarek
- Unify argument names in types and resolvers - #3942 by @NyanKiyoshi

### Core

- Use Black as the default code formatting tool - #3852 by @krzysztofwolski and @NyanKiyoshi
- Dropped Python 3.5 support - #4028 by @korycins
- Rename Cart to Checkout - #3963 by @michaljelonek
- Use data classes to exchange data with payment gateways - #4028 by @korycins
- Refactor order events - #4018 by @NyanKiyoshi

### Dashboard 2.0

- Add bulk actions - #3955 by @dominik-zeglen
- Add user avatar management - #4030 by @benekex2
- Add navigation drawer support on mobile devices - #3839 by @benekex2
- Fix rendering validation errors in product form - #4024 by @benekex2
- Move dialog windows to query string rather than router paths - #3953 by @dominik-zeglen
- Update order events types - #4089 by @jxltom
- Code cleanup by replacing render props with react hooks - #4010 by @dominik-zeglen

### Other notable changes

- Add setting to enable Django Debug Toolbar - #3983 by @koradon
- Use newest GraphQL Playground - #3971 by @salwator
- Ensure adding to quantities in the checkout is respecting the limits - #4005 by @NyanKiyoshi
- Fix country area choices - #4008 by @fowczarek
- Fix price_range_as_dict function - #3999 by @zodiacfireworks
- Fix the product listing not showing in the voucher when there were products selected - #4062 by @NyanKiyoshi
- Fix crash in Dashboard 1.0 when updating an order address's phone number - #4061 by @NyanKiyoshi
- Reduce the time of tests execution by using dummy password hasher - #4083 by @korycins
- Set up explicit **hash** function - #3979 by @akjanik
- Unit tests use none as media root - #3975 by @korycins
- Update file field styles with materializecss template filter - #3998 by @zodiacfireworks
- New translations:
  - Albanian
  - Colombian Spanish
  - Lithuanian

## 2.5.0

### API

- Add query to fetch draft orders - #3809 by @michaljelonek
- Add bulk delete mutations - #3838 by @michaljelonek
- Add `languageCode` enum to API - #3819 by @michaljelonek, #3854 by @jxltom
- Duplicate address instances in checkout mutations - #3866 by @pawelzar
- Restrict access to `orders` query for unauthorized users - #3861 by @pawelzar
- Support setting address as default in address mutations - #3787 by @jxltom
- Fix phone number validation in GraphQL when country prefix not given - #3905 by @patrys
- Report pretty stack traces in DEBUG mode - #3918 by @patrys

### Core

- Drop support for Django 2.1 and Django 1.11 (previous LTS) - #3929 by @patrys
- Fulfillment of digital products - #3868 by @korycins
- Introduce avatars for staff accounts - #3878 by @pawelzar
- Refactor the account avatars path from a relative to absolute - #3938 by @NyanKiyoshi

### Dashboard 2.0

- Add translations section - #3884 by @dominik-zeglen
- Add light/dark theme - #3856 by @dominik-zeglen
- Add customer's address book view - #3826 by @dominik-zeglen
- Add "Add variant" button on the variant details page = #3914 by @dominik-zeglen
- Add back arrows in "Configure" subsections - #3917 by @dominik-zeglen
- Display avatars in staff views - #3922 by @dominik-zeglen
- Prevent user from changing his own status and permissions - #3922 by @dominik-zeglen
- Fix crashing product create view - #3837, #3910 by @dominik-zeglen
- Fix layout in staff members details page - #3857 by @dominik-zeglen
- Fix unfocusing rich text editor - #3902 by @dominik-zeglen
- Improve accessibility - #3856 by @dominik-zeglen

### Other notable changes

- Improve user and staff management in dashboard 1.0 - #3781 by @jxltom
- Fix default product tax rate in Dashboard 1.0 - #3880 by @pawelzar
- Fix logo in docs - #3928 by @michaljelonek
- Fix name of logo file - #3867 by @jxltom
- Fix variants for juices in example data - #3926 by @michaljelonek
- Fix alignment of the cart dropdown on new bootstrap version - #3937 by @NyanKiyoshi
- Refactor the account avatars path from a relative to absolute - #3938 by @NyanKiyoshi
- New translations:
  - Armenian
  - Portuguese
  - Swahili
  - Thai

## 2.4.0

### API

- Add model translations support in GraphQL API - #3789 by @michaljelonek
- Add mutations to manage addresses for authenticated customers - #3772 by @Kwaidan00, @maarcingebala
- Add mutation to apply vouchers in checkout - #3739 by @Kwaidan00
- Add thumbnail field to `OrderLine` type - #3737 by @michaljelonek
- Add a query to fetch order by token - #3740 by @michaljelonek
- Add city choices and city area type to address validator API - #3788 by @jxltom
- Fix access to unpublished objects in API - #3724 by @Kwaidan00
- Fix bug where errors are not returned when creating fulfillment with a non-existent order line - #3777 by @jxltom
- Fix `productCreate` mutation when no product type was provided - #3804 by @michaljelonek
- Enable database search in products query - #3736 by @michaljelonek
- Use authenticated user's email as default email in creating checkout - #3726 by @jxltom
- Generate voucher code if it wasn't provided in mutation - #3717 by @Kwaidan00
- Improve limitation of vouchers by country - #3707 by @michaljelonek
- Only include canceled fulfillments for staff in fulfillment API - #3778 by @jxltom
- Support setting address as when creating customer address #3782 by @jxltom
- Fix generating slug from title - #3816 by @maarcingebala
- Add `variant` field to `OrderLine` type - #3820 by @maarcingebala

### Core

- Add JSON fields to store rich-text content - #3756 by @michaljelonek
- Add function to recalculate total order weight - #3755 by @Kwaidan00, @maarcingebala
- Unify cart creation logic in API and Django views - #3761, #3790 by @maarcingebala
- Unify payment creation logic in API and Django views - #3715 by @maarcingebala
- Support partially charged and refunded payments - #3735 by @jxltom
- Support partial fulfillment of ordered items - #3754 by @jxltom
- Fix applying discounts when a sale has no end date - #3595 by @cprinos

### Dashboard 2.0

- Add "Discounts" section - #3654 by @dominik-zeglen
- Add "Pages" section; introduce Draftail WYSIWYG editor - #3751 by @dominik-zeglen
- Add "Shipping Methods" section - #3770 by @dominik-zeglen
- Add support for date and datetime components - #3708 by @dominik-zeglen
- Restyle app layout - #3811 by @dominik-zeglen

### Other notable changes

- Unify model field names related to models' public access - `publication_date` and `is_published` - #3706 by @michaljelonek
- Improve filter orders by payment status - #3749 @jxltom
- Refactor translations in emails - #3701 by @Kwaidan00
- Use exact image versions in docker-compose - #3742 by @ashishnitinpatil
- Sort order payment and history in descending order - #3747 by @jxltom
- Disable style-loader in dev mode - #3720 by @jxltom
- Add ordering to shipping method - #3806 by @michaljelonek
- Add missing type definition for dashboard 2.0 - #3776 by @jxltom
- Add header and footer for checkout success pages #3752 by @jxltom
- Add instructions for using local assets in Docker - #3723 by @michaljelonek
- Update S3 deployment documentation to include CORS configuration note - #3743 by @NyanKiyoshi
- Fix missing migrations for is_published field of product and page model - #3757 by @jxltom
- Fix problem with l10n in Braintree payment gateway template - #3691 by @Kwaidan00
- Fix bug where payment is not filtered from active ones when creating payment - #3732 by @jxltom
- Fix incorrect cart badge location - #3786 by @jxltom
- Fix storefront styles after bootstrap is updated to 4.3.1 - #3753 by @jxltom
- Fix logo size in different browser and devices with different sizes - #3722 by @jxltom
- Rename dumpdata file `db.json` to `populatedb_data.json` - #3810 by @maarcingebala
- Prefetch collections for product availability - #3813 by @michaljelonek
- Bump django-graphql-jwt - #3814 by @michaljelonek
- Fix generating slug from title - #3816 by @maarcingebala
- New translations:
  - Estonian
  - Indonesian

## 2.3.1

- Fix access to private variant fields in API - #3773 by maarcingebala
- Limit access of quantity and allocated quantity to staff in GraphQL API #3780 by @jxltom

## 2.3.0

### API

- Return user's last checkout in the `User` type - #3578 by @fowczarek
- Automatically assign checkout to the logged in user - #3587 by @fowczarek
- Expose `chargeTaxesOnShipping` field in the `Shop` type - #3603 by @fowczarek
- Expose list of enabled payment gateways - #3639 by @fowczarek
- Validate uploaded files in a unified way - #3633 by @fowczarek
- Add mutation to trigger fetching tax rates - #3622 by @fowczarek
- Use USERNAME_FIELD instead of hard-code email field when resolving user - #3577 by @jxltom
- Require variant and quantity fields in `CheckoutLineInput` type - #3592 by @jxltom
- Preserve order of nodes in `get_nodes_or_error` function - #3632 by @jxltom
- Add list mutations for `Voucher` and `Sale` models - #3669 by @michaljelonek
- Use proper type for countries in `Voucher` type - #3664 by @michaljelonek
- Require email in when creating checkout in API - #3667 by @michaljelonek
- Unify returning errors in the `tokenCreate` mutation - #3666 by @michaljelonek
- Use `Date` field in Sale/Voucher inputs - #3672 by @michaljelonek
- Refactor checkout mutations - #3610 by @fowczarek
- Refactor `clean_instance`, so it does not returns errors anymore - #3597 by @akjanik
- Handle GraphqQL syntax errors - #3576 by @jxltom

### Core

- Refactor payments architecture - #3519 by @michaljelonek
- Improve Docker and `docker-compose` configuration - #3657 by @michaljelonek
- Allow setting payment status manually for dummy gateway in Storefront 1.0 - #3648 by @jxltom
- Infer default transaction kind from operation type - #3646 by @jxltom
- Get correct payment status for order without any payments - #3605 by @jxltom
- Add default ordering by `id` for `CartLine` model - #3593 by @jxltom
- Fix "set password" email sent to customer created in the dashboard - #3688 by @Kwaidan00

### Dashboard 2.0

- ️Add taxes section - #3622 by @dominik-zeglen
- Add drag'n'drop image upload - #3611 by @dominik-zeglen
- Unify grid handling - #3520 by @dominik-zeglen
- Add component generator - #3670 by @dominik-zeglen
- Throw Typescript errors while snapshotting - #3611 by @dominik-zeglen
- Simplify mutation's error checking - #3589 by @dominik-zeglen
- Fix order cancelling - #3624 by @dominik-zeglen
- Fix logo placement - #3602 by @dominik-zeglen

### Other notable changes

- Register Celery task for updating exchange rates - #3599 by @jxltom
- Fix handling different attributes with the same slug - #3626 by @jxltom
- Add missing migrations for tax rate choices - #3629 by @jxltom
- Fix `TypeError` on calling `get_client_token` - #3660 by @michaljelonek
- Make shipping required as default when creating product types - #3655 by @jxltom
- Display payment status on customer's account page in Storefront 1.0 - #3637 by @jxltom
- Make order fields sequence in Dashboard 1.0 same as in Dashboard 2.0 - #3606 by @jxltom
- Fix returning products for homepage for the currently viewing user - #3598 by @jxltom
- Allow filtering payments by status in Dashboard 1.0 - #3608 by @jxltom
- Fix typo in the definition of order status - #3649 by @jxltom
- Add margin for order notes section - #3650 by @jxltom
- Fix logo position - #3609, #3616 by @jxltom
- Storefront visual improvements - #3696 by @piotrgrundas
- Fix product list price filter - #3697 by @Kwaidan00
- Redirect to success page after successful payment - #3693 by @Kwaidan00

## 2.2.0

### API

- Use `PermissionEnum` as input parameter type for `permissions` field - #3434 by @maarcingebala
- Add "authorize" and "charge" mutations for payments - #3426 by @jxltom
- Add alt text to product thumbnails and background images of collections and categories - #3429 by @fowczarek
- Fix passing decimal arguments = #3457 by @fowczarek
- Allow sorting products by the update date - #3470 by @jxltom
- Validate and clear the shipping method in draft order mutations - #3472 by @fowczarek
- Change tax rate field to choice field - #3478 by @fowczarek
- Allow filtering attributes by collections - #3508 by @maarcingebala
- Resolve to `None` when empty object ID was passed as mutation argument - #3497 by @maarcingebala
- Change `errors` field type from [Error] to [Error!] - #3489 by @fowczarek
- Support creating default variant for product types that don't use multiple variants - #3505 by @fowczarek
- Validate SKU when creating a default variant - #3555 by @fowczarek
- Extract enums to separate files - #3523 by @maarcingebala

### Core

- Add Stripe payment gateway - #3408 by @jxltom
- Add `first_name` and `last_name` fields to the `User` model - #3101 by @fowczarek
- Improve several payment validations - #3418 by @jxltom
- Optimize payments related database queries - #3455 by @jxltom
- Add publication date to collections - #3369 by @k-brk
- Fix hard-coded site name in order PDFs - #3526 by @NyanKiyoshi
- Update favicons to the new style - #3483 by @dominik-zeglen
- Fix migrations for default currency - #3235 by @bykof
- Remove Elasticsearch from `docker-compose.yml` - #3482 by @maarcingebala
- Resort imports in tests - #3471 by @jxltom
- Fix the no shipping orders payment crash on Stripe - #3550 by @NyanKiyoshi
- Bump backend dependencies - #3557 by @maarcingebala. This PR removes security issue CVE-2019-3498 which was present in Django 2.1.4. Saleor however wasn't vulnerable to this issue as it doesn't use the affected `django.views.defaults.page_not_found()` view.
- Generate random data using the default currency - #3512 by @stephenmoloney
- New translations:
  - Catalan
  - Serbian

### Dashboard 2.0

- Restyle product selection dialogs - #3499 by @dominik-zeglen, @maarcingebala
- Fix minor visual bugs in Dashboard 2.0 - #3433 by @dominik-zeglen
- Display warning if order draft has missing data - #3431 by @dominik-zeglen
- Add description field to collections - #3435 by @dominik-zeglen
- Add query batching - #3443 by @dominik-zeglen
- Use autocomplete fields in country selection - #3443 by @dominik-zeglen
- Add alt text to categories and collections - #3461 by @dominik-zeglen
- Use first and last name of a customer or staff member in UI - #3247 by @Bonifacy1, @dominik-zeglen
- Show error page if an object was not found - #3463 by @dominik-zeglen
- Fix simple product's inventory data saving bug - #3474 by @dominik-zeglen
- Replace `thumbnailUrl` with `thumbnail { url }` - #3484 by @dominik-zeglen
- Change "Feature on Homepage" switch behavior - #3481 by @dominik-zeglen
- Expand payment section in order view - #3502 by @dominik-zeglen
- Change TypeScript loader to speed up the build process - #3545 by @patrys

### Bugfixes

- Do not show `Pay For Order` if order is partly paid since partial payment is not supported - #3398 by @jxltom
- Fix attribute filters in the products category view - #3535 by @fowczarek
- Fix storybook dependencies conflict - #3544 by @dominik-zeglen

## 2.1.0

### API

- Change selected connection fields to lists - #3307 by @fowczarek
- Require pagination in connections - #3352 by @maarcingebala
- Replace Graphene view with a custom one - #3263 by @patrys
- Change `sortBy` parameter to use enum type - #3345 by @fowczarek
- Add `me` query to fetch data of a logged-in user - #3202, #3316 by @fowczarek
- Add `canFinalize` field to the Order type - #3356 by @fowczarek
- Extract resolvers and mutations to separate files - #3248 by @fowczarek
- Add VAT tax rates field to country - #3392 by @michaljelonek
- Allow creating orders without users - #3396 by @fowczarek

### Core

- Add Razorpay payment gatway - #3205 by @NyanKiyoshi
- Use standard tax rate as a default tax rate value - #3340 by @fowczarek
- Add description field to the Collection model - #3275 by @fowczarek
- Enforce the POST method on VAT rates fetching - #3337 by @NyanKiyoshi
- Generate thumbnails for category/collection background images - #3270 by @NyanKiyoshi
- Add warm-up support in product image creation mutation - #3276 by @NyanKiyoshi
- Fix error in the `populatedb` script when running it not from the project root - #3272 by @NyanKiyoshi
- Make Webpack rebuilds fast - #3290 by @patrys
- Skip installing Chromium to make deployment faster - #3227 by @jxltom
- Add default test runner - #3258 by @jxltom
- Add Transifex client to Pipfile - #3321 by @jxltom
- Remove additional pytest arguments in tox - #3338 by @jxltom
- Remove test warnings - #3339 by @jxltom
- Remove runtime warning when product has discount - #3310 by @jxltom
- Remove `django-graphene-jwt` warnings - #3228 by @jxltom
- Disable deprecated warnings - #3229 by @jxltom
- Add `AWS_S3_ENDPOINT_URL` setting to support DigitalOcean spaces. - #3281 by @hairychris
- Add `.gitattributes` file to hide diffs for generated files on Github - #3055 by @NyanKiyoshi
- Add database sequence reset to `populatedb` - #3406 by @michaljelonek
- Get authorized amount from succeeded auth transactions - #3417 by @jxltom
- Resort imports by `isort` - #3412 by @jxltom

### Dashboard 2.0

- Add confirmation modal when leaving view with unsaved changes - #3375 by @dominik-zeglen
- Add dialog loading and error states - #3359 by @dominik-zeglen
- Split paths and urls - #3350 by @dominik-zeglen
- Derive state from props in forms - #3360 by @dominik-zeglen
- Apply debounce to autocomplete fields - #3351 by @dominik-zeglen
- Use Apollo signatures - #3353 by @dominik-zeglen
- Add order note field in the order details view - #3346 by @dominik-zeglen
- Add app-wide progress bar - #3312 by @dominik-zeglen
- Ensure that all queries are built on top of TypedQuery - #3309 by @dominik-zeglen
- Close modal windows automatically - #3296 by @dominik-zeglen
- Move URLs to separate files - #3295 by @dominik-zeglen
- Add basic filters for products and orders list - #3237 by @Bonifacy1
- Fetch default currency from API - #3280 by @dominik-zeglen
- Add `displayName` property to components - #3238 by @Bonifacy1
- Add window titles - #3279 by @dominik-zeglen
- Add paginator component - #3265 by @dominik-zeglen
- Update Material UI to 3.6 - #3387 by @patrys
- Upgrade React, Apollo, Webpack and Babel - #3393 by @patrys
- Add pagination for required connections - #3411 by @dominik-zeglen

### Bugfixes

- Fix language codes - #3311 by @jxltom
- Fix resolving empty attributes list - #3293 by @maarcingebala
- Fix range filters not being applied - #3385 by @michaljelonek
- Remove timeout for updating image height - #3344 by @jxltom
- Return error if checkout was not found - #3289 by @maarcingebala
- Solve an auto-resize conflict between Materialize and medium-editor - #3367 by @adonig
- Fix calls to `ngettext_lazy` - #3380 by @patrys
- Filter preauthorized order from succeeded transactions - #3399 by @jxltom
- Fix incorrect country code in fixtures - #3349 by @bingimar
- Fix updating background image of a collection - #3362 by @fowczarek & @dominik-zeglen

### Docs

- Document settings related to generating thumbnails on demand - #3329 by @NyanKiyoshi
- Improve documentation for Heroku deployment - #3170 by @raybesiga
- Update documentation on Docker deployment - #3326 by @jxltom
- Document payment gateway configuration - #3376 by @NyanKiyoshi

## 2.0.0

### API

- Add mutation to delete a customer; add `isActive` field in `customerUpdate` mutation - #3177 by @maarcingebala
- Add mutations to manage authorization keys - #3082 by @maarcingebala
- Add queries for dashboard homepage - #3146 by @maarcingebala
- Allows user to unset homepage collection - #3140 by @oldPadavan
- Use enums as permission codes - #3095 by @the-bionic
- Return absolute image URLs - #3182 by @maarcingebala
- Add `backgroundImage` field to `CategoryInput` - #3153 by @oldPadavan
- Add `dateJoined` and `lastLogin` fields in `User` type - #3169 by @maarcingebala
- Separate `parent` input field from `CategoryInput` - #3150 by @akjanik
- Remove duplicated field in Order type - #3180 by @maarcingebala
- Handle empty `backgroundImage` field in API - #3159 by @maarcingebala
- Generate name-based slug in collection mutations - #3145 by @akjanik
- Remove products field from `collectionUpdate` mutation - #3141 by @oldPadavan
- Change `items` field in `Menu` type from connection to list - #3032 by @oldPadavan
- Make `Meta.description` required in `BaseMutation` - #3034 by @oldPadavan
- Apply `textwrap.dedent` to GraphQL descriptions - #3167 by @fowczarek

### Dashboard 2.0

- Add collection management - #3135 by @dominik-zeglen
- Add customer management - #3176 by @dominik-zeglen
- Add homepage view - #3155, #3178 by @Bonifacy1 and @dominik-zeglen
- Add product type management - #3052 by @dominik-zeglen
- Add site settings management - #3071 by @dominik-zeglen
- Escape node IDs in URLs - #3115 by @dominik-zeglen
- Restyle categories section - #3072 by @Bonifacy1

### Other

- Change relation between `ProductType` and `Attribute` models - #3097 by @maarcingebala
- Remove `quantity-allocated` generation in `populatedb` script - #3084 by @MartinSeibert
- Handle `Money` serialization - #3131 by @Pacu2
- Do not collect unnecessary static files - #3050 by @jxltom
- Remove host mounted volume in `docker-compose` - #3091 by @tiangolo
- Remove custom services names in `docker-compose` - #3092 by @tiangolo
- Replace COUNTRIES with countries.countries - #3079 by @neeraj1909
- Installing dev packages in docker since tests are needed - #3078 by @jxltom
- Remove comparing string in address-form-panel template - #3074 by @tomcio1205
- Move updating variant names to a Celery task - #3189 by @fowczarek

### Bugfixes

- Fix typo in `clean_input` method - #3100 by @the-bionic
- Fix typo in `ShippingMethod` model - #3099 by @the-bionic
- Remove duplicated variable declaration - #3094 by @the-bionic

### Docs

- Add createdb note to getting started for Windows - #3106 by @ajostergaard
- Update docs on pipenv - #3045 by @jxltom
