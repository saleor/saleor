"""Checkout completion must not lose or repeat the work it owes a paying customer.

These are due-work-harness contracts (https://github.com/gigaverse-app/due-work-harness)
for ``saleor/checkout/complete_checkout.py``. Completing a paid checkout makes
three commits before any callback runs: reserving stock, capturing the payment,
then creating the order. The order's transaction registers two
``transaction.on_commit`` callbacks: ``order_created`` (the order's events, the
customer's order count, the ORDER_CREATED webhooks), whose writes each commit on
their own, and ``send_order_confirmation``. The obligation: a customer who is
charged has an order, and every order is recorded as placed, confirmed to them,
and announced to the shop's integration.

The shop has one integration: an app subscribed to the ORDER_CREATED,
ORDER_FULLY_PAID and ORDER_CONFIRMED webhooks, as a shop with an ERP or a
fulfilment service has. Its endpoint is the external seam; the webhooks reach it
through Saleor's own webhook plugin and Celery task.

What the harness proves. For each contract it generates cases that replay the
real ``complete_checkout`` and kill the worker after each of its commits, fail
each after-commit callback, and refuse each Celery publication, then run every
recovery Saleor has and compare what is left with the fully delivered outcome.
Recovery is everything Saleor does on its own: every task in its
``CELERY_BEAT_SCHEDULE``, run one hour, one day, 31 days and 91 days later, past
every expiry Saleor configures. The contracts also prove what each recovery
sweep and retention task selects, against the real queries.

* ``CHECKOUT_AS_SHIPPED`` covers the two ``on_commit`` handoffs in
  ``_post_create_order_actions``. What the harness finds there is declared as
  gaps; each is a strict xfail, so the change that fixes a gap makes its case
  pass and must delete the gap. See https://github.com/saleor/saleor/issues/19835.
* ``CHECKOUT_WITH_AUTOMATIC_COMPLETION`` is Saleor's own answer to a charged
  customer with no order: money held as a Transactions API transaction, and a
  beat task that completes a fully paid checkout. It passes, except for two
  gaps in the sweep, declared the same way.
* ``FINDINGS`` pins what every history leaves, in the same run as the verdict,
  so a change to checkout completion shows exactly what moved.

The transition is ``complete_checkout``, called exactly as the
``checkoutComplete`` mutation calls it. (Not through the GraphQL view: its
graphql-core 2 executor waits on a promise that a simulated death, a
``BaseException`` raised in the resolver, never resolves. A real process death
never crosses the resolver, so this is an artefact of simulating it, and the
mutation adds nothing after ``complete_checkout`` returns.) The fixtures are
Saleor's own.

Run with a single process, as the cases commit for real::

    pytest saleor/checkout/tests/due_work -n0
"""

from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
from typing import Any
from unittest import mock
from uuid import UUID

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone
from due_work_harness import (
    Adoption,
    CallableDelivery,
    Claim,
    Decline,
    DueWorkContract,
    DueWorkSource,
    Findings,
    HandoffHistory,
    KnownGap,
    NotApplicable,
    Profile,
    Retention,
    SafetyContract,
    SafetyProfile,
    due_work_contract_suite,
)
from due_work_harness.integrations.celery import (
    celery_beat_evidence,
    held_publications,
)
from due_work_harness.integrations.django.selection import selection_built_by
from due_work_harness.profiles.automatic_recovery import (
    DueWorkSweep,
    InFlightExecution,
)
from freezegun import freeze_time
from pydantic import BaseModel, ConfigDict

from ....account.models import Address, User
from ....celeryconf import app
from ....channel.models import Channel
from ....core.notify import NotifyEventType
from ....graphql.core.utils import to_global_id_or_none
from ....order.models import Order
from ....payment import ChargeStatus, TransactionEventType
from ....payment.models import Payment, TransactionItem
from ....payment.utils import recalculate_transaction_amounts
from ....plugins.manager import PluginsManager, get_plugins_manager
from ....product.models import ProductVariant
from ....site.models import SiteSettings
from ....warehouse.models import Stock
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook
from ....webhook.transport.asynchronous import transport as webhook_transport
from ....webhook.transport.utils import WebhookResponse
from ... import calculations
from ...complete_checkout import _post_create_order_actions, complete_checkout
from ...fetch import fetch_checkout_info, fetch_checkout_lines
from ...models import Checkout, CheckoutMetadata
from ...payment_utils import update_checkout_payment_statuses
from ...tasks import (
    AUTOMATIC_COMPLETION_BATCH_SIZE,
    automatic_checkout_completion_task,
    delete_expired_checkouts,
    trigger_automatic_checkout_completion_task,
)
from ..utils import add_variant_to_checkout

