# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/mirumee/saleor/releases) page.

## [Unreleased]

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
- Fix checkout and order flow with variant without inventory tracking - #5599 by @fowczarek
- Fixed JWT expired token being flagged as unhandled error rather than handled. - #5603 by @NyanKiyoshi
- Refactor read-only middleware - #5602 by @maarcingebala
- Fix availability for variants without inventory tracking - #5605 by @fowczarek

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
