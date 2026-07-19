---
name: filter-benchmark
description: Benchmark and performance-test Django ORM filters on large datasets. Use this skill whenever the user wants to test filter performance, check query plans with EXPLAIN ANALYZE, generate bulk test data for filters, verify index usage, or benchmark any queryset filter in the Saleor codebase. Trigger this even when the user says things like "test the filter on a big dataset", "check if the index is used", "generate data for performance testing", "run explain analyze on this filter", or "benchmark this query".
---

# Filter Benchmark

Performance-test Django ORM filters by generating bulk data, extracting the SQL query, and running EXPLAIN ANALYZE to verify index usage and query efficiency.

## Overview

When adding or modifying filters in the Saleor GraphQL layer, it's critical to verify they perform well on large datasets — a filter that looks correct on 10 rows can cause full table scans on 100k+. This skill automates the full benchmarking workflow:

1. **Identify** — Read the filter code, understand what fields and joins it touches, check existing indexes
2. **Generate data** — Write a bulk population script that creates realistic, varied data targeting the exact fields the filter uses
3. **Populate** — Run the script in Django shell to reach 100k+ rows
4. **Extract SQL** — Get the actual query the filter produces from the Django ORM
5. **EXPLAIN ANALYZE** — Run the query plan analysis and check for seq scans, missing indexes, and performance issues
6. **Report** — Summarize findings and suggest concrete fixes (new indexes, query rewrites)

## Step 1: Identify what to benchmark