#: Far enough ahead for every age-based task Saleor schedules to act: the longest,
#: deleting a user's checkout, waits USER_CHECKOUTS_TIMEDELTA (90 days).
RECOVERY_HORIZONS = (
    timedelta(hours=1),
    timedelta(days=1),
    timedelta(days=31),
    timedelta(days=91),
)


def run_beat_schedule() -> None:
    """Run every periodic task at each horizon: what Saleor does on its own over three months."""
    app.loader.import_default_modules()
    start = timezone.now()
    for horizon in RECOVERY_HORIZONS:
        with freeze_time(start + horizon):
            for entry in settings.CELERY_BEAT_SCHEDULE.values():
                app.tasks[entry["task"]].apply()


# The test settings run Celery tasks eagerly and Saleor's callbacks run in the
# web process: there is no message separate from the process, so no `lose`.
SALEOR = CallableDelivery(name="saleor complete_checkout", recover=run_beat_schedule)


class Shop(BaseModel):
    """What Saleor's own fixtures built for one test, published for the contract's zero-argument bindings."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    channel: Channel
    variant: ProductVariant
    customer: User
    address: Address
    assign_delivery: Callable[[Checkout], Any]
    #: Order confirmations Saleor handed to its notification plugins, by order id.
    confirmations: Counter[str]
    #: Webhooks the shop's integration received: (event type, payload).
    webhooks: list[tuple[str, str]]
    #: Saleor's own Transactions API fixture factories, for the paid-checkout history.
    transaction_item: Callable[..., TransactionItem]
    transaction_events: Callable[..., Any]


_SHOPS: list[Shop] = []


def current_shop() -> Shop:
    assert _SHOPS, "a Saleor contract case runs inside its saleor_shop fixture"
    return _SHOPS[-1]


@pytest.fixture
def saleor_shop(
    monkeypatch,
    channel_USD,
    product,
    shipping_zone,
    customer_user,
    address,
    checkout_delivery,
    transaction_item_generator,
    transaction_events_generator,
    webhook_app,
    settings,
) -> Iterator[Shop]:
    """Build a shop from Saleor's own fixtures, stocked for every history's order, with confirmations counted.

    The shop has an integration subscribed to its order webhooks, as a shop with an
    ERP or a fulfilment service does, so completing a checkout publishes them.
    """
    channel_USD.automatically_confirm_all_new_orders = True
    channel_USD.save()
    # The plugins Saleor's own checkout tests pair: webhooks, and its test payment gateway.
    settings.PLUGINS = [
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.plugins.tests.gateways.dummy.DummyGatewayPlugin",
    ]
    integration = Webhook.objects.create(
        name="erp", app=webhook_app, target_url="https://erp.example.com/saleor"
    )
    for event_type in ORDER_WEBHOOKS:
        integration.events.create(event_type=event_type)
    variant = product.variants.first()
    # ARRANGE: every history places an order, so stock the variant for all of them.
    Stock.objects.filter(product_variant=variant).update(quantity=1_000_000)
    shop = Shop(
        channel=channel_USD,
        variant=variant,
        customer=customer_user,
        address=address,
        assign_delivery=checkout_delivery,
        confirmations=Counter(),
        webhooks=[],
        transaction_item=transaction_item_generator,
        transaction_events=transaction_events_generator,
    )
    notify = PluginsManager.notify

    def recording_notify(
        self: PluginsManager, event: str, payload_func, channel_slug=None, **kwargs
    ):
        # EXTERNAL SEAM: the call Saleor's own checkout tests mock; plugins would send the email from here.
        # Recorded into the shop's own counter: Pydantic validated a copy of any counter passed in.
        if event == NotifyEventType.ORDER_CONFIRMATION:
            shop.confirmations[payload_func()["order"]["id"]] += 1
        return notify(
            self,
            event,
            payload_func=payload_func,
            channel_slug=channel_slug,
            **kwargs,
        )

    monkeypatch.setattr(PluginsManager, "notify", recording_notify)

    def integration_endpoint(
        target_url, domain, secret, event_type, data, custom_headers=None
    ):
        # EXTERNAL SEAM: the integration's HTTP endpoint, which accepts every webhook.
        shop.webhooks.append(
            (event_type, data if isinstance(data, str) else data.decode())
        )
        return WebhookResponse(content="ok", response_status_code=200)

    monkeypatch.setattr(
        webhook_transport, "send_webhook_using_scheme_method", integration_endpoint
    )
    _SHOPS.append(shop)
    yield shop
    _SHOPS.pop()


#: The channel's automatic_completion_delay: how long a fully paid checkout waits before Saleor completes it.
COMPLETION_DELAY = timedelta(minutes=5)


@pytest.fixture
def automatic_completion(saleor_shop: Shop) -> None:
    """Opt the channel into automatic completion of fully paid checkouts, after COMPLETION_DELAY."""
    saleor_shop.channel.automatically_complete_fully_paid_checkouts = True
    saleor_shop.channel.automatic_completion_delay = int(
        COMPLETION_DELAY.total_seconds() // 60
    )
    saleor_shop.channel.save()
    DISPATCHED.clear()
    COMPLETIONS.clear()


#: The order webhooks the shop's integration subscribes to.
ORDER_WEBHOOKS = (
    WebhookEventAsyncType.ORDER_CREATED,
    WebhookEventAsyncType.ORDER_FULLY_PAID,
    WebhookEventAsyncType.ORDER_CONFIRMED,
)

type Handle = tuple[UUID, Any]


def _checkout() -> tuple[Checkout, Any]:
    """Create a customer's checkout for one product, as Saleor's own checkoutComplete tests arrange it."""
    shop = current_shop()
    checkout = Checkout.objects.create(
        currency=shop.channel.currency_code,
        channel=shop.channel,
        price_expiration=timezone.now() + settings.CHECKOUT_PRICES_TTL,
        email=shop.customer.email,
        user=shop.customer,
        shipping_address=shop.address.get_copy(),
        billing_address=shop.address.get_copy(),
    )
    checkout.set_country("US", commit=True)
    CheckoutMetadata.objects.create(checkout=checkout)
    manager = get_plugins_manager(allow_replica=False)
    add_variant_to_checkout(fetch_checkout_info(checkout, [], manager), shop.variant, 1)
    checkout.assigned_delivery = shop.assign_delivery(checkout)
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, fetch_checkout_info(checkout, lines, manager), lines
    )
    return checkout, total.gross


def complete(handle: Handle) -> None:
    """REAL PRODUCTION: complete_checkout, called as Saleor's checkoutComplete mutation calls it."""
    manager = get_plugins_manager(allow_replica=False)
    checkout = Checkout.objects.get(pk=handle[0])
    lines, _ = fetch_checkout_lines(checkout)
    complete_checkout(
        manager=manager,
        checkout_info=fetch_checkout_info(checkout, lines, manager),
        lines=lines,
        payment_data={},
        store_source=False,
        user=current_shop().customer,
        app=None,
        site_settings=SiteSettings.objects.get(site=Site.objects.get_current()),
        redirect_url="https://www.example.com",
    )


