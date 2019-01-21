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
- Refactor payments - #3519 by @michaljelonek