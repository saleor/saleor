# Gift Card Balance Delta & Customer Assignment — PRD + Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add (1) an atomic, race-safe `giftCardBalanceAdjust` mutation that changes a card's balance by a signed delta, and (2) an opt-in customer restriction on gift cards (`assigned_to`) with staff assign/unassign mutations and checkout-time enforcement.

**Architecture:** Feature 1 is a dedicated `BaseMutation` doing a row-locked read-modify-write on `current_balance_amount` (clamp-to-zero on over-deduction, bump `initial_balance` only when a top-up exceeds it), emitting a new gated `BALANCE_ADJUSTED` event. Feature 2 adds two nullable columns (`assigned_to` FK + `assigned_to_email`), staff-only `giftCardAssignUser`/`giftCardUnassignUser` mutations guarded against reassigning in-play cards, plus optional assignment at create; enforcement is a hard gate at `checkoutAddPromoCode` and `checkoutComplete`; reads expose `assignedTo`/`assignedToEmail`, extend owner semantics (code + `me.giftCards`), and add a staff `assignedTo` filter.

**Tech Stack:** Django 5, graphene GraphQL, PostgreSQL, pytest. Saleor Core monorepo.

## Global Constraints

- Target branch `origin/3.23`; PRs `--base 3.23`. Annotate every new type/field/mutation/input with `ADDED_IN_323` (macro exists in `saleor/graphql/core/descriptions.py:18`).
- Each mutation gets its **own dedicated error class** (graphql/CLAUDE.md). Reuse `GiftCardError`/`GiftCardErrorCode` for the giftcard-domain mutations here (they already share it across all giftcard mutations); do **not** invent a checkout error code.
- New filter field ⇒ new DB index added `CONCURRENTLY` (`atomic = False` migration).
- Use `call_event` from `saleor.core.utils.events` for manager webhook dispatch, never call the manager method directly.
- Use `traced_atomic_transaction` + `select_for_update` (via a `lock_objects` module) for read-modify-write.
- Tests: given/when/then, flat (no classes), `--reuse-db`, assert error **length + code via enum name** (`error["code"] == GiftCardErrorCode.X.name`), reuse fixtures.
- Run tests inside the worktree container: `.worktree-container/compose.sh exec saleor pytest --reuse-db <path>`.
- After any GraphQL type change: `python manage.py graphql_schema --schema saleor/graphql/schema.graphql`.
- Do **not** touch/read `used_by`/`used_by_email` for new behavior — deprecated, removal in 4.0.

---

## File Structure

**Feature 1 — balance adjust**
- Modify `saleor/giftcard/__init__.py` — add `BALANCE_ADJUSTED` event constant + choice.
- Modify `saleor/giftcard/events.py` — add `gift_card_balance_adjusted_event`.
- Create `saleor/giftcard/lock_objects.py` — `gift_card_qs_select_for_update`.
- Create `saleor/graphql/giftcard/mutations/gift_card_balance_adjust.py` — `GiftCardBalanceAdjust`.
- Modify `saleor/graphql/giftcard/mutations/__init__.py` + `saleor/graphql/giftcard/schema.py` — register.
- Create `saleor/graphql/giftcard/tests/mutations/test_gift_card_balance_adjust.py`.

**Feature 2 — customer assignment**
- Modify `saleor/giftcard/models.py` — `assigned_to` FK + `assigned_to_email`.
- Create `saleor/giftcard/migrations/00NN_giftcard_assigned_to.py` (AddField) + `00NN+1_giftcard_assigned_to_index.py` (AddIndexConcurrently).
- Modify `saleor/giftcard/__init__.py` — `ASSIGNED_TO_USER` / `UNASSIGNED_FROM_USER`.
- Modify `saleor/giftcard/events.py` — assign/unassign event helpers.
- Modify `saleor/giftcard/error_codes.py` — `CANNOT_ASSIGN`.
- Modify `saleor/giftcard/utils.py` — assign helper (guard) + checkout-add enforcement.
- Modify `saleor/checkout/checkout_cleaner.py` — checkout-complete enforcement.
- Create `saleor/graphql/giftcard/mutations/gift_card_assign_user.py`, `gift_card_unassign_user.py`.
- Modify `saleor/graphql/giftcard/mutations/gift_card_create.py` — optional `assignedTo`.
- Modify `saleor/graphql/giftcard/types.py` — `assignedTo`/`assignedToEmail` fields + resolvers + `resolve_code` owner extension.
- Modify `saleor/graphql/giftcard/dataloaders.py` — `GiftCardsByUserLoader` union.
- Modify `saleor/graphql/giftcard/filters.py` — `assignedTo` filter.
- Tests alongside each.

---

# FEATURE 1 — `giftCardBalanceAdjust`

### Task 1: `BALANCE_ADJUSTED` event type + helper

**Files:**
- Modify: `saleor/giftcard/__init__.py:9-40`
- Modify: `saleor/giftcard/events.py`
- Test: `saleor/giftcard/tests/test_events.py`

**Interfaces:**
- Produces: `GiftCardEvents.BALANCE_ADJUSTED = "balance_adjusted"`; `events.gift_card_balance_adjusted_event(gift_card, old_current_balance: Decimal, old_initial_balance: Decimal, user, app) -> GiftCardEvent`.

- [ ] **Step 1: Write the failing test**

```python
# saleor/giftcard/tests/test_events.py
from decimal import Decimal
from .. import GiftCardEvents
from ..events import gift_card_balance_adjusted_event


def test_gift_card_balance_adjusted_event(gift_card, staff_user):
    # given
    old_current = Decimal("50.00")
    old_initial = Decimal("100.00")

    # when
    event = gift_card_balance_adjusted_event(
        gift_card, old_current, old_initial, staff_user, None
    )

    # then
    assert event.type == GiftCardEvents.BALANCE_ADJUSTED
    balance = event.parameters["balance"]
    assert balance["old_current_balance"] == old_current
    assert balance["old_initial_balance"] == old_initial
    assert balance["current_balance"] == gift_card.current_balance_amount
    assert balance["initial_balance"] == gift_card.initial_balance_amount
    assert balance["currency"] == gift_card.currency
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_events.py::test_gift_card_balance_adjusted_event -v`
Expected: FAIL — `ImportError` / `AttributeError: BALANCE_ADJUSTED`.

- [ ] **Step 3: Add the event constant and choice**

In `saleor/giftcard/__init__.py`, add constant after `REFUNDED_IN_ORDER = "refunded_in_order"`:
```python
    BALANCE_ADJUSTED = "balance_adjusted"
```
And add to `CHOICES` list (after the `REFUNDED_IN_ORDER` tuple):
```python
        (BALANCE_ADJUSTED, "The gift card balance was adjusted by a delta."),
```

- [ ] **Step 4: Add the event helper**

In `saleor/giftcard/events.py` (Decimal already imported at top):
```python
def gift_card_balance_adjusted_event(
    gift_card: GiftCard,
    old_current_balance: Decimal,
    old_initial_balance: Decimal,
    user: User | None,
    app: App | None,
) -> GiftCardEvent:
    balance_data = {
        "currency": gift_card.currency,
        "current_balance": gift_card.current_balance_amount,
        "initial_balance": gift_card.initial_balance_amount,
        "old_current_balance": old_current_balance,
        "old_initial_balance": old_initial_balance,
    }
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.BALANCE_ADJUSTED,
        parameters={"balance": balance_data},
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_events.py::test_gift_card_balance_adjusted_event -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add saleor/giftcard/__init__.py saleor/giftcard/events.py saleor/giftcard/tests/test_events.py
git commit -m "feat(giftcard): add BALANCE_ADJUSTED event"
```