def _order(checkout_pk: UUID) -> Order | None:
    return Order.objects.filter(checkout_token=str(checkout_pk)).first()


def _money_on(model: type[Payment] | type[TransactionItem], pk: object) -> str:
    """Tell what a payment's money belongs to: its order, its checkout, or nothing at all."""
    order_id, checkout_id = (
        model.objects.filter(pk=pk).values_list("order_id", "checkout_id").get()
    )
    return "order" if order_id else "checkout" if checkout_id else "nothing"


class Outcome(BaseModel):
    """What the customer and the shop see: the order, its history, the confirmation, and the money."""

    model_config = ConfigDict(frozen=True)

    order: bool
    events: tuple[str, ...]
    confirmations: int
    #: The order webhooks the shop's integration received.
    webhooks: tuple[str, ...]
    charged: bool
    #: What the customer's money belongs to: "order", "checkout" or "nothing".
    money_on: str


def pay_with_the_payments_api() -> Handle:
    """ARRANGE: a fresh checkout and its Payments API payment, which complete_checkout captures itself."""
    checkout, total = _checkout()
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        checkout=checkout,
        is_active=True,
        total=total.amount,
        currency=total.currency,
        billing_email=checkout.email,
    )
    return checkout.pk, payment.pk


def order_confirmation_and_money(handle: Handle) -> Outcome:
    """OBSERVE: the order and its history, the confirmations the customer was sent, and where the money is."""
    order = _order(handle[0])
    payment = Payment.objects.get(pk=handle[1])
    order_id = to_global_id_or_none(order) if order else None
    return Outcome(
        order=order is not None,
        events=tuple(sorted(order.events.values_list("type", flat=True)))
        if order
        else (),
        confirmations=current_shop().confirmations[order_id] if order_id else 0,
        webhooks=tuple(
            sorted(
                event
                for event, data in current_shop().webhooks
                if order_id and order_id in data
            )
        ),
        charged=payment.captured_amount > 0,
        money_on=_money_on(Payment, payment.pk),
    )


