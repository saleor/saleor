---
name: saleor-migrations
description: Rules for writing safe Django migrations in Saleor that don't lock tables or break zero-downtime deploys. Use whenever creating or editing a migration (schema or data), including field removals and index/constraint changes.
---

# Writing Saleor migrations

Saleor deploys with zero downtime across many pods against a shared Postgres. A migration that takes a
long table lock stalls every pod. Follow these rules.

## Keep locks short: split migrations

- **One model per migration, and one field change per migration.** Each schema operation holds a lock
  on the table for its duration; batching several into one migration multiplies the locked time.
- The only valid reason to combine is separating a schema migration from its data migration.
- Always separate schema changes and data migration.
- Don't add a migration that re-alters a column an earlier migration already changed — check the
  existing migration history first.
- Give migrations descriptive names that reflect the actual operation
  (`0070_add_payment_gift_card_brand`, not `0070_alter_payment_partial_add_db_default` for something
  else).

## Indexes and constraints: create concurrently

- **Add unique constraints/indexes concurrently** using the established non-blocking pattern (see e.g.
  `page` migration `0030_slug_translation_unique_constraint`) — a plain `AddConstraint` /
  `AddIndex` takes a blocking `ACCESS EXCLUSIVE` lock and can stall writes across all pods.
- Enforce value invariants (e.g. non-negative balance) with a DB `CheckConstraint`, not just
  application logic.

## Removing a field: stage it

Removing a NOT NULL / defaulted column in one step can fail mid-deploy while old and new pods coexist.
Stage it across releases:

1. Add a `db_default` so the DB can write the column without the ORM.
2. Remove the field from the ORM model (column still present).
3. **Drop the column in a later version**, tracked by an explicit follow-up issue.

Keep any legacy enum values / code retained only for migration safety tracked as a removal task with a
"remove in X.Y" note.

## Data migrations

- A data migration must be **all-or-nothing**: process everything or nothing. Don't abort partway on a
  fixed depth/count cap and leave a partial migration.
- **`post_migrate` sender must be the migration's own app config** — a common copy-paste bug is
  `registry.get_app_config("product")` inside an `account`/`order` migration.
- Use a module/task **constant** (like `BATCH_SIZE`) for internal tuning knobs, not an env var nobody
  will set.
- When cleaning up (e.g. removing a permission), address **all** models that hold the value
  (App, AppExtension, AppInstallation, …), or document why one is handled elsewhere.
- Watch for per-iteration DB queries (`O(N)` vs `O(1)`); batch related lookups.

## Cross-branch ports

- Keep a ported migration's **filename identical** to its counterpart on the other branch, and add a
  merge migration where histories diverge.
- Keep a ported migration's **filename identical** to its counterpart on the other branch, and add a
  merge migration where histories diverge using `./manage.py makemigrations --merge`.
## Before requesting review

- Confirm each migration touches a single model and a single field, and that any index or constraint
  is created concurrently rather than with a blocking operation.
- Confirm every destructive column change is staged across releases (add `db_default`, then remove the
  field from the ORM, then drop the column in a later version).
- Confirm each `post_migrate` handler passes its own app config as the sender, and that every data
  migration is all-or-nothing rather than aborting partway.
- Run the migration locally with `manage.py migrate` and confirm it applies cleanly.
