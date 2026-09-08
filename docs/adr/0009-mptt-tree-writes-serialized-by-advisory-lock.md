# MPTT structural tree writes are serialized by an advisory lock

**Tags:** category, menu, concurrency

Categories and menu items store their hierarchy as django-mptt nested sets, where every structural write — inserting, deleting or re-parenting a node, or rebuilding a tree — renumbers interval fields across the whole tree with multi-statement read-then-shift queries, and creating a new root allocates the next tree id by reading the current maximum. Both are textbook TOCTOU shapes: two concurrent writers interleave their reads and shifts and silently corrupt the tree, which surfaces as products leaking between sibling categories and categories reporting false ancestors. django-mptt is not concurrency-safe by design and [documents](https://django-mptt.readthedocs.io/en/latest/technical_details.html#concurrency) that callers must provide their own locking around tree operations.

Row locks cannot provide that: the rows a write renumbers extend far beyond the rows it names, and a brand-new root has **no row to lock at all**. Every structural MPTT write must therefore hold the model's global, transaction-scoped Postgres advisory lock for the duration of the write. One global lock per model costs nothing in practice — structural tree writes are rare admin operations, and reads are unaffected.

Rules that keep this safe:

- Only transaction-scoped advisory locks may be used — they release automatically on commit/rollback and stay correct under pgbouncer transaction pooling. Session-scoped advisory locks are forbidden.
- Lock keys form a permanent registry: never reuse or renumber a key, and never change the namespace — a key identifies a lock across all deployed code versions.
- The advisory lock is taken before any row locks in the same transaction, so there is one consistent lock ordering and no new deadlock risk.
- The parent reference is the source of truth for the hierarchy; the nested-set fields are derived, rebuildable data. Corruption is repaired by rebuilding the affected trees from the parent references, itself done under the lock.
- The lock only protects writers that take it: any new code path that re-parents a node, deletes a node instance, or writes the interval fields directly must participate.
- Queryset and cascade deletes are exempt — they bypass the per-instance delete and perform no renumbering. Whole subtrees are removed together, leaving only benign number gaps.
- Holding the lock is not enough when the write is computed from data read before it was taken — mptt computes moves from in-memory instance values. Whatever a write's math depends on must be read, or refreshed, after acquiring the lock.
