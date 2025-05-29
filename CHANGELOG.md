# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.22.0 [Unreleased]

### Breaking changes

### GraphQL API
- You can now filter and search orders using the new `where` and `search` fields on the `orders` query.
  - Use `where` to define complex conditions with `AND`/`OR` logic and operators like `eq`, `oneOf`, `range`.
  - Use `search` to perform full-text search across relevant fields.
- Extend the `Page` type with an `attribute` field. Adds support for querying a specific attribute on a page by `slug`, returning the matching attribute and its assigned values, or null if no match is found.

### Webhooks

### Other changes
- deps: upgraded urllib3 from v1.x to v2.x
- Fix PAGE_DELETE webhook to include pageType in payload - #17697 by @Jennyyyy0212 and @CherineCho2016
