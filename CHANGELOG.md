# Changelog

All notable, unreleased changes to this project will be documented in this file. For the released changes, please visit the [Releases](https://github.com/saleor/saleor/releases) page.

# 3.23.0 [Unreleased]

### Breaking changes

### GraphQL API

### Webhooks

### Other changes
- Improved page search with search vectors. Pages can now be searched by slug, title, content, attribute values, and page type information.
- When installing apps that have the same identifier in manifest as an app that is already installed in Saleor, `AppErrorCode.UNIQUE` error code will be now returned instead of `AppErrorCode.INVALID` (backported to 3.22.1)

### Deprecations
