# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.22.0

### Breaking changes
- The following changes were implemented to orders with a zero total amount:
  - No manual charge (`Transaction` or `Payment`) object will be created.
  - The `OrderEvents.ORDER_MARKED_AS_PAID` event will no longer be emitted.
- Logic associated with `WebhookEventAsyncType.CHECKOUT_FULLY_PAID` event will no longer be triggered when creating a transaction event from webhook response for checkouts with having total gross being 0. At the point of creating the transaction event checkout is already considered fully paid.
- Creating a Payment (old API) for a Checkout object with an existing Transaction (new API) is no longer permitted as it leads to inconsistent behavior.
- Webhooks are no longer triggered for deactivated Apps.

### GraphQL API

- You can now filter and search Models (previously named "Pages") using the new `where` and `search` fields on the `pages` query.
  - The `where` argument supports `AND`/`OR` logic and explicit operators (`eq`, `oneOf`, `range`) for all fields.
  - Existing `filter` fields remain available in `where`: `ids`, `page_types` (now `page_type`), `slugs` (now `slug`), `metadata`.
  - New filtering options available only in `where`:
    - `attributes` - Filter by attributes associated with the page, including:
      - Filter by attribute slug and name
      - Filter by numeric attribute values (with `eq`, `oneOf`, `range` operators)
      - Filter by boolean attribute values
      - Filter by date and datetime attribute values
      - Filter by reference attributes to pages, products, product variants, categories, and collections (by IDs or slugs)
      - Support for `contains_all` (page must reference ALL specified objects) and `contains_any` (page must reference at least ONE specified object)
  - The `search` parameter is now a standalone argument (previously `filter.search`). It works the same as before, searching across page title, slug, and content.