PLACED = Outcome(
    order=True,
    events=("confirmed", "order_fully_paid", "payment_captured", "placed"),
    confirmations=1,
    webhooks=tuple(sorted(ORDER_WEBHOOKS)),
    charged=True,
    money_on="order",
)


def _outcome(**changes: object) -> Outcome:
    return PLACED.model_copy(update=changes)


#: The order's history as it grows, and the webhooks its integration receives.
PLACED_ONLY = ("placed",)
CAPTURED = ("payment_captured", "placed")
FULLY_PAID = ("order_fully_paid", "payment_captured", "placed")
CREATED = (WebhookEventAsyncType.ORDER_CREATED,)
CREATED_AND_PAID = (
    WebhookEventAsyncType.ORDER_CREATED,
    WebhookEventAsyncType.ORDER_FULLY_PAID,
)


def _unconfirmed(events: tuple[str, ...], webhooks: tuple[str, ...]) -> Outcome:
    return _outcome(events=events, webhooks=webhooks, confirmations=0)


#: What each history leaves after three months of everything Saleor schedules.
#: Every entry is a loss the customer, the shop or its integration sees.
FINDINGS = {
    # Benign: nothing was charged, and the customer can try again.
    "worker died after commit 1": _outcome(
        order=False,
        events=(),
        confirmations=0,
        webhooks=(),
        charged=False,
        money_on="nothing",
    ),
    # FINDING 1: charged, and no order is ever created. The payment is captured in its
    # own transaction before the order's; 90 days later Saleor deletes the checkout,
    # and the captured payment belongs to nothing.
    "worker died after commit 2": _outcome(
        order=False, events=(), confirmations=0, webhooks=(), money_on="nothing"
    ),
    # FINDING 2: a paid order, never confirmed, its history and its integration's webhooks
    # cut off wherever the worker died. Everything after the order's commit runs in
    # on_commit callbacks, one autocommit write at a time, and nothing Saleor schedules
    # re-runs them.
    "worker died after commit 3": _unconfirmed((), ()),
    "worker died after commit 4": _unconfirmed((), ()),
    "worker died after commit 5": _unconfirmed((), ()),
    "worker died after commit 6": _unconfirmed(PLACED_ONLY, ()),
    "worker died after commit 7": _unconfirmed(PLACED_ONLY, ()),
    "worker died after commit 8": _unconfirmed(PLACED_ONLY, ()),
    "worker died after commit 9": _unconfirmed(PLACED_ONLY, CREATED),
    "worker died after commit 10": _unconfirmed(PLACED_ONLY, CREATED),
    "worker died after commit 11": _unconfirmed(CAPTURED, CREATED),
    "worker died after commit 12": _unconfirmed(FULLY_PAID, CREATED),
    "worker died after commit 13": _unconfirmed(FULLY_PAID, CREATED),
    "worker died after commit 14": _unconfirmed(FULLY_PAID, CREATED),
    "worker died after commit 15": _unconfirmed(FULLY_PAID, CREATED),
    "worker died after commit 16": _unconfirmed(FULLY_PAID, CREATED_AND_PAID),
    "worker died after commit 17": _unconfirmed(FULLY_PAID, CREATED_AND_PAID),
    "worker died after commit 18": _unconfirmed(PLACED.events, CREATED_AND_PAID),
    "worker died after commit 19": _unconfirmed(PLACED.events, CREATED_AND_PAID),
    "worker died after commit 20": _unconfirmed(PLACED.events, CREATED_AND_PAID),
    "worker died after commit 21": _unconfirmed(PLACED.events, PLACED.webhooks),
    "worker died after commit 22": _unconfirmed(PLACED.events, PLACED.webhooks),
    # FINDING 3: no death at all. When order_created raises (a webhook payload bug, a
    # plugin error, a database error), Django skips every later callback of the
    # commit, so the confirmation is lost with the order's history.
    "after-commit callback 1 failed": _unconfirmed((), ()),
    "after-commit callback 2 failed": _unconfirmed(PLACED.events, PLACED.webhooks),
    # FINDING 4: no death either. When the broker refuses one publish, any of the order's
    # three webhooks, the error escapes order_created: every webhook and history entry
    # after it is lost, Django skips the confirmation, and completing the checkout
    # raises for an order that is placed and paid. Even a refused ORDER_CONFIRMED, the
    # last webhook, costs the customer the confirmation. This is
    # https://github.com/saleor/saleor/issues/19835.
    "the broker refused publication 1": _unconfirmed(PLACED_ONLY, ()),
    "the broker refused publication 2": _unconfirmed(FULLY_PAID, CREATED),
    "the broker refused publication 3": _unconfirmed(PLACED.events, CREATED_AND_PAID),
}


