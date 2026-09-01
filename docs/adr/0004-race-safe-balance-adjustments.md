# Balance adjustments must be race-safe and free of TOCTOU issues

**Tags:** gift card, concurrency

Changing a gift card's balance is money movement that can happen concurrently — a staff adjustment and a checkout charge can hit the same card at the same time. Any balance operation must therefore be **atomic** and free of time-of-check-to-time-of-use (TOCTOU) races: never read a balance, decide, and write it back as separate steps, because a concurrent operation can invalidate the decision in between and silently lose an update or overspend the card.

Practically, this means balance changes are expressed as a single atomic operation (an adjustment applied directly at the database level, self-clamping so a card can never go negative) rather than a read-modify-write in application code. Because this cannot be done safely through the ordinary "load, edit fields, save" update path, balance adjustment is a dedicated operation rather than another editable field on the general gift-card update. This rule applies to any future balance-changing operation, not just the current one.