- You can now filter and search orders using the new `where` and `search` fields on the `orders` query.
  - The `where` argument supports `AND`/`OR` logic and explicit operators (`eq`, `oneOf`, `range`) for all fields.
  - Existing `filter` fields remain available in `where`: `ids`, `channels` (now `channel_id`), `customer`, `created` (now `created_at`), `updated_at`, `status`, `authorize_status`, `charge_status`, `payment_status`, `is_click_and_collect`, `is_preorder`, `checkout_tokens` (now `checkout_token`), `checkout_ids` (now `checkout_id`), `gift_card_used` (now `is_gift_card_used`), `gift_card_bought` (now `is_gift_card_bought`), `numbers` (now `number`), `metadata`.
  - New filtering options available only in `where`:
    - `user` - Filter by user ID.
    - `user_email` - Filter by user email.
    - `voucher_code` - Filter by voucher code used in the order.
    - `has_invoices` - Filter by whether the order has any invoices.
    - `invoices` - Filter by invoice data (creation date, etc.).
    - `has_fulfillments` - Filter by whether the order has any fulfillments.
    - `fulfillments` - Filter by fulfillment data (status, metadata, warehouse).
    - `lines` - Filter by line item data (metadata, product details, quantities).
    - `lines_count` - Filter by number of lines in the order.
    - `transactions` - Filter by transaction data (payment method name and type, metadata). Note: Payment method filtering only works for transactions created after upgrading to this release: [see docs](https://docs.saleor.io/developer/payments/transactions#via-transaction-mutations).
    - `total_gross` - Filter by total gross amount.
    - `total_net` - Filter by total net amount.
    - `product_type_id` - Filter by the product type of related order lines.
    - `events` - Filter by order event type and date.
    - `billing_address` - Filter by billing address fields (phone number, country code, city, postal code, etc.).
    - `shipping_address` - Filter by shipping address fields (phone number, country code, city, postal code, etc.).
  - Use `search` to perform PostgreSQL full-text search (using websearch mode) across relevant fields. Results are ranked by relevance using the following weights:
    1. Weight A (Highest priority):
      - Order number
      - Order ID
      - User email stored on order (`user_email` field)
      - Associated user's email (`user.email` field)
      - Associated user's first name
      - Associated user's last name
    2. Weight B:
      - Customer note
      - Order external reference
      - Billing address fields: first name, last name, street address (line 1 and 2), company name, city, city area, country name, country code, country area, postal code, phone number
      - Shipping address fields: first name, last name, street address (line 1 and 2), company name, city, city area, country name, country code, country area, postal code, phone number
    3. Weight C:
      - Order line fields (up to configured `SEARCH_ORDERS_MAX_INDEXED_LINES` limit):
        - Product SKU
        - Product name
        - Variant name
        - Translated product name
        - Translated variant name
    4. Weight D (Lowest priority):
      - Discount name and translated name (up to configured `SEARCH_ORDERS_MAX_INDEXED_DISCOUNTS` limit)
      - Payment global ID and PSP reference (legacy API, up to configured `SEARCH_ORDERS_MAX_INDEXED_PAYMENTS` limit)
      - Transaction global ID, PSP reference, and transaction event PSP references (up to configured `SEARCH_ORDERS_MAX_INDEXED_TRANSACTIONS` limit)
      - Invoice global ID (up to configured `SEARCH_ORDERS_MAX_INDEXED_INVOICES` limit)
      - Order event messages from `NOTE_ADDED` and `NOTE_UPDATED` events (up to configured `SEARCH_ORDERS_MAX_INDEXED_EVENTS` limit)
- Order sorting options were extended. You can now sort orders by their status.
- You can now filter and search draft orders using the new `where` and `search` fields on the `draftOrders` query.
  - The `where` argument supports `AND`/`OR` logic and explicit operators (`eq`, `oneOf`, `range`) for all fields.
  - Existing `filter` fields remain available in `where`: `channels` (now `channel_id`), `customer`, `created` (now `created_at`), `metadata`.
  - New filtering options available only in `where`:
    - `ids` - Filter by order IDs.
    - `number` - Filter by order number.
    - `updated_at` - Filter by last update date.
    - `user` - Filter by user ID.
    - `user_email` - Filter by user email.
    - `authorize_status` - Filter by authorize status.
    - `charge_status` - Filter by charge status.
    - `is_click_and_collect` - Filter by whether the order uses click and collect delivery.
    - `voucher_code` - Filter by voucher code used in the order.
    - `lines` - Filter by line item data (metadata, product details, quantities).
    - `lines_count` - Filter by number of lines in the draft order.
    - `transactions` - Filter by transaction data (payment method name and type, metadata). Note: Payment method filtering only works for transactions created after upgrading to this release: [see docs](https://docs.saleor.io/developer/payments/transactions#via-transaction-mutations).
    - `total_gross` - Filter by total gross amount.
    - `total_net` - Filter by total net amount.
    - `product_type_id` - Filter by the product type of related order lines.
    - `events` - Filter by order event type and date.
    - `billing_address` - Filter by billing address fields (phone number, country code, city, postal code, etc.).
    - `shipping_address` - Filter by shipping address fields (phone number, country code, city, postal code, etc.).
  - Note that compared to `orders`, draft orders do not support filtering by: `status`, `checkout_token`, `checkout_id`, `is_gift_card_used`, `is_gift_card_bought`, `has_invoices`, `invoices`, `has_fulfillments`, `fulfillments`.
  - Use `search` to perform full-text search across relevant fields, it works the same as `orders` search (see above).

- You can now filter and search customers using the new `where` and `search` fields on the `customers` query.
  - Use `where` to define complex conditions with `AND`/`OR` logic and operators like `eq`, `oneOf`, `range`. It also adds new filtering options for customers:
    - Filter by email address.
    - Filter by first and last name.
    - Filter by active status (`isActive`).
    - Filter by phone numbers and country of associated user addresses.
    - Filter by phone numbers associated with user addresses.
    - Filter by number of orders placed by the user.
  - Use `search` to perform pattern-matching search across relevant fields:
    - Customer's email address, first name, last name
    - Addresses in customer address book: first name, last name, street, city, postal code, country (code and name), phone
- Added support for payment method details in the Transaction API. The payment method details associated with a transaction can now be persisted on the Saleor side, instead of using metadata or external storage. See [docs](https://docs.saleor.io/developer/payments/transactions#via-transaction-mutations) to learn more.
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
- Extend `AttributeEntityType` with `CATEGORY` and `COLLECTION`. You can now assign categories and collections as a attribute reference.
- You can now filter and search attribute choices using the new `where` and `search` fields on the `attribute.choices` query.
- Filtering products by `category` now also includes subcategories. The filter will return products that belong to the specified categories as well as their subcategories.
- Deprecated `Transaction.gatewayResponse` field. Please migrate to Transaction API and Apps.
- Added new `SINGLE_REFERENCE` attribute type. You can now create a reference attribute that points to only one object (unlike the existing `REFERENCE` type, which supports multiple references). They can target the same entities as `REFERENCE` attributes (defined in the `AttributeEntityTypeEnum`).
- Extended support for filtering `products` by associated attributes
  - Attribute slug is now optional when filtering by attribute values
  - Added support for filtering by associated reference objects (e.g., `products`, `pages`, `variants`)
- Added `fractionalAmount` and `fractionDigits` fields to the `Money` type. These fields allow monetary values to be represented as an integer (instead of a float) with an explicit precision provided in `fractionDigits`, which is often required when integrating with payment service providers and allows for safe calculations.
- Add support for filtering `productVariants` by associated attributes
- Refunds are now more powerful. You can configure new `RefundSettings` globally (for all channels) to accept a `reasonReferenceType` using `refundSettingsUpdate` mutation. Once assigned, creating refunds (both manual and with grant refund) will require a reason type to be specified. `refundReasonReferenceTypeClear` mutation clears the settings.
- You can now use the `AssignedAttribute` interface and the `assignedAttribute`, `assignedAttributes` fields on `Page`, `Product`, and `ProductVariant` to fetch assigned attributes and their values in a cleaner, more focused shape.
  - `attribute` and `attributes` fields on Page, Product, and ProductVariant are deprecated.
- Added support for restricting available reference to choose from for `REFERENCE` and `SINGLE_REFERENCE` attributes by specifying reference types (product, product variant, model, etc.).
  - You can now define `referenceTypes` on an `Attribute` to limit reference choices. Use `productType` for product and product variant references, and page types for page references.

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

- Checkouts having total gross amount equal to 0 will get their authorization statuses updated to `CheckoutAuthorizeStatus.FULL` upon fetching checkout data.

- Fixed a bug that could prevent rich text attributes written in scripts using combining diacritical marks (for example, Arabic) from being saved properly.

- Fixed a bug where a Checkout partially paid by Transaction(s) and partially paid by Gift Card(s) could not be completed due to `CHECKOUT_NOT_FULLY_PAID` error. Checkout authorize and charge statuses are now recalculcated more reliably. Status calculcation is now taking into account available gift cards balance.

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
