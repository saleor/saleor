# Saleor

## Graphql

###  API versioning

- Check last git tag to find what version we are branched from (e.g. 3.22 tag). Based on that, add description to new fields with ADDED_IN_{VERSION} clause


### GraphQL permissions
- Use PermissionsField to describe field restrictions

# Testing

## Running tests

- Run tests using `pytest`
- Attach `--reuse-db` argument to speed up tests by reusing the test database
- Select tests to run by passing test file path as an argument
- Enter virtual environment before executing tests

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
-

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
