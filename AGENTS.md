# Saleor

## Deployment model (read this first)

Saleor is deployed for **horizontal scale-out: many identical Kubernetes pods** (web + Celery
workers) run concurrently behind a load balancer, against a **shared Postgres (with read replicas)
and shared Redis/broker**. Any given request or task may land on any pod, and the same code runs in
many processes at once. Write code with that in mind:

- **No in-process/local state as source of truth.** Never rely on module globals, in-memory caches,
  or a value set by a previous request being present on the next one — the next call hits a different
  pod. Shared state lives in Postgres/Redis.
- **Assume every operation runs concurrently with itself.** Use atomic DB operations
  (`F()`, `update_or_create`, `select_for_update`) instead of check-then-act — see *Concurrency and
  Thread Safety* below.
- **Never block a request/worker thread.** No `time.sleep()` and no unbounded `while True` retry loops
  in request-handling code — a blocked thread wastes a finite pod worker slot. Use bounded retries and
  background tasks.
- **Schedule background work after the transaction commits.** Use `on_commit` / `call_event` (not a
  bare `.delay()` inside an open transaction) so a task can't run on another pod before the row it
  needs is committed.
- **Protect the shared database.** It is the scaling bottleneck: avoid N+1 queries and per-row writes
  in loops (bulk instead), keep `select_for_update` transactions short, fetch only the columns you
  need, and don't add per-request queries to hot paths — reuse dataloaders.
- **Make tasks idempotent and safe to retry** — the broker may deliver a task more than once, and pods
  can be killed/rescheduled mid-run.

## Graphql

###  API versioning

- Check last git tag to find what version we are branched from (e.g. 3.22 tag). Based on that, add description to new fields with ADDED_IN_{VERSION} clause


### GraphQL permissions
- Use PermissionsField to describe field restrictions

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
- When setting up test data, extract values into variables and reuse them in assertions. Do not repeat literal values between setup and assertion — use the variable instead.
- When comparing JSON payloads in tests, use `json.loads()` to compare dicts instead of comparing serialized strings with `json.dumps()`. String comparison breaks when key order changes.

### Assert precisely (the #1 source of review comments)

- **Assert exact values and counts, never bounds or mere absence.** No `len(x) > 0`, `>= 1`,
  `assert not errors`, or `call_count >= 1` — assert the exact count, enum, or object so unexpected
  extra results are caught. When one error is expected, assert *exactly one*, its full message, and
  its `path`/field.
- **On negative / permission-denied tests, also assert the side effect did NOT happen** — balance
  unchanged, `SomeEvent.objects.exists() is False`, the object left unmutated. An error assertion
  alone doesn't prove the action was blocked.
- **Never assert a value the test itself just set and saved** — that verifies the ORM, not the code
  under test. Set state *or* assert it, not both.
- **Deep-copy an input before passing it to code that may mutate it**, then assert the `copy.deepcopy`
  snapshot against the expected value. Comparing a mutated object to itself can never fail.
- **Prefer real fixtures/tokens over mocking internals.** Generate a genuinely valid/invalid token
  (e.g. via the real `create_access_token*` factories or pyjwt) rather than mocking `get_decoded_token`
  to return a canned payload — otherwise real breakage isn't caught.
- **A fix must ship with a regression test that reproduces the *actual* reported bug** end-to-end and
  targets the field/path that actually failed — not just the new helper's happy path.
- **Encode preconditions as assertions, not comments** (`assert flag is True` before exercising it),
  so the test fails fast if a default changes.
- Use `Model.objects.get()` when exactly one row is expected (it asserts uniqueness) instead of
  `.first()` + a not-None check, and `qs.exists()` instead of `qs.count() == 0`.
- Don't hardcode a "nonexistent" primary key (e.g. `99999`) — `--reuse-db` can reassign it; derive a
  guaranteed-absent id (create then delete, or `max(pk)+1`).
- Use reserved test domains (`example.com`, `*.test`) for any URL in a test, never a real one.
- Parametrize near-identical test bodies; keep each test minimal (drop unrelated setup); name tests
  for the exact behavior asserted (no double negatives).

# Code structure and layering

- **Keep business logic in the domain layer; GraphQL mutations do input validation and orchestration
  only.** How a token is built/stripped, how a balance changes, etc. belongs in the domain module, not
  in the mutation.
- **Non-GraphQL code must never import from the `graphql` layer.** If a domain-layer task or model
  needs a helper, move that helper into the domain module and import it *from* the GraphQL layer —
  never the reverse.
- **Validate at the point data is produced (fail-fast)**, and clean a sub-entity inside the same clean
  step that owns its parent — don't split one entity's cleaning across separate stages.
- **Pass the narrow value a function actually needs** (a single flag or an already-fetched setting),
  not a broad `info` / `SiteSettings` context object it has to dig into. A wide parameter hides the
  real dependency and forces callers to re-thread context.
- **Prefer typed structures (`dataclass`/`NamedTuple`) over ad-hoc `dict` grab-bags**, and keep a
  function's return shape homogeneous (don't mix heterogeneous entities in one list).
- Extract branchy or long logic into a named helper instead of narrating a ~100-line function with
  comments. Run short-circuit / global checks first, before fetching data.
- Remove code a refactor made dead (unused validators, unreachable guards added only to satisfy mypy).
  Fix the type at its source instead of adding a `cast()` around a wrong upstream annotation.

