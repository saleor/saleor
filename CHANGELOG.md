# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/mirumee/saleor/releases) page.

## [Unreleased]

- Refactor error handling in mutations #3891 by @maarcingebala @akjanik
- Use only_fields instead of exclude_fields in gql api - #3940 by @michaljelonek
- Add mutation for bulk delete order lines - #3935 by @akjanik
- Fix dashboard 1.0 missing logo and missing back arrow on collections - #3958 by @NyanKiyoshi
- Add mutations for publishing and unpublishing multiple pages - #3954 by @akjanik
- Prefetch collections when getting sales of a bunch of products - #3961 by @NyanKiyoshi
- Move dialog windows to querystring rather than router paths - #3953 by @dominik-zeglen
- Add mutation for bulk cancel orders - #3967 by @akjanik
- Hide errors in TokenVerify mutation - #3981 by @fowczarek
- Use newest GraphQL Playground - #3971 by @salwator
- Fix country area choices - #4008 by @fowczarek
- Cleanup and maintenance of the GraphQL API code - #3942 by @NyanKiyoshi
- Removed the dead `children` field from the `Menu` type - #3973 by @NyanKiyoshi
- Add mutations for bulk publishing and unpublishing products - #3969 by akjanik
- Add mutation for bulk publishing and unpublishing collections - #3970 by @akjanik
- Unittests use none as media root - #3975 by @korycins
- Rename Cart to Checkout - #3963 by @michaljelonek
- Implement menus items reordering into the GraphQL API - #3958 by @NyanKiyoshi
- Simplify permission management in API through the meta classes - #3980 by @NyanKiyoshi
- Add settings to enable Django Debug Toolbar - #3983 by @koradon
- Implement variant availability, introducing discounts in variants - #3948 by @NyanKiyoshi
- Add bulk actions - #3955 by @dominik-zeglen
- Update file field styles with materializecss template filter - #3998 by @zodiacfireworks
- Add filtering interface for graphQL API - #3952 by @korycins
- Restrict single payment resolving - #4009 @NyanKiyoshi
- Add mandatory fields errors in new product form - #4024 by @benekex2
- Add navigation drawer support - #3839 by @benekex2
- Set up explicit __hash__ function - #3979 by @akjanik
- Update node-sass to latest version to fix node-js 12 compatibility - #4033 @NyanKiyoshi
- Ensure adding to quantities in checkout is respecting the limits set both in storefront 1.0 and in the API - #4005 by @NyanKiyoshi
- Fix price_range_as_dict function - #3999 by @zodiacfireworks
- Remove unused decorator - #4036 by @maarcingebala
- Overall improvement of the GraphQL performances, especially on single nodes - #3968 @NyanKiyoshi
- Remove unnecessary dedents from GraphQL schema so new Playground can work - #4045 by @salwator


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