COMPLETE_CHECKOUT = HandoffHistory(
    name="complete checkout",
    arrange=pay_with_the_payments_api,
    transition=complete,
    observe=order_confirmation_and_money,
    # Checked in the same run as the verdict: a finding that moves fails the case.
    findings=Findings(PLACED, FINDINGS),
)

#: Past USER_CHECKOUTS_TIMEDELTA (90 days), after which Saleor deletes a user's checkout.
EXPIRED = timedelta(days=91)


def _expire(checkout: Checkout) -> UUID:
    # ARRANGE: untouched since before Saleor's expiry window (update() skips last_change's auto_now).
    Checkout.objects.filter(pk=checkout.pk).update(last_change=timezone.now() - EXPIRED)
    return checkout.pk


def charged_through_the_payments_api() -> UUID:
    """Create a checkout whose Payments API payment was captured and whose order was never created: an order is owed."""
    checkout, total = _checkout()
    Payment.objects.create(
        gateway="mirumee.payments.dummy",
        checkout=checkout,
        is_active=True,
        total=total.amount,
        captured_amount=total.amount,
        charge_status=ChargeStatus.FULLY_CHARGED,
        currency=total.currency,
        billing_email=checkout.email,
    )
    return _expire(checkout)


def charged_through_transactions() -> UUID:
    """Create a checkout charged through the Transactions API whose order was never created: an order is owed."""
    checkout_pk, _ = pay_with_transactions()
    return _expire(Checkout.objects.get(pk=checkout_pk))


def abandoned() -> UUID:
    """Create a checkout nobody paid for, past its expiry: Saleor's own policy says it goes."""
    checkout, _ = _checkout()
    return _expire(checkout)


def _checkout_retention(owed: Callable[[], UUID]) -> Retention:
    return Retention(
        name="saleor delete_expired_checkouts",
        make_non_terminal=owed,
        make_prunable=abandoned,
        run_retention=delete_expired_checkouts,
        still_exists=lambda checkout_pk: Checkout.objects.filter(
            pk=checkout_pk
        ).exists(),
    )


def retention_of_payments_api_checkouts() -> Retention:
    # ARRANGE: an expired checkout holding a captured Payments API payment, and an abandoned one.
    # REAL PRODUCTION: Saleor's delete_expired_checkouts task, as its beat schedule runs it.
    # EXTERNAL SEAM: none.
    # OBSERVE: whether each checkout still exists.
    return _checkout_retention(charged_through_the_payments_api)


