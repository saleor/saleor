# Gift card event — expose assignment on `GiftCardEvent`

## Problem

`giftCardAssignUser` / `giftCardUnassignUser` correctly emit `ASSIGNED_TO_USER` /
`UNASSIGNED_FROM_USER` events, storing the assignee data in `GiftCardEvent.parameters`:

- assign: `previous_assigned_to_id`, `previous_assigned_to_email`, `assigned_to_id`, `assigned_to_email`
- unassign: `previous_assigned_to_id`, `previous_assigned_to_email`

But the `GiftCardEvent` GraphQL type has **no field that surfaces these keys**. Clients see:

- `user` → the *staff actor* (`user=staff`, `MANAGE_USERS`/`MANAGE_STAFF`-gated), not the assigned customer.
- `email` → `parameters.get("email")`, a key assignment events never set → always `null`.
- `parameters` → not exposed at all.

So the assigned/previously-assigned customer is unreachable through the API. This is a
missing read surface, not a payload bug — the stored data is already correct.

## Solution

Purely additive read surface. No changes to the mutations or the stored event payload.

### New type — `GiftCardEventAssignment`

Sibling of `GiftCardEventBalance` in `saleor/graphql/giftcard/types.py`.

| Field | Type | Source (`parameters` key) |
|---|---|---|
| `oldAssignedTo` | `User` | `previous_assigned_to_id` (via `UserByUserIdLoader`) |
| `currentAssignedTo` | `User` | `assigned_to_id` (via `UserByUserIdLoader`) |
| `oldAssignedToEmail` | `String` | `previous_assigned_to_email` |
| `currentAssignedToEmail` | `String` | `assigned_to_email` |

The resolver root is the `GiftCardEvent` model itself, so sub-resolvers read `root.parameters`.

### New field on `GiftCardEvent`

`assignedTo: GiftCardEventAssignment` (`ADDED_IN_323`). `resolve_assigned_to` returns the
event (as assignment root) only for `ASSIGNED_TO_USER` / `UNASSIGNED_FROM_USER`, else `null`
— same guard style as `resolve_balance`.

### Behavior per event type

The `old`/`current` shape unifies both events:

- **`ASSIGNED_TO_USER`** — `old*` = previous assignee (null on first assign), `current*` = new assignee.
- **`UNASSIGNED_FROM_USER`** — `old*` = who it was unassigned from, `current*` = null (params store only `previous_*`).

### Deleted-customer case

`assigned_to` FK is `SET_NULL`, but the denormalized email persists in `parameters`. After the
customer is deleted, `currentAssignedTo`/`oldAssignedTo` (User) resolve to `null` while the
`*Email` fields still return the recorded email — the email is the durable audit value.

### Permissions

- The whole `events` list is already gated behind `MANAGE_GIFT_CARD`; assignment events sit in
  the staff-only bucket (never owner-visible).
- **`User` sub-fields** — gated on `MANAGE_USERS` / `MANAGE_STAFF` / owner, mirroring the existing
  `resolve_user` (event actor) and `GiftCard.assignedTo`. The check runs **only when there is a
  non-null assignee id** — a null id returns `null` without a permission check (so unassign /
  first-assign / deleted-customer cases don't raise a spurious `PermissionDenied`).
- **email sub-fields** — returned plain, resolvable without `MANAGE_USERS`. They are already
  behind the `MANAGE_GIFT_CARD` events gate and are the denormalized audit record.

## Testing

- `test_gift_card_assign_user.py` — mutation query selects `events { type assignedTo { ... } }`
  and asserts the emitted `ASSIGNED_TO_USER` event surfaces the assignee (and, for reassign, the
  previous assignee) through the API; a dedicated test asserts the `User` sub-fields are denied
  for a `MANAGE_GIFT_CARD`-only requester while the `*Email` fields still resolve.
- `test_gift_card_unassign_user.py` — asserts `UNASSIGNED_FROM_USER` exposes `old*` = previous
  assignee, `current*` = `null`.

## Out of scope

- No changes to mutations, event helpers, or stored payload.
- No `parameters` raw-JSON field.
- No obfuscation on the email fields.
