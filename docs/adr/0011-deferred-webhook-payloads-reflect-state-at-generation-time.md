# Deferred webhook payloads reflect state at generation time, not at trigger time

**Tags:** webhook, orders, checkout, concurrency

For the high-volume async events (orders, draft orders, fulfillments, checkouts, per-channel
stock and discounted-price changes) the subscription-webhook payload is not built in the request
that triggered the event. The request records only a pointer (the object's identity, the
requestor and the request time), creates `PENDING` deliveries with no payload, and enqueues a
background task. That task re-reads the object and resolves the subscription query against the
database as it is at that moment. Whether an event is deferred is a per-event flag in
`WebhookEventAsyncType.EVENT_MAP`.

The motivation is request latency. Resolving a subscription query for a large order means
running GraphQL resolvers, dataloaders and often sync webhook calls such as tax calculation, and
doing that once per subscribed app inside the mutation made the heaviest order and checkout
mutations noticeably slower. Moving it to a worker keeps the mutation's cost independent of how
many apps subscribe and how deep their queries are.

The accepted consequence is that an async webhook is a notification that something happened,
carrying the object's current state, not a snapshot of the state at the time it happened. If a
field was `A` when the mutation ran and `B` by the time the task runs, every pending delivery for
that object carries `B`. Two mutations in quick succession produce two deliveries that are
indistinguishable to the receiver. If the object is deleted before the task runs, the deliveries
are marked `FAILED` and no webhook is sent. Consumers that need the previous value must keep it
themselves. The snapshot alternative, serializing the payload in the request and storing it, is
exactly the cost the decision removes, so it was rejected rather than offered as an opt-in.

This applies to subscription webhooks only. Legacy webhooks without a subscription query still
serialize their payload inline and therefore do see the request-time state. The same event can
reach a legacy receiver with `A` and a subscription receiver with `B`.

The task reads from the read replica, and the replica may lag behind the write that created the
deliveries. Instead of reading from the writer, the task waits: it checks that the delivery rows
are visible on the replica and retries with backoff until they are, pinning the check and the
payload generation to a single replica connection so they see one snapshot. Reading from the
writer would move the full payload-generation load onto the primary, which is the database that
every pod shares and the scaling bottleneck.

## Per-webhook opt-out

Deferral is right by default but not for every consumer. An integration that applies each
`ORDER_METADATA_UPDATED` in sequence, expecting the metadata as written by each request, breaks
when several pending deliveries all carry the final state. Each webhook therefore carries a
`payloadGeneration` choice, `DEFERRED` by default or `IMMEDIATE`, set by the app that registers it
through the mutations or the manifest. An `IMMEDIATE` subscription webhook on a deferred event has
its payload built by whatever triggered the event, as every webhook did before deferral, and only
that webhook pays the cost. For events fired from a request that is the mutation's latency. For
events fired from a background task, such as the variant price and stock events, it is that task's
run time, which is why those events were deferred from the start. An app that sets `IMMEDIATE` on
such an event takes that cost knowingly. Because such a task may fire the event with a replica-allowed
manager right after its own write, an `IMMEDIATE` payload on a deferrable event is resolved against the
writer, so the dataloader-resolved fields cannot predate the write. Fields read from the subscribable
object itself still reflect where the caller loaded it from. The choice is ignored where it cannot apply: legacy
webhooks without a subscription query, sync events, and events that are not deferred.

## When each event became deferred

Deferral was rolled out event by event, so the version in which a consumer starts seeing
generation-time state depends on the event. Dates are merge dates on `main`. The release is the
first tagged version that ships the change.

| Event | Deferred since | Release | Change |
|---|---|---|---|
| `CHECKOUT_CREATED`, `CHECKOUT_UPDATED` | 2024-11-15 | 3.21.0 | Introduced the mechanism (#16999) |
| `ORDER_CREATED`, `ORDER_CONFIRMED`, `ORDER_PAID`, `ORDER_FULLY_PAID`, `ORDER_REFUNDED`, `ORDER_FULLY_REFUNDED`, `ORDER_UPDATED`, `ORDER_CANCELLED`, `ORDER_EXPIRED`, `ORDER_FULFILLED`, `ORDER_METADATA_UPDATED` | 2026-02-17 | 3.23.0 | Moved from inline to deferred (#18809) |
| `DRAFT_ORDER_CREATED`, `DRAFT_ORDER_UPDATED` | 2026-02-17 | 3.23.0 | Moved from inline to deferred (#18809) |
| `FULFILLMENT_CANCELED`, `FULFILLMENT_METADATA_UPDATED`, `FULFILLMENT_TRACKING_NUMBER_UPDATED` | 2026-02-17 | 3.23.0 | Moved from inline to deferred (#18809) |
| `PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED` | 2026-03-31 | 3.23.0, backported to 3.22.45 | New event, deferred from the start (#19004, #18973) |
| `PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL`, `PRODUCT_VARIANT_BACK_IN_STOCK_IN_CHANNEL`, `PRODUCT_VARIANT_OUT_OF_STOCK_FOR_CLICK_AND_COLLECT`, `PRODUCT_VARIANT_BACK_IN_STOCK_FOR_CLICK_AND_COLLECT` | 2026-04-21 | 3.23.2 | New events, deferred from the start (#19144) |

`FULFILLMENT_CREATED` and `FULFILLMENT_APPROVED` were flagged as deferred together with the other
order events on 2026-02-17 and reverted to inline on 2026-04-02 (#19012), before 3.23.0 was
released. Their subscribable object is a plain dict rather than a model or a registered dataclass,
so it cannot be reconstructed in the task. No released version delivers them deferred.

Everything not listed, including `ORDER_BULK_CREATED`, `DRAFT_ORDER_DELETED` and all events
outside orders, checkout and variant stock or price, still builds its payload inline and carries
request-time state.
