# A restricted card stays restricted after its customer is deleted

**Tags:** gift card, security

When the customer a card is assigned to is deleted, the card must **not** silently become free for anyone to use again. We keep a trace of the assignment so the card stays restricted — effectively locked until staff explicitly reassign it to another customer.

The alternative (dropping the restriction on customer deletion) would quietly turn a deliberately-restricted card back into a bearer card, which is a security regression: a card meant for one account would become spendable by anyone. Retaining the trace makes "delete the customer" a safe operation that never widens who can spend the card.