# Naming

- No cryptic abbreviations (`gc_brand` → `gift_card_brand`); align a new field's name to the analogous
  existing field.
- **Use positive boolean names** — `delivery_changed`, not `not delivery_unchanged`.
- **Prefix any flag or field that gates deprecated behavior with `legacy_`** so the deprecation is
  obvious from the name alone.
- Name things for what they return/mean and the correct domain, not an incidental call site, and don't
  bake a format assumption into a name (`last_digits` when a code may contain letters → `last_chars`).

# Error handling

- **Catch the specific exception, never a bare `Exception` or `DatabaseError`.** Catch the whole
  provider family when needed (`BotoCoreError` *and* `ClientError`; `GoogleAPIError` for 4xx *and*
  5xx) and the narrowest DB exception that fits (`OperationalError`, not the base class).
- **Distinguish retryable failures (network errors, HTTP 5xx) from terminal ones (4xx, bad data,
  `ValueError`)** — never retry what can't self-recover; return/abort terminal cases immediately so
  invalid work drains fast. Check an HTTP response's status code before reading its body, and always
  pass an explicit timeout to outbound network calls.
- Error messages must state the actual cause ("not found" vs "wrong type"), be attributed to the
  specific line/field for list inputs, and use generic (non-field) errors for config/store-level
  failures. Propagate the original caught message rather than rewriting it.
- Validate referenced GraphQL IDs and return a clean error — don't let a bad/nonexistent id surface a
  cryptic "Cannot return null for non-nullable field" crash.

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

## Schedule background work after commit

Never schedule a Celery task with a bare `.delay()` inside an open transaction — the task can start on
another pod before the transaction commits and fail on data it can't see yet. Schedule via `on_commit`
(or `call_event`, which does this for webhook events) so the task only fires after the commit:

```python
from django.db.transaction import on_commit

with traced_atomic_transaction():
    obj.save()
    on_commit(lambda: my_task.delay(obj.pk))
```

Wrap multi-write / read-modify-write operations in a transaction so they are all-or-nothing, and emit
a state-change event inside the same transaction as the change.

## Never block a request/worker thread

No `time.sleep()` and no unbounded `while True` retry loops in request-handling or worker code — a
blocked thread wastes one of the pod's finite worker slots. Use bounded `for attempt in range(n)`
retries and offload waiting to background tasks.

## Other concurrency rules

- **Scope `allow_writer()` to the exact statement that needs it** (`with allow_writer(): ...`), not the
  whole task/function.
- **Re-establish the DB/writer context inside every Promise `.then()` callback** — it runs after the
  previous context has exited (like async), so a writer/context opened before `.then()` is gone inside it.
- **Never gate a blocking `Queue.get()` on a separate `empty()`/non-empty check** across threads — the
  last item can be drained between the check and the get, hanging the consumer. Use a non-blocking get
  or a sentinel.
- Route heavyweight fan-out tasks (large downloads, thousands of objects) to a dedicated, bounded queue
  so a single bulk mutation can't starve workers or OOM a pod.

## Summary of Patterns Used in Saleor

| Pattern | Module Example | When to Use |
|---------|---------------|-------------|
| `F()` atomic increment | `saleor/discount/utils/voucher.py:85` | Counter updates |
| `select_for_update` | `saleor/payment/lock_objects.py` | Complex read-modify-write |
| `update_or_create` | `saleor/graphql/attribute/utils/type_handlers.py` | Upsert operations |
| `traced_atomic_transaction` | `saleor/core/tracing.py` | Multi-operation atomicity |
| `on_commit` task scheduling | Any mutation that dispatches a task | Fire task only after commit |

# Database access

The shared Postgres is the scaling bottleneck — every pod hits it. Keep queries cheap and few.

- **No per-row query in a loop (N+1).** Build a dict keyed by the join fields for O(1) lookups, or do a
  single aggregate / `filter(...).exists()` across all rows.
- **Bulk `queryset.update()` / `.delete()`** instead of saving/deleting per row, and **`.iterator()`**
  instead of `list()` on an unbounded queryset.
- **Fetch only the columns you need** (`.values(...)` / `.values_list("pk", flat=True)`), not full
  model instances, when that's all you use.
- Use `qs.exists()` over `qs.count() == 0`.
- **Don't add per-request DB queries to hot paths** (auth, resolvers) — reuse dataloaders. Don't bypass
  a dataloader to "get the latest" value; the data is replica-delayed anyway, so the extra query buys
  no real consistency.
- Keep `select_for_update` transactions short (no `list()` of unbounded sets or per-row queries while
  holding the lock). Don't persist rows purely for debugging/observability — log instead (writes
  replicate to every read replica).

# Data minimization

- **Don't denormalize user PII** (email, etc.) into other tables or event params — store only the
  reference id. Register any new user-referencing/PII field with the anonymizer app, and ensure PII is
  deleted with the user (`on_delete=PROTECT` + deactivate, not `SET_NULL` that leaves orphaned data).
- **Treat any downloaded file or URL as untrusted**: `Content-Type` headers are spoofable (confirm the
  real type from magic bytes), enforce an allowed-format allowlist (reject SVG and other
  executable/vector formats), enforce a maximum size, and check the HTTP status before reading the body.