def retention_of_transactions_checkouts() -> Retention:
    # ARRANGE: an expired checkout holding charged Transactions API money, and an abandoned one.
    # REAL PRODUCTION: Saleor's delete_expired_checkouts task, as its beat schedule runs it.
    # EXTERNAL SEAM: none.
    # OBSERVE: whether each checkout still exists.
    return _checkout_retention(charged_through_transactions)


CHECKOUT_AS_SHIPPED = DueWorkContract(
    name="saleor checkout",
    adoption=Adoption.LEGACY,
    transactional=True,
    fixtures=("saleor_shop",),
    profiles={
        Profile.A: KnownGap(
            "no periodic task Saleor schedules selects an order whose after-commit work never ran: its events, "
            "its ORDER_CREATED webhooks and its confirmation are owed by nothing but the lost callbacks "
            "(https://github.com/saleor/saleor/issues/19835)"
        ),
        Profile.B: Decline(
            "completion serialises on the checkout row lock (select_for_update) inside each of its transactions; "
            "it holds no lease that could outlive a worker"
        ),
        Profile.C: KnownGap(
            "with the Payments API the gateway captures the payment between two commits: a death after the "
            "capture leaves an outcome Saleor never reconciles, so the customer is charged and no order is made"
        ),
        Profile.D: Claim(
            gaps={
                "assert_retention_preserves_non_terminal_work": (
                    "delete_expired_checkouts keeps checkouts holding Transactions API money, but deletes one "
                    "holding a captured Payments API payment, the only record that an order is owed: after 90 "
                    "days that payment belongs to nothing"
                )
            }
        ),
        Profile.E: NotApplicable(
            "one completion writes each order's events and confirmation once; no two race"
        ),
        Profile.F: KnownGap(
            "no product state records that an order is still to be confirmed, so no recovery can derive the "
            "obligation the lost callback held (https://github.com/saleor/saleor/issues/19835)"
        ),
    },
    safety=SafetyContract(
        name="saleor checkout",
        adoption=Adoption.LEGACY,
        profiles={
            SafetyProfile.REPLAY_SAFE_EXECUTION: Decline(
                "nothing in Saleor replays a lost confirmation (profile A), so there is no replay to make safe"
            ),
            SafetyProfile.BOUNDED_RETRY: NotApplicable(
                "the post-commit callbacks are not retried"
            ),
        },
    ),
    retention=retention_of_payments_api_checkouts,
    handoffs=(COMPLETE_CHECKOUT,),
    handoff_delivery=SALEOR,
    handoff_gaps={
        "complete checkout": (
            "a death after the Payments API capture charges the customer with no order, which after 90 days "
            "belongs to nothing; a death after the order commits leaves it unconfirmed with its history empty or "
            "half-written; and a failing order_created callback, or the broker refusing any one of the order's "
            "webhooks, with no death at all, makes Django skip the confirmation "
            "(https://github.com/saleor/saleor/issues/19835). "
            "FINDINGS pins each history"
        )
    },
)


# This is where the magic happens. The class is empty on purpose: the decorator reads the
# CHECKOUT_AS_SHIPPED contract above and generates its tests, one or more for every
# guarantee the contract claims or declines, bound to Saleor's real checkoutComplete
# mutation, Celery broker, webhooks and delete_expired_checkouts task. No test case is
# written by hand.
#
# One of the generated cases is how #19835 was found:
# handoff-complete checkout-assert_crash_at_every_commit_converges replays checkoutComplete
# once per thing that can go wrong: the process dies after each commit or after the
# gateway charges, an order_created receiver raises, or the broker refuses one of the
# order's webhook publishes. It then compares each run with a normal checkout. A refused
# publish, with no crash at all, ends with an order that has no confirmation email and is
# missing its webhooks, so the case fails. The contract declares that as a gap, so it is
# reported as a strict XFAIL; the day every history converges, it passes, and the strict
# marker fails the run until the gap is removed.
@due_work_contract_suite(
    CHECKOUT_AS_SHIPPED, covers=(DueWorkSource(_post_create_order_actions, sites=2),)
)
class TestCheckoutAsShipped:
    """Every case in this class is generated from CHECKOUT_AS_SHIPPED; see the comment above."""


