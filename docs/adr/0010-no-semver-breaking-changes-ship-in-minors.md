# Saleor does not follow semver; breaking changes ship in minor releases

**Tags:** graphql, api, versioning

Saleor's version number looks like semver (`3.24.0`) but does not behave like it. A minor release may remove a GraphQL field, change a field's type, rename an enum, or drop a webhook event. Patch releases on an active line (`3.23.x`) may add new GraphQL types and ship schema migrations. Only the major component signals a large, coordinated rewrite — and it is not the gate for breaking changes.

The consequence for anyone reading a version number: **an upgrade between minors is not automatically safe.** The authoritative record of what changed is `CHANGELOG.md` and the upgrade notes, not the version delta.

Rules that follow from this:

- A breaking change must be announced in `CHANGELOG.md` under a "Breaking changes" heading, naming the exact field, type or event and the replacement. The version number carries none of that information.
- Deprecate before removing whenever a replacement can coexist. `@deprecated` in a released minor is the only migration window clients get, and it must last longer than one minor — deprecating and removing one release apart is equivalent to no window at all.
- Prefer a design that avoids the break outright, even when it costs more code. Adding a field alongside an existing one, or introducing an interface rather than swapping a concrete type, keeps every existing document valid. The generic media gallery took this route: `Media` is an interface implemented by per-owner concrete types, so `Product.media` never changed its return type.
- Global IDs, thumbnail proxy URLs and anything else persisted outside the database (CDN caches, rich-text content, customer HTML) can never be broken, regardless of what the schema says. `TYPE_TO_MODEL_DATA_MAPPING["ProductMedia"]` is permanent for that reason.
