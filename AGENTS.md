# Saleor

## Graphql

###  API versioning

- Check last git tag to find what version we are branched from (e.g. 3.22 tag). Based on that, add description to new fields with ADDED_IN_{VERSION} clause


### GraphQL permissions
- Use PermissionsField to describe field restrictions

# Architecture

- Do not use Django signals (e.g. `post_save`, `pre_delete`, `@receiver`). Call the relevant logic explicitly from the code that triggers it instead of wiring it through signal handlers. (The one exception is the `post_migrate` signal used to trigger data-migration tasks — see Data Migrations below.)

# Code style

- Use global import statements. Place all imports at the top of the file rather than inside functions, methods, or other local scopes.

# Testing

## Running in a git worktree

When Saleor is checked out in a git worktree, prefer running operations (tests, management
commands, etc.) inside that worktree's containers rather than on the host machine. The host's
services may belong to a different worktree, so running directly on the host can hit the wrong
database/cache or collide with another worktree's stack.

- Use the `.worktree-container/compose.sh` wrapper, which targets the current worktree's
  isolated stack. Run commands inside the `saleor` service, e.g.:
  ```sh
  .worktree-container/compose.sh up -d                       # start this worktree's stack
  .worktree-container/compose.sh exec saleor pytest --reuse-db saleor/path/to/test_file.py
  .worktree-container/compose.sh exec saleor python manage.py migrate
  ```
- Do not run these operations directly on the host machine when working in a worktree.

## Running tests

- Run tests using `pytest`
- Attach `--reuse-db` argument to speed up tests by reusing the test database
- Select tests to run by passing test file path as an argument
- Inside the dev container, dependencies are installed system-wide, so run `pytest` directly — no virtual environment to activate
- On the host (outside the container), enter the virtual environment before executing tests

## Writing tests

- Use given/when/then structure for clarity
- Use `pytest` fixtures for setup and teardown
- Declare test suites flat in file. Do not wrapp in classes
- Prefer using fixtures over mocking. Fixtures are usually within directory "tests/fixtures" and are functions decorated with`@pytest.fixture`
- When you create an object for testing and fixture for it doesn't exist, create new one. You can use factory to pass arguments to the fixture.
- When writing assertions, prefer assertion on actual returned value instead of checking if it's not none. For example: `assert email is "a@b.com` instead if `assert email is not None`
- When asserting GraphQL errors, assert error message too
- When asserting to Enum, import enum in a test file and use `assert error.code == MyEnum.SOME_ERROR.name` instead plain string comparison
- Avoid assertion to plain values, if you already have references to existing value. For example, when you create entity in database and assert if entity is returned in response, compare response fields with entity fields, instead plain values.
- When building GraphQL query variables, use enum values instead of plain strings. For example: `{"field": TransactionSortField.CREATED_AT.name}` instead of `{"field": "CREATED_AT"}`
- Do not write unnecessary prefix to test names. If file name is `test_my_mutation.py`, do not write `test_my_mutation_with_x_y` but `test_with_x_y`
- When testing graphQL cases with expected errors ALWAYS assert expected length of errors list
- When setting up test data, extract values into variables and reuse them in assertions. Do not repeat literal values between setup and assertion — use the variable instead.
- When comparing JSON payloads in tests, use `json.loads()` to compare dicts instead of comparing serialized strings with `json.dumps()`. String comparison breaks when key order changes.
- When a test expects exactly one row, use `Model.objects.get()` instead of `.first()` followed by an `is not None` assertion. `get()` both fetches the object and asserts that exactly one exists, so drop the separate not-None check.
- For presence/absence checks prefer `qs.exists()` over `qs.count() == 0` / `!= 0`. `exists()` is cheaper than a `COUNT`. Example: `assert checkout.lines.exists() is False`.
- Use `@pytest.mark.parametrize` for variations of the same scenario instead of copy/pasting near-identical test bodies. Label each case with a leading `_case` string parameter rather than the `ids=` argument — it keeps the description next to the data and is easier to read and edit:
  ```python
  @pytest.mark.parametrize(
      ("_case", "value"),
      [
          ("omitted", {}),
          ("empty_list", {"lines": []}),
      ],
  )
  def test_something(_case, value): ...
  ```
