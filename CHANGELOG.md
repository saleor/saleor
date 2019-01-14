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
