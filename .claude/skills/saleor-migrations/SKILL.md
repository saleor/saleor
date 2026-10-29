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

## Backwards compatibility: the new schema must work with the *old* code

During a rolling deploy, pods running the **previous** minor version talk to the **already-migrated**
database. Django `SELECT`s and `UPDATE`s every column it knows about, so the schema must stay valid
for that old ORM. Making the DB backwards-compatible is the default; changing old code requires
crafting two releases at once — reserve it for cases where nothing else works.

### Adding a field

Old pods insert rows without knowing the column, so it must be writable without them:
`null=True` **or** a `db_default`. Plain Django `default=` is not enough — it lives in Python and never
reaches the database.

### Removing a field: stage it across three releases

Removing a NOT NULL / defaulted column in one step can fail mid-deploy while old and new pods coexist.

1. **N** — add a `db_default` (or `null=True`) so the DB can write the column without the ORM.
2. **N+1** — de-register the field from the ORM, leaving the column in place, via
   `SeparateDatabaseAndState`: `state_operations=[RemoveField(...)]` and `database_operations` that
   make the column nullable. Old pods still find the column; new pods no longer touch it.
3. **N+2** — drop the column, now that no process uses it. Track it as an explicit follow-up.

```python
migrations.SeparateDatabaseAndState(
    database_operations=[
        migrations.AlterField(
            model_name="sitesettings",
            name="automatically_confirm_all_new_orders",
            field=models.BooleanField(null=True, blank=True),
        ),
    ],
    state_operations=[
        migrations.RemoveField(
            model_name="sitesettings",
            name="automatically_confirm_all_new_orders",
        ),
    ],
)
```

Keep any legacy enum values / code retained only for migration safety tracked as a removal task with a
"remove in X.Y" note.

### Renaming or moving a field

Avoid unless necessary — a rename is an add plus a remove, so it costs the same three releases.

1. **N** — add the new field (`null=True`), and write **both** old and new fields everywhere the old
   one is written, so old pods keep seeing valid data. Add a data migration that backfills the new
   field. Note in the upgrade guide that N+1 requires upgrading to this patch release first.
2. **N+1** — read from the new field. Re-run the backfill data migration (old pods may have inserted
   rows in the old format between step 1's migration and the cutover), then drop `null=True` from the
   new field. De-register the old field per "Removing a field" step 2.
3. **N+2** — drop the old column.

Handle "new field is null but old one isn't" while both exist.

**Any data migration that reshapes data written by old pods runs twice** — once before the new code
deploys, once in the next version when the old code is provably gone.

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
  field from the ORM via `SeparateDatabaseAndState`, then drop the column in a later version).
- Confirm every new column is nullable or has a `db_default` — a Python-only `default=` leaves old pods
  unable to insert.
- Confirm any data migration over data old pods still write is scheduled to run again in the next
  version.
- Confirm each `post_migrate` handler passes its own app config as the sender, and that every data
  migration is all-or-nothing rather than aborting partway.
- Run the migration locally with `manage.py migrate` and confirm it applies cleanly.