class Paid(BaseModel):
    """The money and the order alone: whether a charged customer has an order to show for it."""

    model_config = ConfigDict(frozen=True)

    order: bool
    charged: bool
    money_on: str


def pay_with_transactions() -> Handle:
    """ARRANGE: a fresh checkout, charged by the payment app before completion, as Saleor's own tests arrange it."""
    shop = current_shop()
    checkout, total = _checkout()
    transaction = shop.transaction_item(checkout_id=checkout.pk)
    shop.transaction_events(
        transaction=transaction,
        psp_references=["1"],
        types=[TransactionEventType.CHARGE_SUCCESS],
        amounts=[total.amount],
    )
    recalculate_transaction_amounts(transaction)
    # Settle the checkout's payment status now, as Saleor would on the next fetch, so that
    # completing it writes nothing inside fetch_checkout_data's promise chain, where a
    # simulated death (a BaseException) would leave the promise waiting forever.
    update_checkout_payment_statuses(checkout, total, checkout_has_lines=True)
    return checkout.pk, transaction.pk


def order_and_money(handle: Handle) -> Paid:
    """OBSERVE: whether the charged customer has an order, and where the money is."""
    transaction = TransactionItem.objects.get(pk=handle[1])
    return Paid(
        order=_order(handle[0]) is not None,
        charged=transaction.charged_value > Decimal(0),
        money_on=_money_on(TransactionItem, transaction.pk),
    )


COMPLETE_PAID_CHECKOUT = HandoffHistory(
    name="complete paid checkout",
    arrange=pay_with_transactions,
    transition=complete,
    observe=order_and_money,
)

#: The checkouts the most recent tick dispatched for completion, in dispatch order.
DISPATCHED: list[UUID] = []
#: Every completion dispatched for a checkout, held or run: each is an execution in production.
COMPLETIONS: Counter[UUID] = Counter()


def completion_selection() -> Any:
    """Observe Saleor's selection: the query its own tick evaluates, with the tick's dispatches held."""
    with held_publications():
        return selection_built_by(trigger_automatic_checkout_completion_task, Checkout)


def run_completion_tick() -> int:
    """Run Saleor's tick, as its beat schedule runs it, with each completion it dispatches recorded."""
    DISPATCHED.clear()
    dispatch = automatic_checkout_completion_task.apply_async

    def recorded(args: Any = None, kwargs: Any = None, **options: Any) -> Any:
        # EXTERNAL SEAM: the completion task's publication, recorded on its way through.
        DISPATCHED.append(args[0])
        COMPLETIONS[args[0]] += 1
        return dispatch(args=args, kwargs=kwargs, **options)

    # mock, not pytest's MonkeyPatch: on undo MonkeyPatch writes the bound method back onto the
    # task instance, where it would shadow every later class-level patch of Task.apply_async.
    with mock.patch.object(automatic_checkout_completion_task, "apply_async", recorded):
        trigger_automatic_checkout_completion_task()
    return len(DISPATCHED)


def owed_completion(age: timedelta = timedelta(0)) -> Checkout:
    """Create a fully paid checkout that nobody completed, last changed ``age`` ago: Saleor owes it an order."""
    checkout_pk, _ = pay_with_transactions()
    Checkout.objects.filter(pk=checkout_pk).update(last_change=timezone.now() - age)
    return Checkout.objects.get(pk=checkout_pk)


def given_up_completion(age: timedelta = timedelta(0)) -> list[Checkout]:
    """Create a fully paid checkout past AUTOMATIC_CHECKOUT_COMPLETION_OLDEST_MODIFIED, which Saleor stops retrying."""
    return [
        owed_completion(
            settings.AUTOMATIC_CHECKOUT_COMPLETION_OLDEST_MODIFIED
            + timedelta(minutes=1)
            + age
        )
    ]


@contextmanager
def completion_in_flight(checkout: Checkout, tick: Callable[[], int]) -> Iterator[None]:
    """Hold the checkout's completion, dispatched by the real tick and not yet run: a message waiting for a worker."""
    with held_publications():
        tick()
        yield


