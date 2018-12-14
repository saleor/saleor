# Changelog
All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/mirumee/saleor/releases) page.

## [Unreleased]
- Use `PermissionEnum` as input parameter type for `permissions` field - #3434 by @maarcingebala
- Fix minor visual bugs in Dashboard 2.0 - #3433 by @dominik-zeglen
- Display warning if order draft has missing data - #3431 by @dominik-zeglen
- Add `first_name` and `last_name` fields to the `User` model - #3101 by @fowczarek
- Add description field to collections - #3435 by @dominik-zeglen
- Add payment authorize and charge mutation - #3426 by @jxltom
- Do not show `Pay For Order` if order is partly paid since partial payment is not supported - #3398 by @jxltom
- Add alt text to `Product` `thumbnail` and `background_image` of `Collection` and `Category` - #3429 by @fowczarek
- Improve several payment validations - #3418 by @jxltom
- Fix decimal value argument in GraphQL = #3457 by @fowczarek
- Bump `urllib3` and `elasticsearch` to latest versions - #3460 by @maarcingebala
