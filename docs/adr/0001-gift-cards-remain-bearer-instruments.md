# Gift cards remain bearer instruments; customer assignment is a separate opt-in restriction

**Tags:** gift card, security, checkout

A gift card is a **bearer instrument** — whoever holds the code can spend it, including in guest checkout. This is the intended default: it was established when we deprecated `used_by` as a redemption lock in PR #13019 ("Allow to add a gift card to a checkout without email"), which removed the old rule that bound a card to the first customer who used it because it caused checkout friction. A card with no assignment behaves exactly as before.

Customer assignment is therefore an **opt-in restriction layered on top** of the bearer default, not a change to it. Enforcement only exists once staff explicitly restrict a card to a customer.

## Assignment is a new concept, separate from `used_by`

Assignment and "who used the card" are two different things, and keeping them apart is deliberate:

- **Assignment** is *forward-looking*: "this customer is **allowed** to spend this card." It is a restriction staff set on purpose.
- **`used_by`** is *historical*: "this is the last customer who **spent** the card." It is an audit record, updated on every use, and it is deprecated (since PR #13019).

Reusing `used_by` for assignment would conflate a restriction with an audit trail — two things that change at different times, for different reasons. So assignment gets its own dedicated field and is never derived from `used_by`.

## Enforcement must not leak who a card belongs to

Because a restriction ties a card to a specific account, enforcement must not become an **email/account enumeration oracle**: when a restricted card is rejected at checkout, the failure must be generic and must never reveal that the card is assigned, or to whom. Leaking that signal would let an attacker probe which emails a card is bound to. Restricted cards also cannot be used in guest checkout, since there is no account to match against.