def automatic_completion_sweep() -> DueWorkSweep:
    # ARRANGE: fully paid checkouts, aged into and past Saleor's windows (owed_completion, given_up_completion).
    # REAL PRODUCTION: Saleor's trigger_automatic_checkout_completion_task, its selection observed as it runs.
    # EXTERNAL SEAM: the completion task's Celery dispatch, recorded, and held while one is in flight.
    # OBSERVE: the checkouts each tick dispatched, and every completion dispatched per checkout.
    return DueWorkSweep(
        name="saleor automatic checkout completion",
        due_work=completion_selection,
        run_tick=run_completion_tick,
        make_owed=owed_completion,
        make_terminal=given_up_completion,
        recovery_delay=COMPLETION_DELAY,
        page_size=AUTOMATIC_COMPLETION_BATCH_SIZE,
        assert_scheduled=celery_beat_evidence(
            "saleor.checkout.tasks.trigger_automatic_checkout_completion_task"
        ),
        in_flight=InFlightExecution(
            make_owed=lambda: owed_completion(COMPLETION_DELAY + timedelta(minutes=1)),
            start=completion_in_flight,
            execution_count_for=lambda checkout: COMPLETIONS[checkout.pk],
        ),
        dispatched_ids=lambda: list(DISPATCHED),
        identity_of=lambda checkout: checkout.pk,
    )


CHECKOUT_WITH_AUTOMATIC_COMPLETION = DueWorkContract(
    name="saleor checkout, Transactions API with automatic completion",
    adoption=Adoption.LEGACY,
    transactional=True,
    fixtures=("saleor_shop", "automatic_completion"),
    profiles={
        # Saleor's selection is built inline in its tick, so the sweep observes the query the
        # tick evaluates instead of restating it (selection_built_by).
        Profile.A: Claim(
            gaps={
                "assert_in_flight_work_is_not_duplicated": (
                    "the selection orders by last_automatic_completion_attempt but never excludes a recent one, "
                    "so a paid checkout whose completion is dispatched and not yet run is dispatched again by the "
                    "next tick, a minute later"
                ),
                "assert_outstanding_work_is_observable": (
                    "nothing reports how many fully paid checkouts await automatic completion, so a stalled "
                    "completion task is indistinguishable from an idle one"
                ),
            }
        ),
        Profile.B: Decline(
            "completion serialises on the checkout row lock; it holds no lease"
        ),
        Profile.C: Decline(
            "the payment app charges before completion and records a TransactionItem, so completion makes no "
            "gateway call whose outcome could be unknown"
        ),
        Profile.D: Claim(),
        Profile.E: NotApplicable("one completion writes each order once; no two race"),
        Profile.F: Decline(
            "the obligation is the fully paid checkout itself, which automatic completion selects from product state"
        ),
    },
    safety=SafetyContract(
        name="saleor checkout, Transactions API with automatic completion",
        profiles={
            SafetyProfile.REPLAY_SAFE_EXECUTION: Decline(
                "completing an already completed checkout returns its existing order"
            ),
            SafetyProfile.BOUNDED_RETRY: NotApplicable(
                "automatic completion retries on the beat schedule, unbounded"
            ),
        },
    ),
    sweep=automatic_completion_sweep,
    retention=retention_of_transactions_checkouts,
    handoffs=(COMPLETE_PAID_CHECKOUT,),
    handoff_delivery=SALEOR,
)


# The magic again, for Saleor's other checkout design: the decorator generates this
# class's tests from CHECKOUT_WITH_AUTOMATIC_COMPLETION, bound to the real
# trigger_automatic_checkout_completion_task beat tick, Transactions API money and
# delete_expired_checkouts. Two generated cases are strict XFAILs: the next tick dispatches
# a paid checkout again while its completion is still in flight, and nothing reports how
# many paid checkouts are waiting to be completed.
@due_work_contract_suite(CHECKOUT_WITH_AUTOMATIC_COMPLETION)
class TestCheckoutWithAutomaticCompletion:
    """Saleor's own design: money held as a transaction, and a beat task that completes a paid checkout."""
