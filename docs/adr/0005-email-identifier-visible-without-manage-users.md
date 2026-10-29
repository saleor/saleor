# Denormalized email identifiers are visible without MANAGE_USERS

**Tags:** gift card, security, permissions

Staff who can manage gift cards (`MANAGE_GIFT_CARD`) can read the **denormalized email** of the user a card is assigned to (as well as the created-by / used-by emails), even if they do **not** hold `MANAGE_USERS`. Access to the full **`User` object** is stricter: it requires `MANAGE_USERS` (via `resolve_assigned_to`).

The reasoning is that the email is a low-sensitivity identifier that lets an operator reason about who is performing operations or who a card belongs to — needed to do the gift-card job at all. The full user entity exposes much more (profile, addresses, order history, metadata) and is genuinely account-management scope, so it stays behind `MANAGE_USERS`. `MANAGE_GIFT_CARD` on the email resolvers still ensures that someone who cannot manage gift cards sees nothing at all (unauthorized requestors get the obfuscated email). This mirrors the decision made for refund reasons.

This is a deliberate choice, not accidental broken access control. It is documented both here and inline at the resolver so future readers do not "fix" the email resolver to require `MANAGE_USERS` and break the intended workflow.
