This folder contains graphQL layer

**Each mutation must have its own error class.
** Never reuse error classes between mutations.
Each mutation gets a dedicated error type so clients can handle errors specifically and new error codes can be added without affecting other mutations.

**Always tag new mutations and fields with `ADDED_IN_{VERSION}`.
** Check the latest git tag to determine the current version.
Every new type, field, mutation, and input must include the version annotation in its description so the API changelog is generated correctly.

**Limit input list sizes to a maximum of 100 per call (unless specified otherwise).
** Unbounded lists in mutation inputs can lead to OOM errors, timeouts, and expensive queries.
Apply the same limit pattern used in queries (max 100 items) and document the limit in the field description.

**Register query cost multipliers for limited/paginated fields.** When adding a new field with a `limit` argument, update `saleor/graphql/query_cost_map.py` so the `limit` value is used as a cost multiplier. This prevents expensive queries from bypassing rate limiting.


**Use `Meta.permissions` rather than manual permission checks in `perform_mutation`.
** The `BaseMutation.mutate` method already calls `check_permissions` using the permissions declared in `Meta`.
Adding manual permission checks in `perform_mutation` is redundant and can diverge from the declared permissions.

**Return the created or mutated object from mutations.
** Callers may need the created object's ID or fields immediately after the mutation. Always include the result object in the mutation response type.

**Use dataloader pattern when resolving fields**

**Regenerate graphql schema** when graphql types changes, run `python manage.py graphql_schema --schema saleor/graphql/schema.graphql` to regenerate schema

**Ensure you use existing scalars**

**Write exhausitve grahpql descirptions on fields, including limits and behavior**

# Input validation

For complex input shapes prefer using Pydantic model. Ensure Pydantic errors are mapped to Django ValidationError

# Adding new filter

- Create new DB index on django model for each filtered field (add index concurrently)

Example migration:

```python
import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations
class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        (“account”, “0095_repopulate_user_number_of_orders”),
    ]
    operations = [
        AddIndexConcurrently(
            model_name=“transactionitem”,
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=[“psp_reference”], name=“psp_reference_idx”
            ),
        ),
    ]
```