- When a mutation input is optional/nullable, test the explicit `null` value in addition to omitting the field — they are distinct inputs and can be handled differently.


# Webhooks and Events

## Dispatching webhook events

When triggering plugin manager methods to dispatch webhook events, always use `call_event` from `saleor.core.utils.events` instead of calling the manager method directly.

**Bad:**
```python
manager.product_variant_discounted_price_updated(price_info, webhooks=webhooks)
```

**Good:**
```python
from saleor.core.utils.events import call_event

call_event(manager.product_variant_discounted_price_updated, price_info, webhooks=webhooks)
```

# Concurrency and Thread Safety

Saleor runs across many Python services that execute concurrently. Follow these patterns to ensure thread-safe code.

## Atomic Increment Pattern

Never use `instance.count += 1; instance.save()` - this is NOT atomic and causes lost updates.

**Bad:**
```python
existing.count += 1
existing.save(update_fields=["count"])
```

**Good - use F() expressions:**
```python
from django.db.models import F

Model.objects.filter(pk=existing.pk).update(count=F("count") + 1)
```

## Avoid Check-Then-Act Race Conditions

Never check if a record exists and then create/update it in separate operations.

**Bad:**
```python
existing = Model.objects.filter(app=app, key=key).first()
if not existing:
    Model.objects.create(app=app, key=key, ...)  # Race condition: duplicate may be created
else:
    existing.update(...)
```

**Good - use update_or_create with unique constraint:**
```python
obj, created = Model.objects.update_or_create(
    app=app, key=key,  # Lookup fields
    defaults={"message": message, "updated_at": now}  # Fields to update
)
```

**Note:** `update_or_create` requires a unique constraint on the lookup fields to be truly safe.


## Row-Level Locking with select_for_update

For complex operations requiring multiple reads/writes on the same row, use `select_for_update`:

```python
from saleor.core.tracing import traced_atomic_transaction

with traced_atomic_transaction():
    obj = Model.objects.select_for_update().get(pk=pk)
    # Perform operations - row is locked until transaction ends
    obj.save()
```

**Pattern: Create lock_objects.py modules** (like `saleor/payment/lock_objects.py`):

```python
def my_model_qs_select_for_update() -> QuerySet[MyModel]:
    return MyModel.objects.order_by("pk").select_for_update(of=["self"])
```

## Database Transactions

Wrap related operations in transactions using `traced_atomic_transaction`:

```python
from saleor.core.tracing import traced_atomic_transaction

with traced_atomic_transaction():
    # All operations here are atomic
    obj1.save()
    obj2.save()
```

## Summary of Patterns Used in Saleor

| Pattern | Module Example | When to Use |
|---------|---------------|-------------|
| `F()` atomic increment | `saleor/discount/utils/voucher.py:85` | Counter updates |
| `select_for_update` | `saleor/payment/lock_objects.py` | Complex read-modify-write |
| `update_or_create` | `saleor/graphql/attribute/utils/type_handlers.py` | Upsert operations |
| `traced_atomic_transaction` | `saleor/core/tracing.py` | Multi-operation atomicity |

# Data Migrations

## Marking search indexes as dirty

When adding or changing search vector indexing logic, create a data migration that marks all existing rows as dirty so they get re-indexed.

### Structure

1. **Task file** — place in `saleor/<app>/migrations/tasks/saleor<version>.py`
2. **Migration file** — place in `saleor/<app>/migrations/<number>_<name>.py`

### Task rules

- Decorate with `@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)` and `@allow_writer()`
- Process in batches (e.g. 1000 rows) to avoid long-running transactions
- Use `select_for_update` via the app's `lock_objects` module to lock rows before updating
- Use the subquery pattern: lock rows first, then filter+update in a separate query:
  ```python
  with transaction.atomic():
      pks = (
          model_qs_select_for_update()
          .filter(pk__in=batch_pks)
          .values_list("pk", flat=True)
      )
      Model.objects.filter(pk__in=pks).update(search_index_dirty=True)
  ```
