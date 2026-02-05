# Saleor

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