Read the filter code to understand:
- Which model(s) are being filtered
- Which fields are involved (including related model fields for subquery filters)
- What indexes exist on those fields (check the model's `Meta.indexes`)
- What filter input combinations matter (e.g., date ranges, enum values, subqueries with `Exists`)

Look at the filter function source — it lives in `saleor/graphql/<app>/filters.py`. Understand the ORM query it builds (`.filter()`, `Q()`, `Exists()`, `OuterRef()`, etc.) because the test data must exercise all code paths.

## Step 2: Generate bulk data script

Write a Python script that creates test data with enough variety to exercise the filter. The script should:

- Use `bulk_create` with `ignore_conflicts=True` for maximum speed
- Create data in batches (1000-5000 objects per batch) to avoid memory issues
- Vary the field values that the filter targets so the query planner sees realistic data distribution
- For date fields: spread values across a wide range (months/years), not just a narrow window
- For enum/choice fields: distribute across all possible values
- For related objects (e.g., events on a transaction): create multiple per parent with varied attributes
- Handle required foreign keys by creating or reusing minimal parent objects (orders, checkouts, etc.)
- Use `timezone.now()` and `timedelta` for date generation
- Override `auto_now` / `auto_now_add` fields via `bulk_update` after creation when needed

The script should be a function that creates ~1000 objects per call. The user will call it in a loop to reach 100k+.

**Example structure:**

```python
import random
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from saleor.payment.models import TransactionItem, TransactionEvent
from saleor.payment import TransactionEventType


def populate(batch_size=1000):
    """Create batch_size TransactionItems with varied events."""
    now = timezone.now()

    # Create TransactionItems
    transactions = TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                currency="USD",
                charged_value=Decimal("10.00"),
                # Vary dates across 2 years
                created_at=now - timedelta(days=random.randint(0, 730)),
            )
            for _ in range(batch_size)
        ]
    )

    # Override auto_now/auto_now_add fields with varied values via bulk_update
    for t in transactions:
        t.created_at = now - timedelta(days=random.randint(0, 730))
        t.modified_at = now - timedelta(days=random.randint(0, 365))
    TransactionItem.objects.bulk_update(transactions, ["created_at", "modified_at"])

    # Create events for each transaction
    event_types = [e.value for e in TransactionEventType]
    events = []
    for t in transactions:
        num_events = random.randint(1, 4)
        for _ in range(num_events):
            events.append(
                TransactionEvent(
                    transaction=t,
                    type=random.choice(event_types),
                    amount_value=Decimal("10.00"),
                    currency="USD",
                    created_at=now - timedelta(days=random.randint(0, 730)),
                )
            )
    TransactionEvent.objects.bulk_create(events)
    print(
        f"Created {len(transactions)} transactions and {len(events)} events. "
        f"Total: {TransactionItem.objects.count()} transactions, "
        f"{TransactionEvent.objects.count()} events"
    )
```

Adapt this pattern to whatever model and filter is being tested. The key principle: the data must vary on exactly the fields the filter touches.

## Step 3: Populate the database

Run the population script in Django shell. Activate the venv first:

```bash
source .venv/bin/activate && python manage.py shell
```

Then in the shell, run the function in a loop:

```python
for i in range(100):
    populate()
```

This reaches 100k objects. Monitor the output to confirm counts are growing. If the database already has data from a previous run, check counts first and only add what's needed.

## Step 4: Extract the SQL query

Get the actual SQL that the filter produces. There are two approaches — use whichever fits best:

### Approach A: From the filter function directly

Open a Django shell and call the filter function with representative input values, then print the query:

```python
from saleor.payment.models import TransactionItem
from saleor.graphql.payment.filters import filter_where_created_at_range

qs = TransactionItem.objects.all()
filtered = filter_where_created_at_range(qs, None, {"gte": "2025-01-01T00:00:00Z", "lte": "2025-06-01T00:00:00Z"})
print(str(filtered.query))
```

### Approach B: From a test with breakpoint

Add a `breakpoint()` right after the filter call in the filter function, run a test that hits it, then in the debugger:

```python
print(str(qs.query))
```

Use this approach when the filter input is complex (e.g., involves GraphQL variable resolution or multiple conditions).

### Approach C: Using `.explain()` directly

```python
print(qs.explain(analyze=True, verbose=True, buffers=True))
```

This runs EXPLAIN ANALYZE directly from Django without needing psql. Useful for a quick check, but the `data.sql` + `make explain` approach gives JSON output which is easier to analyze.

## Step 5: Analyze queries and generate report

Use the helper script at `.claude/skills/filter-benchmark/analyze_query.py`. It does everything in one call per queryset:
- Runs EXPLAIN ANALYZE with default planner settings
- Runs EXPLAIN ANALYZE with `enable_seqscan = OFF` to verify index availability
- Detects red flags (Seq Scans on large tables, row estimate mismatches, sorts, nested loops with inner seq scans)
- Saves JSON plans to `/tmp`
- Uploads plans to explain.dalibo.com for interactive visualization

Run in Django shell:

```python
import sys; sys.path.insert(0, ".claude/skills/filter-benchmark")
from analyze_query import analyze, report

# Analyze each queryset — prints quick summary + warnings inline
analyze(filtered_qs, "created_at range")
analyze(another_qs, "events by type")

# Print a full markdown report with Dalibo links
report()
```

Before analyzing, verify the querysets actually return rows. If EXPLAIN ANALYZE shows 0 rows, the filter input values don't match the generated data — adjust filter parameters (widen date range, use existing event types) and re-run.

The `report()` output includes a summary table and per-query details. Use it as the basis for the final report to the user, adding:

**1. Dataset size** — how many objects of each model, how field values are distributed

**2. Recommendations** — if there are warnings, suggest concrete fixes:
- Missing index: show the migration to add it (use `AddIndexConcurrently`)
- Suboptimal query: suggest ORM changes in the filter function
- Missing composite index: when filtering on multiple fields together

## Step 6: Wrap up

After presenting the report with Dalibo links, ask the user if they want to clean up the test data. If yes, delete the objects in reverse dependency order (child models first, then parents) to avoid foreign key violations. Use `.delete()` with filtering to target only the bulk-created data — for example, filter by the date range or other markers used during generation. Print counts of deleted objects for confirmation.
