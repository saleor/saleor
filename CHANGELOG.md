# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.22.0 [Unreleased]

### Breaking changes
- Increased query cost for attribute-related operations due to the addition of `AttributeValue.referencedObject`.

### GraphQL API

- Added support for filtering products by attribute value names. The `AttributeInput` now includes a `valueNames` field, enabling filtering by the names of attribute values, in addition to the existing filtering by value slugs.
- You can now filter and search orders using the new `where` and `search` fields on the `pages` query.
  - Use `where` to define complex conditions with `AND`/`OR` logic and operators like `eq`, `oneOf`, `range`.
  - Use `search` to perform full-text search across relevant fields.
- Add support for filtering `pages` by associated attributes
- You can now filter and search orders using the new `where` and `search` fields on the `orders` query.
  - Use `where` to define complex conditions with `AND`/`OR` logic and operators like `eq`, `oneOf`, `range`.
  - Use `search` to perform full-text search across relevant fields.
  - Added filtering options for orders:
    - Filter by voucher codes.
    - Filter by invoice existence.
    - Filter by associated invoice creation date.
    - Filter by fulfillment existence.
    - Filter by associated fulfillment status and metadata.
    - Filter by number of lines in the order.
    - Filter by order total gross and net price amount.
    - Filter by order metadata.
    - Filter by associated lines metadata.
    - Filter by the product type of related order lines.
    - Filter by associated event type and date.
    - Filter by associated payment method name and type.
    - Filter by associated billing and shipping address phone number and country code.
    - Filter by associated transactionItems metadata.
- You can now filter and search orders using the new `where` and `search` fields on the `orders` query.
  - Use `where` to define complex conditions with `AND`/`OR` logic and operators like `eq`, `oneOf`, `range`.
  - Use `search` to perform full-text search across relevant fields.
  - Added filtering options for draft orders:
    - Filter by number.
    - Filter by last update date.
    - Filter by voucher codes.
    - Filter by authorize and charge status.
    - Filter by number of lines in the draft order.
    - Filter by draft order total gross and net price amount.
    - Filter by draft order metadata.
    - Filter by draft order by associated lines metadata.
    - Filter by the product type of related order lines.
    - Filter by associated event type and date.
    - Filter by associated payment method name and type.
    - Filter by associated billing and shipping address phone number and country code.
- Extend the `Page` type with an `attribute` field. Adds support for querying a specific attribute on a page by `slug`, returning the matching attribute and its assigned values, or null if no match is found.
- Enhanced order search options. Orders can now be searched using:
  - The order's ID
  - IDs of invoices linked to the order
  - Messages from related order events
  - The content of customer note
  - The order external reference
- Extend sorting options. You can now sort orders by their status.
- Add support for payment method details in the Transaction API. The payment method details associated with a transaction can now be persisted on the Saleor side. See [docs](https://docs.saleor.io/developer/payments/transactions#via-transaction-mutations) to learn more.
- You can now filter and search customers using the new `where` and `search` fields on the `customers` query.
  - Use `where` to define complex conditions with `AND`/`OR` logic and operators like `eq`, `oneOf`, `range`.
  - Use `search` to perform full-text search across relevant fields.
  - Introduced new filtering options for customers:
    - Filter by email address.
    - Filter by first and last name.
    - Filter by active status (`isActive`).
    - Filter by phone numbers and country of associated user addresses.
    - Filter by phone numbers associated with user addresses.
    - Filter by number of orders placed by the user.
- Deprecated the `filter` argument in favor of the new `where` and `search` arguments.
  The `where` argument introduces more flexible filtering, allowing complex conditions using `AND`/`OR` logic and operators such as `eq`, `oneOf`, and `range`.
  The `filter` argument has been deprecated in the following queries:
  - `attributes`
  - `customers`
  - `products`
  - `productVariants`
  - `orders`
  - `draftOrders`
  - `productType.availableAttributes`
  - `category.products`
  - `collection.products`
  - `pageType.availableAttributes`
- Extend `AttributeEntityType` with `CATEGORY` and `COLLECTION`. You can now assign category and collection as a attribute reference.
- Attribute values now expose the `referencedObject`, allowing for easier access to the linked entity.
- You can now filter and search attribute choices using the new `where` and `search` fields on the `attribute.choices` query.
- Filtering products by `category` now also includes subcategories. The filter will return products that belong to the specified categories as well as their subcategories.
- Deprecated `Transaction.gatewayResponse` field. Please migrate to Transaction API and Apps.
- Extend the `Attribute` type with a `values` field, allowing you to retrieve all values assigned to a specific attribute.

### Webhooks
- Transaction webhooks responsible for processing payments can now return payment method details`, which will be associated with the corresponding transaction. See [docs](https://docs.saleor.io/developer/extending/webhooks/synchronous-events/transaction#response-4) to learn more.

### Other changes
- Add JSON schemas for synchronous webhooks, now available in `saleor/json_schemas.py`. These schemas define the expected structure of webhook responses sent back to Saleor, enabling improved validation and tooling support for integrations. This change helps ensure that responses from webhook consumers meet Saleor’s expectations and can be reliably processed.

- deps: upgraded urllib3 from v1.x to v2.x
- Fix PAGE_DELETE webhook to include pageType in payload - #17697 by @Jennyyyy0212 and @CherineCho2016
- Stripe Plugin has been deprecated. It will be removed in the future. Please use [the Stripe App](https://docs.saleor.io/developer/app-store/apps/stripe/overview) instead
- App Extensions: Added new allowed extension target: NEW_TAB. Once handled in the Dashboard, an extension will be able to open a link in new tab
- App Extensions: New mount points for Dashboard categories, collections, gift cards, draft orders, discounts, vouchers, pages, pages types and menus
- App Extensions: Now mount point types have been added, meant to be used as widgets. Additionally, a new target `WIDGET` has been added. For `NEW_TAB` and `WIDGET` targets, new field `options`. See [docs](https://docs.saleor.io/developer/extending/apps/extending-dashboard-with-apps) to learn more
- Changed logging settings of failed requests to reduce logs amount in production:

  - Downgraded the "A query had an error" log from INFO to DEBUG level.
  - Increased the `django.request` logger's level to ERROR, to reduce the number of WARNING logs for failed GraphQL or 404 requests.

  Previously, a failed GraphQL request (up to Saleor 3.21) would generate the following logs:

  ```
  2025-06-06 13:26:06,104 INFO saleor.graphql.errors.handled A query had an error [PID:21676:ThreadPoolExecutor-5_0]
  2025-06-06 13:26:06,107 WARNING django.request Bad Request: /graphql/ [PID:21676:ThreadPoolExecutor-6_0]
  INFO:     127.0.0.1:63244 - "POST /graphql/ HTTP/1.1" 400 Bad Request
  ```

  Starting from Saleor 3.22, the same request logs only the HTTP-level message:

  ```
  INFO:     127.0.0.1:63345 - "POST /graphql/ HTTP/1.1" 400 Bad Request
  ```

  To see details of why a GraphQL request is failing, you can use OpenTelemetry tracing, where each span for a failing request will be marked with an error flag and will include an error message.

- Fixed bug when not-authenticated staff user couldn't fetch `appExtension.app` without `MANAGE_APPS`. Now apps access is available by staff users and the app itself (for app and extension it owns)

- Fixed bug in user email filtering to make it case-insensitive.
