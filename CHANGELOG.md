# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/mirumee/saleor/releases) page.

## [Unreleased]

- Use USERNAME_FIELD instead of hard-code email field when resolving user - #3577 by @jxltom
- Support returning user's checkouts in GraphQL API - #3578 by @fowczarek
- Catch GraphqQL syntax errors and output it to errors field - #3576 by @jxltom
- Fix bug that quantity and variant id of CheckoutLineInput should be required - #3592 by @jxltom
- Register celery task for updating exchange rates - #3599 by @jxltom
- Order by id by default for CartLine - #3593 by @jxltom
- Fix bug where products in homepage should be visible to request.user instead of anonymous user - #3598 by @jxltom
- Simplify mutation's error checking - #3589 by @dominik-zeglen
- Add checkout assignment to the logged in customer - #3587 by @fowczarek
- Refactor `clean_instance`, so it does not returns errors anymore - #3597 by @akjanik
- Fix logo placement - #3602 by @dominik-zeglen
- Add charges taxes on shipping field to shop settings in GraphQL Api - #3603 by @fowczarek
- Make order fields sequence same as dashboard 2.0 - #3606 by @jxltom
- Fix bug where orders can not be filtered by payment status - #3608 by @jxltom
- Fix logo placement in dashboard 2.0 when the svg has specific width - #3609 by @jxltom
- Support get correct payment status for order without any payments - #3605 by @jxltom
- Continue fixing logo placement in storefront 1.0 and dashboard 2.0's login page - #3616 by @jxltom
- Refactor checkout mutations - #3610 by @fowczarek
- Add drag'n'drop image upload - #3611 by @dominik-zeglen
- Throw typescript errors while snapshotting - #3611 by @dominik-zeglen
- Fix order cancelling - #3624 by @dominik-zeglen
- Unify grid handling - #3520 by @dominik-zeglen
- Refactor payments - #3519 by @michaljelonek
- Fix bug where product variant can not have attributes with same slug - #3626 by @jxltom
- Add missing migrations for tax rate choices - #3629 by @jxltom
- Validate files uploaded in API in a unified way - #3633 by @fowczarek
- Add ShopFetchTaxRates mutation - #3622 by @fowczarek
- Add taxes section - #3622 by @dominik-zeglen
- Expose in API list of supported payment gateways - #3639 by @fowczarek
- Display payment status in account order list page and account order detail page - #3637 by @jxltom
- Fix bug where node order is not preserved in GraphQL API - #3632 by @jxltom
- Support set arbitary charge status for dummy gateway in storefront 1.0 - #3648 by @jxltom
- Fix typo in the definition of order UNFULFILLED status - #3649 by @jxltom
- Add missing margin for order notes section - #3650 by @jxltom
- Infer default transaction kind from operation type instead of passing it manually  - #3646 by @jxltom
- Set shipping required as default for product type - #3655 by @jxltom
- Docker and compose improvements - #3657 by @michaljelonek
- Fix TypeError on calling get_client_token - #3660 by @michaljelonek
- Fix countries in Voucher - #3664 by @michaljelonek
- Make tokenCreate errors return [] when there are no errors - #3666 by @michaljelonek
- Require email in CheckoutCreate and CheckoutEmailUpdate - #3667 by @michaljelonek
- Add list mutations to Voucher and Sale - #3669 by @michaljelonek
- Modify Sale/Voucher Inputs to use Date - #3672 by @michaljelonek
- Add component generator - #3670 by @dominik-zeglen
- Fix set-password email to customer created in dashboard - #3688 by @Kwaidan00
- Allow e-mail null in checkout create, always return list for available shipping methods - #3685 by @michaljelonek
- Storefront visual improvements - #3696 by @piotrgrundas
- Fix product list price filter - #3697 by @Kwaidan00