---

### Task 2: gift card row-lock helper

**Files:**
- Create: `saleor/giftcard/lock_objects.py`
- Test: `saleor/giftcard/tests/test_lock_objects.py`

**Interfaces:**
- Produces: `gift_card_qs_select_for_update() -> QuerySet[GiftCard]`.

- [ ] **Step 1: Write the failing test**

```python
# saleor/giftcard/tests/test_lock_objects.py
from ..lock_objects import gift_card_qs_select_for_update
from ..models import GiftCard


def test_gift_card_qs_select_for_update_returns_giftcard_queryset(gift_card):
    # when
    qs = gift_card_qs_select_for_update()

    # then
    assert qs.model is GiftCard
    assert qs.query.select_for_update is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_lock_objects.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Create the module**

```python
# saleor/giftcard/lock_objects.py
from django.db.models import QuerySet

from .models import GiftCard


def gift_card_qs_select_for_update() -> QuerySet[GiftCard]:
    return GiftCard.objects.order_by("pk").select_for_update(of=["self"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_lock_objects.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add saleor/giftcard/lock_objects.py saleor/giftcard/tests/test_lock_objects.py
git commit -m "feat(giftcard): add gift card select_for_update lock helper"
```

---

### Task 3: `GiftCardBalanceAdjust` mutation

**Files:**
- Create: `saleor/graphql/giftcard/mutations/gift_card_balance_adjust.py`
- Modify: `saleor/graphql/giftcard/mutations/__init__.py`
- Modify: `saleor/graphql/giftcard/schema.py:137-150`
- Test: `saleor/graphql/giftcard/tests/mutations/test_gift_card_balance_adjust.py`
- Regenerate: `saleor/graphql/schema.graphql`

**Interfaces:**
- Consumes: `gift_card_qs_select_for_update` (Task 2), `gift_card_balance_adjusted_event` (Task 1).
- Produces: mutation `giftCardBalanceAdjust(id: ID!, amount: Decimal!) -> { giftCard, errors }`.

**Semantics (verbatim rules):** `amount != 0` (else `INVALID`), currency-precision-valid on `abs(amount)` (else `INVALID`). Under row lock: `new_current = old_current + amount`; if `new_current < 0` clamp to `0`. Set `current_balance_amount = new_current`; if `new_current > old_initial` also set `initial_balance_amount = new_current`. Read exact old/new for the event. Allowed regardless of `is_active`/expiry. Emit `GIFT_CARD_UPDATED` via `call_event`. Event is `MANAGE_GIFT_CARD`-gated automatically (giftcard events resolver already hides non-USED/REFUNDED types).

- [ ] **Step 1: Write the failing tests**

```python
# saleor/graphql/giftcard/tests/mutations/test_gift_card_balance_adjust.py
from decimal import Decimal

import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation GiftCardBalanceAdjust($id: ID!, $amount: Decimal!) {
        giftCardBalanceAdjust(id: $id, amount: $amount) {
            giftCard {
                id
                currentBalance { amount }
                initialBalance { amount }
            }
            errors { field code message }
        }
    }
"""


def _adjust(api_client, gift_card, amount, permissions=None):
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "amount": str(amount),
    }
    kwargs = {"permissions": permissions} if permissions is not None else {}
    response = api_client.post_graphql(MUTATION, variables, **kwargs)
    return response


def test_increase_balance(staff_api_client, gift_card, permission_manage_gift_card):
    # given
    gift_card.current_balance_amount = Decimal("50.00")
    gift_card.initial_balance_amount = Decimal("100.00")
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal("20.00"), [permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardBalanceAdjust"]
    assert data["errors"] == []
    assert data["giftCard"]["currentBalance"]["amount"] == 70.0
    assert data["giftCard"]["initialBalance"]["amount"] == 100.0
    gift_card.refresh_from_db()
    assert gift_card.current_balance_amount == Decimal("70.00")
    assert gift_card.events.filter(type=GiftCardEvents.BALANCE_ADJUSTED).count() == 1


def test_increase_above_initial_bumps_initial(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.current_balance_amount = Decimal("90.00")
    gift_card.initial_balance_amount = Decimal("100.00")
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal("30.00"), [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBalanceAdjust"]
    assert data["giftCard"]["currentBalance"]["amount"] == 120.0
    assert data["giftCard"]["initialBalance"]["amount"] == 120.0


def test_decrease_clamps_to_zero(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.current_balance_amount = Decimal("10.00")
    gift_card.initial_balance_amount = Decimal("100.00")
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal("-25.00"), [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBalanceAdjust"]
    assert data["giftCard"]["currentBalance"]["amount"] == 0.0
    assert data["giftCard"]["initialBalance"]["amount"] == 100.0


def test_zero_amount_is_rejected(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal("0"), [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBalanceAdjust"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "amount"
    assert data["errors"][0]["code"] == GiftCardErrorCode.INVALID.name


def test_requires_permission(staff_api_client, gift_card):
    # when
    response = _adjust(staff_api_client, gift_card, Decimal("10.00"))

    # then
    assert_no_permission(response)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/mutations/test_gift_card_balance_adjust.py -v`
Expected: FAIL — mutation field `giftCardBalanceAdjust` does not exist.

- [ ] **Step 3: Implement the mutation**

```python
# saleor/graphql/giftcard/mutations/gift_card_balance_adjust.py
from decimal import Decimal

import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....giftcard import events, models
from ....giftcard.error_codes import GiftCardErrorCode
from ....giftcard.lock_objects import gift_card_qs_select_for_update
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal as DecimalScalar
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardBalanceAdjust(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="The adjusted gift card.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the gift card to adjust.")
        amount = DecimalScalar(
            required=True,
            description=(
                "Signed amount to adjust the current balance by. Positive tops up, "
                "negative deducts. A deduction below zero clamps the balance to zero. "
                "A top-up above the initial balance raises the initial balance to the "
                "new current balance. " + ADDED_IN_323
            ),
        )

    class Meta:
        description = (
            "Adjust a gift card's balance by a signed delta atomically. " + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_UPDATED,
                description="A gift card was updated.",
            )
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, id, amount):
        gift_card = cls.get_node_or_error(info, id, only_type=GiftCard, field="id")

        if amount == Decimal(0):
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Adjustment amount cannot be zero.",
                        code=GiftCardErrorCode.INVALID.value,
                    )
                }
            )
        try:
            validate_price_precision(abs(amount), gift_card.currency)
        except ValidationError as e:
            e.code = GiftCardErrorCode.INVALID.value
            raise ValidationError({"amount": e}) from e

        user = info.context.user
        app = get_app_promise(info.context).get()

        with traced_atomic_transaction():
            locked = gift_card_qs_select_for_update().get(pk=gift_card.pk)
            old_current = locked.current_balance_amount
            old_initial = locked.initial_balance_amount

            new_current = old_current + amount
            if new_current < Decimal(0):
                new_current = Decimal(0)
            locked.current_balance_amount = new_current
            update_fields = ["current_balance_amount"]
            if new_current > old_initial:
                locked.initial_balance_amount = new_current
                update_fields.append("initial_balance_amount")
            locked.save(update_fields=update_fields)

            events.gift_card_balance_adjusted_event(
                locked, old_current, old_initial, user, app
            )

        manager = get_plugin_manager_promise(info.context).get()
        call_event(manager.gift_card_updated, locked)

        return cls(gift_card=locked, errors=[])
```

> **Verify before running:** confirm `saleor/graphql/core/scalars.py` exports a `Decimal` scalar. If it does not, replace the `DecimalScalar` import with `graphene.Decimal` and use `graphene.Decimal(...)` in `Arguments`.

- [ ] **Step 4: Register the mutation**

In `saleor/graphql/giftcard/mutations/__init__.py` add the export (match existing style):
```python
from .gift_card_balance_adjust import GiftCardBalanceAdjust
```
(and add `"GiftCardBalanceAdjust"` to `__all__` if present.)

In `saleor/graphql/giftcard/schema.py`, import it alongside the other mutation imports and add inside `GiftCardMutations`:
```python
    gift_card_balance_adjust = GiftCardBalanceAdjust.Field()
```

- [ ] **Step 5: Regenerate schema and run tests**

Run:
```
.worktree-container/compose.sh exec saleor python manage.py graphql_schema --schema saleor/graphql/schema.graphql
.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/mutations/test_gift_card_balance_adjust.py -v
```
Expected: PASS (all 5 tests).

- [ ] **Step 6: Commit**

```bash
git add saleor/graphql/giftcard/mutations/gift_card_balance_adjust.py \
        saleor/graphql/giftcard/mutations/__init__.py \
        saleor/graphql/giftcard/schema.py saleor/graphql/schema.graphql \
        saleor/graphql/giftcard/tests/mutations/test_gift_card_balance_adjust.py
git commit -m "feat(giftcard): add giftCardBalanceAdjust mutation"
```

---

# FEATURE 2 — Customer assignment

### Task 4: Model fields `assigned_to` + `assigned_to_email` (+ index)

**Files:**
- Modify: `saleor/giftcard/models.py` (after `used_by_email`, ~line 65)
- Create: `saleor/giftcard/migrations/00NN_giftcard_assigned_to.py` (AddField, atomic)
- Create: `saleor/giftcard/migrations/00NN+1_giftcard_assigned_to_idx.py` (AddIndexConcurrently, `atomic = False`)
- Test: `saleor/giftcard/tests/test_models.py`

**Interfaces:**
- Produces: `GiftCard.assigned_to` (FK User, null, SET_NULL, related_name `assigned_gift_cards`), `GiftCard.assigned_to_email` (EmailField null/blank), index `giftcard_assigned_to_idx` on `assigned_to`.

- [ ] **Step 1: Write the failing test**

```python
# saleor/giftcard/tests/test_models.py
from ..models import GiftCard


def test_gift_card_can_be_assigned_to_customer(gift_card, customer_user):
    # when
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

    # then
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email
    assert gift_card in GiftCard.objects.filter(assigned_to=customer_user)
    assert customer_user.assigned_gift_cards.filter(pk=gift_card.pk).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_models.py::test_gift_card_can_be_assigned_to_customer -v`
Expected: FAIL — `assigned_to` field/attr does not exist.

- [ ] **Step 3: Add the fields**

In `saleor/giftcard/models.py`, after `used_by_email = models.EmailField(null=True, blank=True)`:
```python
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="assigned_gift_cards",
    )
    assigned_to_email = models.EmailField(null=True, blank=True)
```

- [ ] **Step 4: Generate the AddField migration**

Run: `.worktree-container/compose.sh exec saleor python manage.py makemigrations giftcard`
Expected: creates `00NN_giftcard_assigned_to*.py` with `AddField` for `assigned_to` and `assigned_to_email`. Rename to `00NN_giftcard_assigned_to.py`.

- [ ] **Step 5: Add the concurrent index migration**

Create `saleor/giftcard/migrations/00NN+1_giftcard_assigned_to_idx.py`:
```python
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("giftcard", "00NN_giftcard_assigned_to"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="giftcard",
            index=models.Index(
                fields=["assigned_to"], name="giftcard_assigned_to_idx"
            ),
        ),
    ]
```

- [ ] **Step 6: Migrate and run the test**

Run:
```
.worktree-container/compose.sh exec saleor python manage.py migrate giftcard
.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_models.py::test_gift_card_can_be_assigned_to_customer -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add saleor/giftcard/models.py saleor/giftcard/migrations/ saleor/giftcard/tests/test_models.py
git commit -m "feat(giftcard): add assigned_to customer relation to gift card"
```

---

### Task 5: assign/unassign event types + helpers

**Files:**
- Modify: `saleor/giftcard/__init__.py`
- Modify: `saleor/giftcard/events.py`
- Test: `saleor/giftcard/tests/test_events.py`

**Interfaces:**
- Produces: `GiftCardEvents.ASSIGNED_TO_USER = "assigned_to_user"`, `GiftCardEvents.UNASSIGNED_FROM_USER = "unassigned_from_user"`; `events.gift_card_assigned_event(gift_card, previous_user_id, previous_email, user, app)`, `events.gift_card_unassigned_event(gift_card, previous_user_id, previous_email, user, app)`.

- [ ] **Step 1: Write the failing test**

```python
# append to saleor/giftcard/tests/test_events.py
from ..events import gift_card_assigned_event, gift_card_unassigned_event


def test_gift_card_assigned_event_records_prev_and_new(
    gift_card, customer_user, staff_user
):
    # given
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email

    # when
    event = gift_card_assigned_event(gift_card, None, None, staff_user, None)

    # then
    assert event.type == GiftCardEvents.ASSIGNED_TO_USER
    assert event.parameters["previous_assigned_to_id"] is None
    assert event.parameters["previous_assigned_to_email"] is None
    assert event.parameters["assigned_to_id"] == customer_user.id
    assert event.parameters["assigned_to_email"] == customer_user.email


def test_gift_card_unassigned_event_records_prev(gift_card, customer_user, staff_user):
    # when
    event = gift_card_unassigned_event(
        gift_card, customer_user.id, customer_user.email, staff_user, None
    )

    # then
    assert event.type == GiftCardEvents.UNASSIGNED_FROM_USER
    assert event.parameters["previous_assigned_to_id"] == customer_user.id
    assert event.parameters["previous_assigned_to_email"] == customer_user.email
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_events.py -k "assigned" -v`
Expected: FAIL — attrs/functions missing.

- [ ] **Step 3: Add constants + choices**

In `saleor/giftcard/__init__.py`:
```python
    ASSIGNED_TO_USER = "assigned_to_user"
    UNASSIGNED_FROM_USER = "unassigned_from_user"
```
CHOICES additions:
```python
        (ASSIGNED_TO_USER, "The gift card was assigned to a customer."),
        (UNASSIGNED_FROM_USER, "The gift card was unassigned from a customer."),
```

- [ ] **Step 4: Add event helpers**

In `saleor/giftcard/events.py`:
```python
def gift_card_assigned_event(
    gift_card: GiftCard,
    previous_user_id: int | None,
    previous_email: str | None,
    user: User | None,
    app: App | None,
) -> GiftCardEvent:
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.ASSIGNED_TO_USER,
        parameters={
            "previous_assigned_to_id": previous_user_id,
            "previous_assigned_to_email": previous_email,
            "assigned_to_id": gift_card.assigned_to_id,
            "assigned_to_email": gift_card.assigned_to_email,
        },
    )


def gift_card_unassigned_event(
    gift_card: GiftCard,
    previous_user_id: int | None,
    previous_email: str | None,
    user: User | None,
    app: App | None,
) -> GiftCardEvent:
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.UNASSIGNED_FROM_USER,
        parameters={
            "previous_assigned_to_id": previous_user_id,
            "previous_assigned_to_email": previous_email,
        },
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_events.py -k "assigned" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add saleor/giftcard/__init__.py saleor/giftcard/events.py saleor/giftcard/tests/test_events.py
git commit -m "feat(giftcard): add assign/unassign gift card events"
```

---

### Task 6: `CANNOT_ASSIGN` error code + assign domain helper (guard)

**Files:**
- Modify: `saleor/giftcard/error_codes.py`
- Modify: `saleor/giftcard/utils.py`
- Test: `saleor/giftcard/tests/test_utils.py`

**Interfaces:**
- Produces: `GiftCardErrorCode.CANNOT_ASSIGN = "cannot_assign"`; `utils.assign_gift_card_to_user(gift_card, user) -> None` (row-locked; raises `GiftCardCannotAssign` if used-in-order or attached to a paid checkout; auto-detaches clean checkouts; sets `assigned_to`/`assigned_to_email`, saves).
- Define exception `class GiftCardCannotAssign(Exception)` in `saleor/giftcard/utils.py` (mapped to `CANNOT_ASSIGN` by the mutation in Task 7).

**Guard rules (verbatim):** `last_used_on is not None` → raise. Any attached checkout with `payments.filter(is_active=True).exists()` OR `payment_transactions.exists()` → raise. Otherwise detach the card from every attached checkout via `.gift_cards.remove()` + `save(update_fields=["last_change"])` (this is the same invalidation `checkoutRemovePromoCode` performs), then set assignment.

- [ ] **Step 1: Write the failing tests**

```python
# saleor/giftcard/tests/test_utils.py
import pytest

from ..models import GiftCard
from ..utils import GiftCardCannotAssign, assign_gift_card_to_user


def test_assign_sets_user_and_email(gift_card, customer_user):
    # when
    assign_gift_card_to_user(gift_card, customer_user)

    # then
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email


def test_assign_blocked_when_used_in_order(gift_card, customer_user):
    # given
    from django.utils import timezone

    gift_card.last_used_on = timezone.now()
    gift_card.save(update_fields=["last_used_on"])

    # when / then
    with pytest.raises(GiftCardCannotAssign):
        assign_gift_card_to_user(gift_card, customer_user)


def test_assign_detaches_clean_checkout(gift_card, customer_user, checkout):
    # given
    checkout.gift_cards.add(gift_card)

    # when
    assign_gift_card_to_user(gift_card, customer_user)

    # then
    assert not checkout.gift_cards.filter(pk=gift_card.pk).exists()
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user


def test_assign_blocked_when_checkout_has_transaction(
    gift_card, customer_user, checkout, transaction_item_generator
):
    # given
    checkout.gift_cards.add(gift_card)
    transaction_item_generator(checkout_id=checkout.pk)

    # when / then
    with pytest.raises(GiftCardCannotAssign):
        assign_gift_card_to_user(gift_card, customer_user)
    assert checkout.gift_cards.filter(pk=gift_card.pk).exists()
```

> Confirm the `transaction_item_generator` fixture accepts `checkout_id`; if not, create a `TransactionItem` bound to `checkout` directly in the test.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_utils.py -k assign -v`
Expected: FAIL — import errors.

- [ ] **Step 3: Add the error code**

In `saleor/giftcard/error_codes.py` add to the enum:
```python
    CANNOT_ASSIGN = "cannot_assign"
```

- [ ] **Step 4: Implement the helper**

In `saleor/giftcard/utils.py` (add imports for `traced_atomic_transaction`, `gift_card_qs_select_for_update`, `User` typing):
```python
class GiftCardCannotAssign(Exception):
    """Raised when a gift card cannot be (re)assigned to a customer."""


def assign_gift_card_to_user(gift_card: "GiftCard", user: "User") -> None:
    from ..core.tracing import traced_atomic_transaction
    from .lock_objects import gift_card_qs_select_for_update

    with traced_atomic_transaction():
        locked = gift_card_qs_select_for_update().get(pk=gift_card.pk)

        if locked.last_used_on is not None:
            raise GiftCardCannotAssign(
                "Cannot assign a gift card that was already used in an order."
            )

        attached_checkouts = list(locked.checkouts.all())
        for checkout in attached_checkouts:
            has_transactions = (
                checkout.payments.filter(is_active=True).exists()
                or checkout.payment_transactions.exists()
            )
            if has_transactions:
                raise GiftCardCannotAssign(
                    "Cannot assign a gift card attached to a checkout with payments."
                )
        for checkout in attached_checkouts:
            checkout.gift_cards.remove(locked)
            checkout.save(update_fields=["last_change"])

        locked.assigned_to = user
        locked.assigned_to_email = user.email
        locked.save(update_fields=["assigned_to", "assigned_to_email"])

        gift_card.assigned_to = user
        gift_card.assigned_to_email = user.email
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_utils.py -k assign -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add saleor/giftcard/error_codes.py saleor/giftcard/utils.py saleor/giftcard/tests/test_utils.py
git commit -m "feat(giftcard): add assign-to-user helper with reassign guard"
```

---

### Task 7: `giftCardAssignUser` mutation

**Files:**
- Create: `saleor/graphql/giftcard/mutations/gift_card_assign_user.py`
- Modify: `saleor/graphql/giftcard/mutations/__init__.py`, `saleor/graphql/giftcard/schema.py`
- Test: `saleor/graphql/giftcard/tests/mutations/test_gift_card_assign_user.py`
- Regenerate: `saleor/graphql/schema.graphql`

**Interfaces:**
- Consumes: `utils.assign_gift_card_to_user`, `GiftCardCannotAssign`, `events.gift_card_assigned_event`.
- Produces: `giftCardAssignUser(id: ID!, userId: ID!) -> { giftCard, errors }`, `MANAGE_GIFT_CARD`, emits `GIFT_CARD_UPDATED`.

- [ ] **Step 1: Write the failing tests**

```python
# saleor/graphql/giftcard/tests/mutations/test_gift_card_assign_user.py
import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation Assign($id: ID!, $userId: ID!) {
        giftCardAssignUser(id: $id, userId: $userId) {
            giftCard { id }
            errors { field code message }
        }
    }
"""


def _vars(gift_card, user):
    return {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "userId": graphene.Node.to_global_id("User", user.pk),
    }


def test_assign_user(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # when
    response = staff_api_client.post_graphql(
        MUTATION, _vars(gift_card, customer_user), permissions=[permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert data["errors"] == []
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email
    assert gift_card.events.filter(type=GiftCardEvents.ASSIGNED_TO_USER).count() == 1


def test_reassign_records_previous(
    staff_api_client, gift_card, customer_user, staff_user, permission_manage_gift_card
):
    # given
    from .....giftcard.utils import assign_gift_card_to_user

    assign_gift_card_to_user(gift_card, staff_user)

    # when
    response = staff_api_client.post_graphql(
        MUTATION, _vars(gift_card, customer_user), permissions=[permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert data["errors"] == []
    event = gift_card.events.filter(type=GiftCardEvents.ASSIGNED_TO_USER).last()
    assert event.parameters["previous_assigned_to_id"] == staff_user.id
    assert event.parameters["assigned_to_id"] == customer_user.id


def test_assign_blocked_when_used(
    staff_api_client, gift_card_used, customer_user, permission_manage_gift_card
):
    # when
    response = staff_api_client.post_graphql(
        MUTATION, _vars(gift_card_used, customer_user), permissions=[permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == GiftCardErrorCode.CANNOT_ASSIGN.name


def test_requires_permission(staff_api_client, gift_card, customer_user):
    # when
    response = staff_api_client.post_graphql(MUTATION, _vars(gift_card, customer_user))

    # then
    assert_no_permission(response)
```

> `gift_card_used` is an existing fixture with `last_used_on` set; if its state differs, set `last_used_on` in the test.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/mutations/test_gift_card_assign_user.py -v`
Expected: FAIL — field missing.

- [ ] **Step 3: Implement the mutation**

```python
# saleor/graphql/giftcard/mutations/gift_card_assign_user.py
import graphene
from django.core.exceptions import ValidationError

from ....account.models import User as UserModel
from ....core.utils.events import call_event
from ....giftcard import events, models
from ....giftcard.error_codes import GiftCardErrorCode
from ....giftcard.utils import GiftCardCannotAssign, assign_gift_card_to_user
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...account.types import User
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardAssignUser(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="The assigned gift card.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the gift card.")
        user_id = graphene.ID(
            required=True, description="ID of the customer to restrict the card to."
        )

    class Meta:
        description = (
            "Restrict a gift card so only the given customer can use it. " + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_UPDATED,
                description="A gift card was updated.",
            )
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, id, user_id):
        gift_card = cls.get_node_or_error(info, id, only_type=GiftCard, field="id")
        user = cls.get_node_or_error(
            info, user_id, only_type=User, field="user_id", qs=UserModel.objects.filter(is_active=True)
        )

        previous_user_id = gift_card.assigned_to_id
        previous_email = gift_card.assigned_to_email

        try:
            assign_gift_card_to_user(gift_card, user)
        except GiftCardCannotAssign as e:
            raise ValidationError(
                {"id": ValidationError(str(e), code=GiftCardErrorCode.CANNOT_ASSIGN.value)}
            ) from e

        staff = info.context.user
        app = get_app_promise(info.context).get()
        events.gift_card_assigned_event(
            gift_card, previous_user_id, previous_email, staff, app
        )

        manager = get_plugin_manager_promise(info.context).get()
        call_event(manager.gift_card_updated, gift_card)
        return cls(gift_card=gift_card, errors=[])
```

> `get_node_or_error(..., qs=UserModel.objects.filter(is_active=True))` enforces "active user"; staff accounts pass (no `is_staff` filter) per design.

- [ ] **Step 4: Register + regenerate schema**

Add to `mutations/__init__.py` and `schema.py`:
```python
    gift_card_assign_user = GiftCardAssignUser.Field()
```
Run: `.worktree-container/compose.sh exec saleor python manage.py graphql_schema --schema saleor/graphql/schema.graphql`

- [ ] **Step 5: Run tests**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/mutations/test_gift_card_assign_user.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add saleor/graphql/giftcard/mutations/gift_card_assign_user.py \
        saleor/graphql/giftcard/mutations/__init__.py saleor/graphql/giftcard/schema.py \
        saleor/graphql/schema.graphql \
        saleor/graphql/giftcard/tests/mutations/test_gift_card_assign_user.py
git commit -m "feat(giftcard): add giftCardAssignUser mutation"
```

---

### Task 8: `giftCardUnassignUser` mutation

**Files:**
- Create: `saleor/graphql/giftcard/mutations/gift_card_unassign_user.py`
- Modify: `mutations/__init__.py`, `schema.py`
- Test: `saleor/graphql/giftcard/tests/mutations/test_gift_card_unassign_user.py`
- Regenerate schema.

**Interfaces:**
- Produces: `giftCardUnassignUser(id: ID!) -> { giftCard, errors }`, `MANAGE_GIFT_CARD`, clears both fields, emits `UNASSIGNED_FROM_USER` event + `GIFT_CARD_UPDATED`.

- [ ] **Step 1: Write the failing test**

```python
# saleor/graphql/giftcard/tests/mutations/test_gift_card_unassign_user.py
import graphene

from .....giftcard import GiftCardEvents
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation Unassign($id: ID!) {
        giftCardUnassignUser(id: $id) {
            giftCard { id }
            errors { field code message }
        }
    }
"""


def test_unassign_clears_fields(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # given
    from .....giftcard.utils import assign_gift_card_to_user

    assign_gift_card_to_user(gift_card, customer_user)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardUnassignUser"]
    assert data["errors"] == []
    gift_card.refresh_from_db()
    assert gift_card.assigned_to is None
    assert gift_card.assigned_to_email is None
    assert gift_card.events.filter(type=GiftCardEvents.UNASSIGNED_FROM_USER).count() == 1


def test_requires_permission(staff_api_client, gift_card):
    # when
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}
    response = staff_api_client.post_graphql(MUTATION, variables)

    # then
    assert_no_permission(response)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/mutations/test_gift_card_unassign_user.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# saleor/graphql/giftcard/mutations/gift_card_unassign_user.py
import graphene

from ....core.utils.events import call_event
from ....giftcard import events, models
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardUnassignUser(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="The unassigned gift card.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the gift card.")

    class Meta:
        description = (
            "Remove a customer restriction from a gift card. " + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_UPDATED,
                description="A gift card was updated.",
            )
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, id):
        gift_card = cls.get_node_or_error(info, id, only_type=GiftCard, field="id")
        previous_user_id = gift_card.assigned_to_id
        previous_email = gift_card.assigned_to_email

        gift_card.assigned_to = None
        gift_card.assigned_to_email = None
        gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

        staff = info.context.user
        app = get_app_promise(info.context).get()
        events.gift_card_unassigned_event(
            gift_card, previous_user_id, previous_email, staff, app
        )

        manager = get_plugin_manager_promise(info.context).get()
        call_event(manager.gift_card_updated, gift_card)
        return cls(gift_card=gift_card, errors=[])
```

- [ ] **Step 4: Register + regenerate schema**

Add `gift_card_unassign_user = GiftCardUnassignUser.Field()`; run graphql_schema.

- [ ] **Step 5: Run test**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/mutations/test_gift_card_unassign_user.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add saleor/graphql/giftcard/mutations/gift_card_unassign_user.py \
        saleor/graphql/giftcard/mutations/__init__.py saleor/graphql/giftcard/schema.py \
        saleor/graphql/schema.graphql \
        saleor/graphql/giftcard/tests/mutations/test_gift_card_unassign_user.py
git commit -m "feat(giftcard): add giftCardUnassignUser mutation"
```

---

### Task 9: Optional `assignedTo` at `giftCardCreate`

**Files:**
- Modify: `saleor/graphql/giftcard/mutations/gift_card_create.py`
- Test: `saleor/graphql/giftcard/tests/mutations/test_gift_card_create.py`
- Regenerate schema.

**Interfaces:**
- Consumes: `events.gift_card_assigned_event`.
- Produces: `GiftCardCreateInput.assigned_to: ID` (optional). No guard (new card can't be in play). Sets `assigned_to` + `assigned_to_email`, emits `ASSIGNED_TO_USER`.

- [ ] **Step 1: Write the failing test**

```python
# append to saleor/graphql/giftcard/tests/mutations/test_gift_card_create.py
def test_create_with_assigned_to(
    staff_api_client, customer_user, permission_manage_gift_card
):
    # given
    from .....giftcard import GiftCardEvents
    import graphene

    query = """
        mutation Create($input: GiftCardCreateInput!) {
            giftCardCreate(input: $input) {
                giftCard { id }
                errors { field code }
            }
        }
    """
    variables = {
        "input": {
            "balance": {"amount": 100, "currency": "USD"},
            "isActive": True,
            "assignedTo": graphene.Node.to_global_id("User", customer_user.pk),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    from ....tests.utils import get_graphql_content

    data = get_graphql_content(response)["data"]["giftCardCreate"]
    assert data["errors"] == []
    from .....giftcard.models import GiftCard

    gift_card = GiftCard.objects.get(
        pk=graphene.Node.from_global_id(data["giftCard"]["id"])[1]
    )
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email
    assert gift_card.events.filter(type=GiftCardEvents.ASSIGNED_TO_USER).count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db "saleor/graphql/giftcard/tests/mutations/test_gift_card_create.py::test_create_with_assigned_to" -v`
Expected: FAIL — unknown input field `assignedTo`.

- [ ] **Step 3: Add input field, resolve it, persist + event**

In `gift_card_create.py`, add to `GiftCardCreateInput`:
```python
    assigned_to = graphene.ID(
        required=False,
        description=(
            "ID of the customer the gift card is restricted to. " + ADDED_IN_323
        ),
    )
```
(import `ADDED_IN_323` from `...core.descriptions`.)

In `clean_input`, after the `user_email` block, resolve the assignee:
```python
        if assigned_to_id := data.get("assigned_to"):
            assigned_user = cls.get_node_or_error(
                info, assigned_to_id, only_type="User", field="assigned_to"
            )
            cleaned_input["assigned_to"] = assigned_user
            cleaned_input["assigned_to_email"] = assigned_user.email
```

In `post_save_action`, after `gift_card_issued_event(...)`, emit assignment event when set:
```python
        if instance.assigned_to_id:
            events.gift_card_assigned_event(instance, None, None, user, app)
```
(The `assigned_to`/`assigned_to_email` values in `cleaned_input` are persisted by the base `ModelMutation.save`/`construct_instance` because they are real model fields.)

- [ ] **Step 4: Regenerate schema and run test**

Run:
```
.worktree-container/compose.sh exec saleor python manage.py graphql_schema --schema saleor/graphql/schema.graphql
.worktree-container/compose.sh exec saleor pytest --reuse-db "saleor/graphql/giftcard/tests/mutations/test_gift_card_create.py::test_create_with_assigned_to" -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add saleor/graphql/giftcard/mutations/gift_card_create.py saleor/graphql/schema.graphql \
        saleor/graphql/giftcard/tests/mutations/test_gift_card_create.py
git commit -m "feat(giftcard): allow assigning customer at gift card create"
```

---

### Task 10: Enforcement at `checkoutAddPromoCode`

**Files:**
- Modify: `saleor/giftcard/utils.py` (`add_gift_card_code_to_checkout`)
- Test: `saleor/giftcard/tests/test_utils.py`

**Interfaces:**
- Consumes: `assigned_to_id`/`assigned_to_email` fields.
- Behavior: after fetching `gift_card`, if `gift_card.assigned_to_email` is set, allow only when `checkout.user_id` equals `gift_card.assigned_to_id`; otherwise `raise InvalidPromoCode()` (generic, no reason leak). Guests (`checkout.user_id is None`) are rejected for restricted cards.

- [ ] **Step 1: Write the failing tests**

```python
# saleor/giftcard/tests/test_utils.py
import pytest

from ..utils import add_gift_card_code_to_checkout
from ...core.exceptions import InvalidPromoCode  # verify import path


def test_add_restricted_card_allows_matching_user(
    checkout_with_item, gift_card, customer_user
):
    # given
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.currency = checkout.currency
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "currency"])

    # when
    add_gift_card_code_to_checkout(
        checkout, customer_user.email, gift_card.code, checkout.currency
    )

    # then
    assert checkout.gift_cards.filter(pk=gift_card.pk).exists()


def test_add_restricted_card_rejects_other_user(
    checkout_with_item, gift_card, customer_user, staff_user
):
    # given
    checkout = checkout_with_item
    checkout.user = staff_user
    checkout.save(update_fields=["user"])
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.currency = checkout.currency
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "currency"])

    # when / then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, staff_user.email, gift_card.code, checkout.currency
        )


def test_add_restricted_card_rejects_guest(checkout_with_item, gift_card, customer_user):
    # given
    checkout = checkout_with_item
    checkout.user = None
    checkout.save(update_fields=["user"])
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.currency = checkout.currency
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "currency"])

    # when / then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, "guest@example.com", gift_card.code, checkout.currency
        )
```

> Verify `InvalidPromoCode`'s import path (grep for `class InvalidPromoCode`); adjust the import in the test and note it for Step 3.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_utils.py -k "restricted_card" -v`
Expected: FAIL — restriction not enforced (matching test may pass; the reject tests fail).

- [ ] **Step 3: Add the enforcement**

In `add_gift_card_code_to_checkout`, immediately after the `except GiftCard.DoesNotExist` block and before `checkout.gift_cards.add(gift_card)`:
```python
    if gift_card.assigned_to_email and gift_card.assigned_to_id != checkout.user_id:
        # Restricted gift cards can only be used by the assigned customer.
        # Generic error — do not reveal the assignee.
        raise InvalidPromoCode()
```
(When `checkout.user_id` is None or the FK was nulled by customer deletion, the inequality holds and the card is rejected.)

- [ ] **Step 4: Run tests**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard/tests/test_utils.py -k "restricted_card" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add saleor/giftcard/utils.py saleor/giftcard/tests/test_utils.py
git commit -m "feat(giftcard): enforce customer restriction when adding card to checkout"
```

---

### Task 11: Enforcement at `checkoutComplete`

**Files:**
- Modify: `saleor/checkout/checkout_cleaner.py` (`_validate_gift_cards`)
- Test: `saleor/checkout/tests/test_checkout_cleaner.py`

**Interfaces:**
- Behavior: within the gift-card checkout validation, if any attached card has `assigned_to_email` set and `assigned_to_id != checkout.user_id`, raise `GiftCardNotApplicable` with a **generic** message (no assignee identity).

- [ ] **Step 1: Write the failing test**

```python
# saleor/checkout/tests/test_checkout_cleaner.py
import pytest

from ..checkout_cleaner import _validate_gift_cards
from ...giftcard.models import GiftCard
from ..error_codes import CheckoutErrorCode  # for reference


def test_validate_gift_cards_rejects_mismatched_assignment(
    checkout_with_gift_card, customer_user, staff_user
):
    # given
    checkout = checkout_with_gift_card
    checkout.user = staff_user
    checkout.save(update_fields=["user"])
    gift_card = checkout.gift_cards.first()
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

    # when / then
    from ...giftcard.models import GiftCardNotApplicable  # verify path

    with pytest.raises(GiftCardNotApplicable):
        _validate_gift_cards(checkout)


def test_validate_gift_cards_allows_matching_assignment(
    checkout_with_gift_card, customer_user
):
    # given
    checkout = checkout_with_gift_card
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    gift_card = checkout.gift_cards.first()
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

    # when / then (no raise)
    _validate_gift_cards(checkout)
```

> Verify the import path of `GiftCardNotApplicable` (it is raised in the existing `_validate_gift_cards`; grep for its definition, likely `saleor/giftcard/models.py` or `saleor/core/exceptions.py`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/checkout/tests/test_checkout_cleaner.py -k gift_card -v`
Expected: mismatch test FAILS (no raise yet).

- [ ] **Step 3: Add the assignment check**

Append to `_validate_gift_cards` in `saleor/checkout/checkout_cleaner.py`:
```python
    restricted = GiftCard.objects.filter(
        checkouts=checkout.token, assigned_to_email__isnull=False
    )
    if checkout.user_id:
        restricted = restricted.exclude(assigned_to_id=checkout.user_id)
    if restricted.exists():
        # Generic message — do not reveal the assignee.
        raise GiftCardNotApplicable("Gift card cannot be used. Order placement cancelled.")
```

- [ ] **Step 4: Run tests**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/checkout/tests/test_checkout_cleaner.py -k gift_card -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add saleor/checkout/checkout_cleaner.py saleor/checkout/tests/test_checkout_cleaner.py
git commit -m "feat(giftcard): enforce customer restriction at checkout complete"
```

---

### Task 12: Expose `assignedTo` / `assignedToEmail` on the GiftCard type

**Files:**
- Modify: `saleor/graphql/giftcard/types.py`
- Test: `saleor/graphql/giftcard/tests/queries/test_gift_card.py`
- Regenerate schema.

**Interfaces:**
- Produces: `GiftCard.assignedTo: User` (resolver gated by `MANAGE_USERS`, owner-or-perm, mirroring `resolve_created_by`); `GiftCard.assignedToEmail: String` (obfuscation mirroring `resolve_created_by_email`).

- [ ] **Step 1: Write the failing test**

```python
# saleor/graphql/giftcard/tests/queries/test_gift_card.py
import graphene

from ....tests.utils import get_graphql_content

QUERY = """
    query GiftCard($id: ID!) {
        giftCard(id: $id) {
            assignedTo { email }
            assignedToEmail
        }
    }
"""


def test_assigned_to_visible_with_manage_users(
    staff_api_client,
    gift_card,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
):
    # given
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCard"]
    assert data["assignedTo"]["email"] == customer_user.email
    assert data["assignedToEmail"] == customer_user.email
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db "saleor/graphql/giftcard/tests/queries/test_gift_card.py::test_assigned_to_visible_with_manage_users" -v`
Expected: FAIL — field does not exist.

- [ ] **Step 3: Add fields + resolvers**

In `saleor/graphql/giftcard/types.py`, add fields near `used_by` (with `ADDED_IN_323`):
```python
    assigned_to = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The customer the gift card usage is restricted to. " + ADDED_IN_323,
    )
    assigned_to_email = graphene.String(
        required=False,
        description=(
            "Email of the customer the gift card is restricted to. " + ADDED_IN_323
        ),
    )
```
Add resolvers modeled on `resolve_created_by` / `resolve_created_by_email`:
```python
    @staticmethod
    def resolve_assigned_to(root: models.GiftCard, info):
        def _resolve_assigned_to(user):
            requestor = get_user_or_app_from_context(info.context)
            check_is_owner_or_has_one_of_perms(
                requestor, user, AccountPermissions.MANAGE_USERS
            )
            return user

        if root.assigned_to_id is None:
            return None
        return (
            UserByUserIdLoader(info.context)
            .load(root.assigned_to_id)
            .then(_resolve_assigned_to)
        )

    @staticmethod
    def resolve_assigned_to_email(root: models.GiftCard, info):
        def _resolve_assigned_to_email(user):
            requestor = get_user_or_app_from_context(info.context)
            if is_owner_or_has_one_of_perms(
                requestor, user, GiftcardPermissions.MANAGE_GIFT_CARD
            ):
                return user.email if user else root.assigned_to_email
            return obfuscate_email(user.email if user else root.assigned_to_email)

        if root.assigned_to_id is None:
            return _resolve_assigned_to_email(None)
        return (
            UserByUserIdLoader(info.context)
            .load(root.assigned_to_id)
            .then(_resolve_assigned_to_email)
        )
```

- [ ] **Step 4: Regenerate schema + run test**

Run:
```
.worktree-container/compose.sh exec saleor python manage.py graphql_schema --schema saleor/graphql/schema.graphql
.worktree-container/compose.sh exec saleor pytest --reuse-db "saleor/graphql/giftcard/tests/queries/test_gift_card.py::test_assigned_to_visible_with_manage_users" -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add saleor/graphql/giftcard/types.py saleor/graphql/schema.graphql \
        saleor/graphql/giftcard/tests/queries/test_gift_card.py
git commit -m "feat(giftcard): expose assignedTo and assignedToEmail on GiftCard"
```

---

### Task 13: Owner semantics — `resolve_code` + `me.giftCards`

**Files:**
- Modify: `saleor/graphql/giftcard/types.py` (`resolve_code`)
- Modify: `saleor/graphql/giftcard/dataloaders.py` (`GiftCardsByUserLoader`)
- Test: `saleor/graphql/giftcard/tests/queries/test_gift_card.py`, `saleor/graphql/account/tests/queries/test_me.py` (or existing me-giftcards test module)

**Interfaces:**
- Behavior: an assigned customer (`assigned_to == requestor`) counts as owner for `resolve_code`; `me.giftCards` returns the union of `used_by == me` and `assigned_to == me` cards (deduplicated).

- [ ] **Step 1: Write the failing tests**

```python
# saleor/graphql/giftcard/tests/queries/test_gift_card.py
import graphene

from ....tests.utils import get_graphql_content

CODE_QUERY = """
    query GiftCard($id: ID!) { giftCard(id: $id) { code } }
"""


def test_assigned_customer_can_read_code(user_api_client, gift_card, customer_user):
    # given (user_api_client is authenticated as customer_user)
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.used_by = None
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "used_by"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = user_api_client.post_graphql(CODE_QUERY, variables)

    # then
    data = get_graphql_content(response)["data"]["giftCard"]
    assert data["code"] == gift_card.code
```

```python
# me giftCards union test (place beside existing me.giftCards tests)
import graphene
from ....tests.utils import get_graphql_content

ME_GIFT_CARDS = """
    query { me { giftCards(first: 10) { edges { node { id } } } } }
"""


def test_me_gift_cards_includes_assigned(user_api_client, gift_card, customer_user):
    # given
    gift_card.used_by = None
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["used_by", "assigned_to", "assigned_to_email"])

    # when
    response = user_api_client.post_graphql(ME_GIFT_CARDS, {})

    # then
    edges = get_graphql_content(response)["data"]["me"]["giftCards"]["edges"]
    ids = {e["node"]["id"] for e in edges}
    assert graphene.Node.to_global_id("GiftCard", gift_card.pk) in ids
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/queries/test_gift_card.py -k "assigned_customer_can_read_code" -v`
Expected: FAIL (code is PermissionDenied; me list empty).

- [ ] **Step 3: Extend `resolve_code`**

Replace the `resolve_code` tail so it considers `assigned_to` as owner. Load both users; treat requestor as owner if it matches either `used_by` or `assigned_to`:
```python
    @staticmethod
    def resolve_code(root: models.GiftCard, info):
        def _resolve_code(owner_ids):
            requestor = get_user_or_app_from_context(info.context)
            if requestor:
                requestor_is_owner = getattr(requestor, "id", None) in owner_ids
                if requestor_is_owner or requestor.has_perm(
                    GiftcardPermissions.MANAGE_GIFT_CARD
                ):
                    return root.code
            return PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    GiftcardPermissions.MANAGE_GIFT_CARD,
                ]
            )

        owner_ids = {
            uid for uid in (root.used_by_id, root.assigned_to_id) if uid is not None
        }
        return _resolve_code(owner_ids)
```
> This compares ids directly (no user load needed for the owner check), preserving existing MANAGE_GIFT_CARD behavior.

- [ ] **Step 4: Extend `GiftCardsByUserLoader`**

In `saleor/graphql/giftcard/dataloaders.py`, union on `assigned_to_id`:
```python
    def batch_load(self, keys):
        from django.db.models import Q

        gift_cards = GiftCard.objects.using(self.database_connection_name).filter(
            Q(used_by_id__in=keys) | Q(assigned_to_id__in=keys)
        )
        gift_cards_by_user_map = defaultdict(list)
        for gift_card in gift_cards:
            seen = set()
            for uid in (gift_card.used_by_id, gift_card.assigned_to_id):
                if uid in keys and uid not in seen:
                    gift_cards_by_user_map[uid].append(gift_card)
                    seen.add(uid)
        return [gift_cards_by_user_map.get(user_id, []) for user_id in keys]
```

- [ ] **Step 5: Run tests**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/graphql/giftcard/tests/queries/test_gift_card.py saleor/graphql/account/tests/ -k "assigned" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add saleor/graphql/giftcard/types.py saleor/graphql/giftcard/dataloaders.py \
        saleor/graphql/giftcard/tests/queries/test_gift_card.py saleor/graphql/account/tests/
git commit -m "feat(giftcard): grant assigned customer owner visibility (code + me.giftCards)"
```

---

### Task 14: Staff `assignedTo` filter

**Files:**
- Modify: `saleor/graphql/giftcard/filters.py`
- Test: `saleor/graphql/giftcard/tests/queries/test_gift_cards.py` (filter tests module)
- Regenerate schema.

**Interfaces:**
- Produces: `GiftCardFilter.assigned_to` (`GlobalIDMultipleChoiceFilter`) filtering cards whose `assigned_to_id` is in the given user ids. Index from Task 4 backs it.

- [ ] **Step 1: Write the failing test**

```python
# saleor/graphql/giftcard/tests/queries/test_gift_cards.py
import graphene

from ....tests.utils import get_graphql_content

QUERY = """
    query GiftCards($filter: GiftCardFilterInput!) {
        giftCards(first: 10, filter: $filter) {
            edges { node { id } }
        }
    }
"""


def test_filter_by_assigned_to(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # given
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])
    variables = {
        "filter": {"assignedTo": [graphene.Node.to_global_id("User", customer_user.pk)]}
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY, variables, permissions=[permission_manage_gift_card]
    )

    # then
    edges = get_graphql_content(response)["data"]["giftCards"]["edges"]
    ids = {e["node"]["id"] for e in edges}
    assert graphene.Node.to_global_id("GiftCard", gift_card.pk) in ids
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.worktree-container/compose.sh exec saleor pytest --reuse-db "saleor/graphql/giftcard/tests/queries/test_gift_cards.py::test_filter_by_assigned_to" -v`
Expected: FAIL — unknown filter field `assignedTo`.

- [ ] **Step 3: Add filter function + field**

In `saleor/graphql/giftcard/filters.py`, add a module-level filter fn (mirror `filter_used_by`):
```python
def filter_assigned_to(qs, _, value):
    if value:
        _, user_pks = resolve_global_ids_to_primary_keys(value, "User")
        users = account_models.User.objects.using(qs.db).filter(pk__in=user_pks)
        qs = qs.filter(Exists(users.filter(pk=OuterRef("assigned_to_id"))))
    return qs
```
Add to `GiftCardFilter`:
```python
    assigned_to = GlobalIDMultipleChoiceFilter(method=filter_assigned_to)
```

- [ ] **Step 4: Regenerate schema + run test**

Run:
```
.worktree-container/compose.sh exec saleor python manage.py graphql_schema --schema saleor/graphql/schema.graphql
.worktree-container/compose.sh exec saleor pytest --reuse-db "saleor/graphql/giftcard/tests/queries/test_gift_cards.py::test_filter_by_assigned_to" -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add saleor/graphql/giftcard/filters.py saleor/graphql/schema.graphql \
        saleor/graphql/giftcard/tests/queries/test_gift_cards.py
git commit -m "feat(giftcard): add assignedTo filter to gift card list"
```

---

### Task 15: Changelog + full regression

**Files:**
- Modify: `CHANGELOG.md`
- Regenerate/verify: `saleor/graphql/schema.graphql`

- [ ] **Step 1: Add changelog entries**

Under the unreleased section:
```
- Add `giftCardBalanceAdjust` mutation to change a gift card balance by a signed delta atomically. - #<PR>
- Add customer restriction for gift cards: `assignedTo`/`assignedToEmail` fields, `giftCardAssignUser`/`giftCardUnassignUser` mutations, `assignedTo` on `GiftCardCreateInput`, and `assignedTo` gift card filter. Restricted cards can only be used by the assigned customer at checkout. - #<PR>
```

- [ ] **Step 2: Verify schema is committed and clean**

Run:
```
.worktree-container/compose.sh exec saleor python manage.py graphql_schema --schema saleor/graphql/schema.graphql
git diff --exit-code saleor/graphql/schema.graphql
```
Expected: no diff (schema already regenerated in prior tasks).

- [ ] **Step 3: Run full giftcard + checkout regression**

Run:
```
.worktree-container/compose.sh exec saleor pytest --reuse-db saleor/giftcard saleor/graphql/giftcard saleor/checkout/tests/test_checkout_cleaner.py -q
```
Expected: PASS (no regressions).

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(giftcard): changelog for balance adjust + customer assignment"
```

---

## Self-Review

**Spec coverage** (each locked decision → task):
- Balance delta as dedicated atomic mutation, current-only + initial bump, clamp-to-zero, `BALANCE_ADJUSTED` gated event, allowed on inactive/expired, `GIFT_CARD_UPDATED` webhook → Tasks 1–3. ✅
- `assigned_to` FK (SET_NULL) + persistent `assigned_to_email`, restricted-iff-email, FK-only matching, index → Task 4. ✅
- `used_by` untouched → respected throughout (only `assigned_to` used). ✅
- Staff assign/unassign `MANAGE_GIFT_CARD`, any active user (staff allowed), guard (used-in-order / paid-checkout freeze via `CANNOT_ASSIGN`, clean-checkout auto-detach via removal helper), row-locked, reassign records prev+new in one event → Tasks 6–8. ✅
- Optional `assignedTo` at create (no guard) → Task 9. ✅
- Enforcement at add + complete, generic `INVALID_PROMO_CODE` / `GiftCardNotApplicable`, no reason leak, guests rejected → Tasks 10–11. ✅
- Reads: `assignedTo` (MANAGE_USERS-gated), `assignedToEmail` (obfuscated), assigned customer = owner (code + me.giftCards), staff filter → Tasks 12–14. ✅
- Assign/unassign events staff-only + `GIFT_CARD_UPDATED` webhook → Tasks 5, 7, 8. ✅
- No bulk assign → intentionally omitted. ✅
- `ADDED_IN_323` on all new API; schema regen; changelog → throughout + Task 15. ✅

**Type consistency:** `assigned_to`/`assigned_to_email` model fields, `assigned_gift_cards` related_name, `GiftCardErrorCode.CANNOT_ASSIGN`, `GiftCardEvents.{BALANCE_ADJUSTED,ASSIGNED_TO_USER,UNASSIGNED_FROM_USER}`, `assign_gift_card_to_user`/`GiftCardCannotAssign`, `gift_card_qs_select_for_update`, and event helper signatures are used identically across tasks. ✅

**Pre-flight verifications flagged inline (do before/at the referenced step):**
1. `Decimal` scalar export in `saleor/graphql/core/scalars.py` (Task 3) — fall back to `graphene.Decimal`.
2. `InvalidPromoCode` import path (Task 10).
3. `GiftCardNotApplicable` import path (Task 11).
4. `transaction_item_generator` fixture signature (Task 6).
5. Existing `me.giftCards` test module location (Task 13).
