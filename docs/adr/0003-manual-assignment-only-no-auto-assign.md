# Assignment is manual-only; no auto-assign-on-use

**Tags:** gift card

Cards are assigned **only** by explicit staff action. We considered, then cut, an "automatically assign the card to whoever pays with it" lifecycle (auto-assign on payment, make it permanent when the order completes, revert if the checkout is abandoned).

It was cut because it is the same auto-locking behavior Saleor already built and deliberately removed in PR #13019 — binding a card to the customer who used it caused enough checkout friction to be torn out. A narrower, reversible version would reintroduce that same class of behavior plus significant complexity (distinguishing automatic from manual assignment so cleanup never clobbers a staff decision, promotion on order completion, reversal on abandonment) for benefit that did not justify it. Keeping assignment manual leaves one concept, one rule, and no hidden lifecycle.
