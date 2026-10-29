# Webhook identifier is an app-only pointer

**Tags:** webhook, app, graphql, permissions

`webhookUpdate` and `webhookDelete` accept `identifier` as an alternative to `id`, but only from
an app referencing its own webhook. Staff users must use `id`.

`Webhook.identifier` is unique per app, not globally, so it names a single webhook only once an
app scope is fixed, and the caller's own app is the only scope we accept. The pointer exists
because of an asymmetry in what each client knows: an app learns its identifiers from its own
manifest but never learns the global IDs Saleor assigns, so without it an app must list and match
its webhooks before mutating one. Staff have the inverse problem — the dashboard hands them global
IDs — so an identifier pointer buys them nothing.

The obvious extension is an `app` argument letting staff disambiguate. **Do not add it without
revisiting this decision.** It was considered and rejected: no known caller needs it, and it costs
four extra validation branches (`identifier` without `app`, `app` without `identifier`, `app`
contradicting `id`, an app naming someone else's `app`). Adding an optional argument later is
backward compatible, so nothing is foreclosed.
