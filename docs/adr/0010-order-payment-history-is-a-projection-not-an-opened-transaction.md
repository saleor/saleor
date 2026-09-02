# Order payment history is a projection, not an opened `TransactionItem`

**Tags:** payments, graphql, permissions, orders

Customer-facing payment history is a new `Order.transactionSummaries` field returning a
`TransactionSummary` projection of the existing `TransactionItem` rows, rather than a permission
change on `Order.transactions`.

Opening `Order.transactions` would publish the whole type — `externalUrl` (PSP back-office deep
link), `events` (internal ledger, staff identities, idempotency keys), `createdBy`, `name`,
`message` — and its `id`, which is the transaction `token`, a capability accepted by the
unauthenticated `transactionInitialize`/`transactionProcess` mutations. Allowlisting fields on the
existing type is not an option either: `PermissionsField` raises, and `[TransactionItem!]!` with
non-null fields means one denied field nulls the entire order. The projection is an allowlist, so
fields added to `TransactionItem` later cannot leak through it.

The field is meant to be queried by a storefront (account page, order summary) to show the money
that moved to and from the customer. That is why transactions with all amounts at zero are
filtered out: they are abandoned payment attempts, carry no information for the customer, and
would otherwise expose the brand and last digits of every card the buyer merely tried.
