---
name: saleor-graphql-api-change
description: Checklist for adding, changing, deprecating, or removing anything in the Saleor GraphQL schema — fields, mutations, inputs, enums, or webhook event types. Use whenever a change touches the public GraphQL API so it passes review the first time.
---

# Changing the Saleor GraphQL API

Human reviewers repeatedly send changes back for the same schema mistakes. Work through this
checklist for any change to a GraphQL field, mutation, input, enum, or webhook event type.

## Versioning

- Find the version this branch is cut from: check the latest git tag (e.g. `3.22`). Annotate every
  **new** field/mutation/argument with `ADDED_IN_{VERSION}` for the release it actually ships in — not
  the current `main` version. If the change is backported, use the backport's version.
- After any schema change, **regenerate `schema.graphql`** and commit it. A stale schema file fails CI
  and review.

## Deprecating a field / enum value

- **Deprecate through the real mechanism so the schema emits an `@deprecated` directive** — never by
  writing "DEPRECATED" text into the `description`:
  - Fields/arguments: `deprecation_reason=DEPRECATED_IN_3X_FIELD` (or the input variant).
  - Enum values: `from_enum(SomeEnum, deprecation_reason=<callback>)`.
- Deprecation wording must be precise ("This event **type** will be removed", not "This event").
- When you deprecate/remove a mutation, update related field descriptions to point users at the
  replacement.

## Removing a field (breaking change)

- **Never remove a field that wasn't deprecated in a prior released version.** The order is:
  deprecate → ship a release → remove in a later version. Confirm the deprecation actually shipped.
- **Provide an off-ramp before removing** a field users depend on (a replacement field, metadata, etc.).
- Removing a public field requires a CHANGELOG entry and a **tracked follow-up issue** for the eventual
  DB column drop (see `saleor-migrations` for staged destructive changes).
- For breaking *behavior* (not just schema) changes, stage enforcement across releases —
  warn/silently-ignore first, crash later — so upgraders aren't broken instantly.

## Descriptions

- State **concrete values** (the actual configured limit, not "the number is limited").
- Keep descriptions **in sync with the field's real type and nullability**.
- Describe **what the field is**, not how a specific client should interpret it, and omit internal
  jargon ("atomically", "signed delta").

## Design & consistency

- Prefer a **generic enum value plus a distinguishing flag** over an app/integration-specific enum
  member (`GIFT_CARD` + a brand field, not `SALEOR_GIFT_CARD`). Don't shape the shared API around one
  integration, and don't bake provider-specific length assumptions into shared field limits.
- Mutation return types should be implicitly `required=False`, consistent with existing mutations
  (`OrderSettingsUpdate`, `ShopAddressUpdate`), to avoid non-nullable-field crashes.
- Pass the **type class** to `get_node_or_error(only_type=PageType)`, not the string `"PageType"`
  (gives real typing, drops a `cast`).
- Name new sort/filter enum fields to match the type's existing field names (`createdAt`/`modifiedAt`).
- Don't use `default_value=[]` on Graphene inputs (graphene treats it as a shared literal) — leave it
  optional and default inside the mutation body.
- Don't put any mutable values inside `default_value` Graphene input fields, nor in any
  other defaults (such as function signatures) where this memory pointer or value
  could get mutated (thus potentially leading to unexpected behaviors).
- Guard restricted fields with `PermissionsField`, and add a **separate authorization test per
  permission-gated field**.
- Ensure `class Meta` always defines the `permissions` property unless you are explicitly
  told that you shouldn't.

## Webhook event types

- Add the new event to `WEBHOOK_EVENT_DESCRIPTION` with a description **and** an `ADDED_IN_{VERSION}`
  clause.
- Introduce a **specific error code** for a distinct, actionable failure mode instead of overloading a
  generic `INVALID`.
- Mark high-fan-out events (can reach thousands of objects) with `is_deferred_payload` so payload
  building stays short in the scheduling task; reuse `CustomJsonEncoder` and existing dataloaders.
- Provide a minimal static fallback payload (e.g. `{"id": "Variant:<ID>"}`).

## Before requesting review

- Have you regenerated `schema.graphql`, and are the `ADDED_IN`/`DEPRECATED_IN` annotations correct
  for the release this change actually ships in?
- Do the deprecations show up as `@deprecated` directives in the generated schema, rather than only as
  prose in a description?
- Is every new or changed input/output contract covered by a unit test, including any nullability
  changes?
- Follow the `saleor-pr-checklist` skill for the general PR gate before opening the PR.