- Self-chain with `.delay()` at the end if there are more rows to process
- Stop chaining when the batch returns no results

### Migration rules

- Use `post_migrate` signal to trigger the celery task after all migrations complete (not inline)
- Connect to `post_migrate` inside a `RunPython` operation
- Use `registry.get_app_config("<app>")` as the sender
- Always provide `migrations.RunPython.noop` as the reverse operation

### Reference example

- Task: `saleor/giftcard/migrations/tasks/saleor3_22.py`
- Migration: `saleor/giftcard/migrations/0023_mark_gift_cards_search_vector_as_dirty.py`

## Adding indexes / unique constraints concurrently

Building an index synchronously (the default `AddIndex` / `AddConstraint`) takes
an `ACCESS EXCLUSIVE` lock on the whole table for the duration of the build,
blocking reads and writes. On a large table this can mean significant downtime.
Build the index `CONCURRENTLY` instead so it does not block concurrent traffic.

### Rules

- `CREATE INDEX CONCURRENTLY` cannot run inside a transaction, so the migration
  that creates it must set `atomic = False`.
- Keep the concurrent index in its **own** migration. Fast, atomic schema
  changes (`AddField`, `CheckConstraint`, etc.) stay in a normal `atomic = True`
  migration; only the slow, non-atomic index build lives on its own. This keeps
  most schema changes transactional and limits the blast radius if the
  concurrent build fails and has to be retried.
- To back a `UniqueConstraint` with a concurrently-built index, wrap the raw SQL
  in `SeparateDatabaseAndState`: `database_operations` create the index
  `CONCURRENTLY` and attach it via `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE
  USING INDEX`, while `state_operations` hold the matching
  `AddConstraint(UniqueConstraint(...))` so Django's model state stays in sync.
- Always provide `reverse_sql` (use `DROP INDEX CONCURRENTLY IF EXISTS` /
  `DROP CONSTRAINT IF EXISTS`).

### Reference example

- `saleor/page/migrations/0030_slug_translation_unique_constraint.py`
- `saleor/app/migrations/0040_appextension_identifier_unique_constraint.py`
  (split out of the atomic `0039_appextension_identifier_and_more.py`)

# Code style

## Correctness (Django): use `pk` instead of `id`

Don't use the `id` DB field in Django models, instead use `pk` when referencing the object ID
field from a model.

Don't:

```py
book = Book.objects.get(id=1)
id = book.id
```

Do:

```py
book = Book.objects.get(pk=1)
id = book.pk
```

## Prefer docstrings over comments

When describing behavior prefer to use docstring over a comment:

Not:

```python
def foo():
  # Comment
  # instead of
  # docstring
```

Do:

```python
def foo():
  """Doc string"""
```

## Agent skills

### Issue tracker

Issue tracking is opted out — skills must not create issues, PRDs, or triage records anywhere, and should treat "publish to the issue tracker" steps as not applicable. See `docs/agents/issue-tracker.md`.

### Triage labels

Not applicable — there is no issue queue, so the triage state machine and label vocabulary are unused. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

# Performance

- Avoid unnecessarely broad `Model.save()` calls and unnecessarely broad `Model.refresh_from_db()`.
  Instead, use tuples that select specific DB fields, e.g.,
  `invoice.refresh_from_db(fields=("id",))`, or `invoice.save(update_fields=("number",))`
- Avoid iterating over the same objects multiple times (meaning multiple O(N) operations)

  Don't:

  ```py
  assigned_ids = [giftcard.pk for giftcards in assigned_cards]
  deactivated_ids = [giftcard.pk for giftcards in assigned_cards if giftcard.active]
  ```

  Do:

  ```py
  assigned_ids = []
  deactivated_ids = []
  for giftcard in giftcards:
      assigned_ids.append(giftcard.pk)
      if giftcard.active is True:
          deactivated_ids.append(giftcard.pk)
  ```
