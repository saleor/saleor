---
name: add-graphql-mutation
description: Add a new GraphQL mutation to the saleor backend. Use this whenever a task asks for a new operation in saleor's GraphQL schema (e.g. `pageDuplicate`, `productReorder`), so the implementation matches existing patterns for base class choice, permissions, error types, transactions, and event dispatch.
---

# Add a GraphQL mutation in saleor
This skill captures the pattern used across `saleor/graphql/*/mutations/`. Follow it unless you have a specific reason not to.
## 1 · Pick the base class
- Pure action on an existing object (no input payload, only an ID; e.g. duplicate, publish, reorder): subclass `BaseMutation` from `saleor.graphql.core.mutations`.
- Create a new row with an input object: subclass `DeprecatedModelMutation` (or the newer `ModelMutation` equivalent) \u2014 mirror `PageCreate` in `saleor/graphql/page/mutations/page_create.py`.
- Delete an existing row by ID: subclass `ModelDeleteMutation` (mirror `PageDelete`).
- Update an existing row: subclass the corresponding Create class (mirror `PageUpdate`).
Do not roll your own base class.
## 2 · Wire Meta correctly
```python path=null start=null
class Meta:
    description = "..."
    permissions = (PagePermissions.MANAGE_PAGES,)     # never omit; unauthenticated paths must 403
    error_type_class = PageError                       # use the app's error enum
    error_type_field = "page_errors"                   # deprecated alias kept for back-compat
```
`BaseMutation` auto-appends the permission message to `description`, and adds both `errors` and `<error_type_field>` fields to the payload.
## 3 · Arguments
Declare `class Arguments:` inside the mutation with typed `graphene` fields. For ID inputs use `graphene.ID(required=True, description=...)`. Use `cls.get_node_or_error(info, data["id"], only_type=<GrapheneType>)` to resolve \u2014 that also emits the standardized NOT_FOUND error.
## 4 · Do work under a traced atomic transaction
```python path=null start=null
from ....core.tracing import traced_atomic_transaction

with traced_atomic_transaction():
    # all DB writes here
```
Any multi-step write (create + associate attribute values, update + reindex, etc.) belongs in a single `traced_atomic_transaction` block.
## 5 · Dispatch events via `call_event`
```python path=null start=null
from ...plugins.dataloaders import get_plugin_manager_promise

manager = get_plugin_manager_promise(info.context).get()
cls.call_event(manager.page_created, new_page)        # or page_updated, page_deleted, ...
```
Never call `manager.<event>()` directly and never call `call_event` from inside the atomic block \u2014 events fire on commit.
## 6 · Return ChannelContext when the object type needs one
Look at the corresponding `*Create`/`*Update` classes. If they wrap the returned instance in `ChannelContext(instance, channel_slug=...)` inside `success_response`, you must too; otherwise the Graphene resolver raises at response time.
## 7 · Register the mutation
Three edits, always together:
1. The mutation file: `saleor/graphql/<app>/mutations/<name>.py`.
2. `saleor/graphql/<app>/mutations/__init__.py`: import the class and add it to `__all__`.
3. `saleor/graphql/<app>/schema.py`: inside the `<App>Mutations(graphene.ObjectType)` class, add `<snake_name> = YourMutation.Field()` alongside its siblings.
Miss any of the three and the mutation will not appear in introspection.
## 8 · Validate locally
- Reload the api+worker containers: `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart api worker` (or `make up` from `saleor-demo`).
- Introspect: `curl -s -X POST -H 'Content-Type: application/json' -d '{"query":"query{__type(name:\"Mutation\"){fields{name}}}"}' http://localhost:8000/graphql/ | grep <name>`.
- Call the mutation via curl with a JWT from `make api-token`.
- Update the dashboard: run `make refresh-schema` from `saleor-demo` before editing dashboard `mutations.ts`.
## Reference examples
- Stateless action: `saleor/graphql/page/mutations/page_duplicate.py`
- Create: `saleor/graphql/page/mutations/page_create.py`
- Delete: `saleor/graphql/page/mutations/page_delete.py`
- Update: `saleor/graphql/page/mutations/page_update.py`
