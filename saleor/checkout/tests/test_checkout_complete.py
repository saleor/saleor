from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings

from ...account import CustomerEvents
from ...account.models import CustomerEvent
from ...core.exceptions import InsufficientStock
from ...core.notify_events import NotifyEventType
from ...core.taxes import zero_money, zero_taxed_money
from ...discount.models import VoucherCustomer
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCard, GiftCardEvent
from ...order import OrderEvents
from ...order.models import OrderEvent
from ...order.notifications import get_default_order_payload
from ...payment import TransactionKind
from ...payment.models import Payment
from ...plugins.manager import get_plugins_manager
from ...product.models import ProductTranslation, ProductVariantTranslation
from ...tests.utils import flush_post_commit_hooks
from .. import calculations
from ..complete_checkout import (
    _create_order,
    _prepare_order_data,
    _process_shipping_data_for_order,
    complete_checkout,
)
from ..fetch import fetch_checkout_info, fetch_checkout_lines
from ..utils import add_variant_to_checkout


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_create_order_captured_payment_creates_expected_events(
    mock_notify,
    checkout_with_item,
    customer_user,
    shipping_method,
    payment_txn_captured,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_user = customer_user

    # Ensure not events are existing prior
    assert not OrderEvent.objects.exists()
    assert not CustomerEvent.objects.exists()

    # Prepare valid checkout
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_shipping_address
    checkout.shipping_method = shipping_method
    checkout.payments.add(payment_txn_captured)
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    # Place checkout
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=[],
            taxes_included_in_prices=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )
    flush_post_commit_hooks()

    (
        order_placed_event,
        payment_captured_event,
        order_fully_paid_event,
        order_confirmed_event,
    ) = order.events.all()  # type: OrderEvent

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_placed_event.type == OrderEvents.PLACED
    # is the user anonymous/ the customer
    assert order_placed_event.user == checkout_user
    # is the associated backref order valid
    assert order_placed_event.order is order
    # ensure a date was set
    assert order_placed_event.date
    # should not have any additional parameters
    assert not order_placed_event.parameters

    # Ensure the correct order event was created
    # is the event the expected type
    assert payment_captured_event.type == OrderEvents.PAYMENT_CAPTURED
    # is the user anonymous/ the customer
    assert payment_captured_event.user == checkout_user
    # is the associated backref order valid
    assert payment_captured_event.order is order
    # ensure a date was set
    assert payment_captured_event.date
    # should not have any additional parameters
    assert "amount" in payment_captured_event.parameters.keys()
    assert "payment_id" in payment_captured_event.parameters.keys()
    assert "payment_gateway" in payment_captured_event.parameters.keys()

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_fully_paid_event.type == OrderEvents.ORDER_FULLY_PAID
    # is the user anonymous/ the customer
    assert order_fully_paid_event.user == checkout_user
    # is the associated backref order valid
    assert order_fully_paid_event.order is order
    # ensure a date was set
    assert order_fully_paid_event.date
    # should not have any additional parameters
    assert not order_fully_paid_event.parameters

    expected_order_payload = {
        "order": get_default_order_payload(order, checkout.redirect_url),
        "recipient_email": order.get_customer_email(),
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }

    expected_payment_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "payment": {
            "created": payment_txn_captured.created_at,
            "modified": payment_txn_captured.modified_at,
            "charge_status": payment_txn_captured.charge_status,
            "total": payment_txn_captured.total,
            "captured_amount": payment_txn_captured.captured_amount,
            "currency": payment_txn_captured.currency,
        },
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }
    # Ensure the correct order confirmed event was created
    # should be order confirmed event
    assert order_confirmed_event.type == OrderEvents.CONFIRMED
    # ensure the user is checkout user
    assert order_confirmed_event.user == checkout_user
    # ensure the order confirmed event is related to order
    assert order_confirmed_event.order is order
    # ensure a date was set
    assert order_confirmed_event.date
    # ensure the event parameters are empty
    assert order_confirmed_event.parameters == {}

    mock_notify.assert_has_calls(
        [
            mock.call(
                NotifyEventType.ORDER_CONFIRMATION,
                expected_order_payload,
                channel_slug=channel_USD.slug,
            ),
            mock.call(
                NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
                expected_payment_payload,
                channel_slug=channel_USD.slug,
            ),
        ],
        any_order=True,
    )

    # Ensure the correct customer event was created if the user was not anonymous
    placement_event = customer_user.events.get()  # type: CustomerEvent
    assert placement_event.type == CustomerEvents.PLACED_ORDER  # check the event type
    assert placement_event.user == customer_user  # check the backref is valid
    assert placement_event.order == order  # check the associated order is valid
    assert placement_event.date  # ensure a date was set
    assert not placement_event.parameters  # should not have any additional parameters


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_create_order_captured_payment_creates_expected_events_anonymous_user(
    mock_notify,
    checkout_with_item,
    customer_user,
    shipping_method,
    payment_txn_captured,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_user = None

    # Ensure not events are existing prior
    assert not OrderEvent.objects.exists()
    assert not CustomerEvent.objects.exists()

    # Prepare valid checkout
    checkout.user = checkout_user
    checkout.email = "test@example.com"
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_shipping_address
    checkout.shipping_method = shipping_method
    checkout.payments.add(payment_txn_captured)
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    # Place checkout
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=None,
            taxes_included_in_prices=True,
        ),
        user=AnonymousUser(),
        app=None,
        manager=manager,
    )
    flush_post_commit_hooks()

    (
        order_placed_event,
        payment_captured_event,
        order_fully_paid_event,
        order_confirmed_event,
    ) = order.events.all()  # type: OrderEvent

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_placed_event.type == OrderEvents.PLACED
    # is the user anonymous/ the customer
    assert order_placed_event.user == checkout_user
    # is the associated backref order valid
    assert order_placed_event.order is order
    # ensure a date was set
    assert order_placed_event.date
    # should not have any additional parameters
    assert not order_placed_event.parameters

    # Ensure the correct order event was created
    # is the event the expected type
    assert payment_captured_event.type == OrderEvents.PAYMENT_CAPTURED
    # is the user anonymous/ the customer
    assert payment_captured_event.user == checkout_user
    # is the associated backref order valid
    assert payment_captured_event.order is order
    # ensure a date was set
    assert payment_captured_event.date
    # should not have any additional parameters
    assert "amount" in payment_captured_event.parameters.keys()
    assert "payment_id" in payment_captured_event.parameters.keys()
    assert "payment_gateway" in payment_captured_event.parameters.keys()

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_fully_paid_event.type == OrderEvents.ORDER_FULLY_PAID
    # is the user anonymous/ the customer
    assert order_fully_paid_event.user == checkout_user
    # is the associated backref order valid
    assert order_fully_paid_event.order is order
    # ensure a date was set
    assert order_fully_paid_event.date
    # should not have any additional parameters
    assert not order_fully_paid_event.parameters

    expected_order_payload = {
        "order": get_default_order_payload(order, checkout.redirect_url),
        "recipient_email": order.get_customer_email(),
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }

    expected_payment_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "payment": {
            "created": payment_txn_captured.created_at,
            "modified": payment_txn_captured.modified_at,
            "charge_status": payment_txn_captured.charge_status,
            "total": payment_txn_captured.total,
            "captured_amount": payment_txn_captured.captured_amount,
            "currency": payment_txn_captured.currency,
        },
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }

    # Ensure the correct order confirmed event was created
    # should be order confirmed event
    assert order_confirmed_event.type == OrderEvents.CONFIRMED
    # ensure the user is checkout user
    assert order_confirmed_event.user == checkout_user
    # ensure the order confirmed event is related to order
    assert order_confirmed_event.order is order
    # ensure a date was set
    assert order_confirmed_event.date
    # ensure the event parameters are empty
    assert order_confirmed_event.parameters == {}

    mock_notify.assert_has_calls(
        [
            mock.call(
                NotifyEventType.ORDER_CONFIRMATION,
                expected_order_payload,
                channel_slug=channel_USD.slug,
            ),
            mock.call(
                NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
                expected_payment_payload,
                channel_slug=channel_USD.slug,
            ),
        ],
        any_order=True,
    )

    # Check no event was created if the user was anonymous
    assert not CustomerEvent.objects.exists()  # should not have created any event


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_create_order_preauth_payment_creates_expected_events(
    mock_notify,
    checkout_with_item,
    customer_user,
    shipping_method,
    payment_txn_preauth,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_user = customer_user

    # Ensure not events are existing prior
    assert not OrderEvent.objects.exists()
    assert not CustomerEvent.objects.exists()

    # Prepare valid checkout
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_shipping_address
    checkout.shipping_method = shipping_method
    checkout.payments.add(payment_txn_preauth)
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    # Place checkout
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=[],
            taxes_included_in_prices=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )
    flush_post_commit_hooks()

    (
        order_placed_event,
        payment_authorized_event,
        order_confirmed_event,
    ) = order.events.all()  # type: OrderEvent

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_placed_event.type == OrderEvents.PLACED
    # is the user anonymous/ the customer
    assert order_placed_event.user == checkout_user
    # is the associated backref order valid
    assert order_placed_event.order is order
    # ensure a date was set
    assert order_placed_event.date
    # should not have any additional parameters
    assert not order_placed_event.parameters

    # Ensure the correct order event was created
    # is the event the expected type
    assert payment_authorized_event.type == OrderEvents.PAYMENT_AUTHORIZED
    # is the user anonymous/ the customer
    assert payment_authorized_event.user == checkout_user
    # is the associated backref order valid
    assert payment_authorized_event.order is order
    # ensure a date was set
    assert payment_authorized_event.date
    # should not have any additional parameters
    assert "amount" in payment_authorized_event.parameters.keys()
    assert "payment_id" in payment_authorized_event.parameters.keys()
    assert "payment_gateway" in payment_authorized_event.parameters.keys()

    expected_payload = {
        "order": get_default_order_payload(order, checkout.redirect_url),
        "recipient_email": order.get_customer_email(),
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }

    # Ensure the correct order confirmed event was created
    # should be order confirmed event
    assert order_confirmed_event.type == OrderEvents.CONFIRMED
    # ensure the user is checkout user
    assert order_confirmed_event.user == checkout_user
    # ensure the order confirmed event is related to order
    assert order_confirmed_event.order is order
    # ensure a date was set
    assert order_confirmed_event.date
    # ensure the event parameters are empty
    assert order_confirmed_event.parameters == {}

    mock_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMATION,
        expected_payload,
        channel_slug=channel_USD.slug,
    )

    # Ensure the correct customer event was created if the user was not anonymous
    placement_event = customer_user.events.get()  # type: CustomerEvent
    assert placement_event.type == CustomerEvents.PLACED_ORDER  # check the event type
    assert placement_event.user == customer_user  # check the backref is valid
    assert placement_event.order == order  # check the associated order is valid
    assert placement_event.date  # ensure a date was set
    assert not placement_event.parameters  # should not have any additional parameters


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_create_order_preauth_payment_creates_expected_events_anonymous_user(
    mock_notify,
    checkout_with_item,
    customer_user,
    shipping_method,
    payment_txn_preauth,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_user = None

    # Ensure not events are existing prior
    assert not OrderEvent.objects.exists()
    assert not CustomerEvent.objects.exists()

    # Prepare valid checkout
    checkout.user = checkout_user
    checkout.email = "test@example.com"
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_shipping_address
    checkout.shipping_method = shipping_method
    checkout.payments.add(payment_txn_preauth)
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    # Place checkout
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=[],
            taxes_included_in_prices=True,
        ),
        user=AnonymousUser(),
        app=None,
        manager=manager,
    )
    flush_post_commit_hooks()

    (
        order_placed_event,
        payment_captured_event,
        order_confirmed_event,
    ) = order.events.all()  # type: OrderEvent

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_placed_event.type == OrderEvents.PLACED
    # is the user anonymous/ the customer
    assert order_placed_event.user == checkout_user
    # is the associated backref order valid
    assert order_placed_event.order is order
    # ensure a date was set
    assert order_placed_event.date
    # should not have any additional parameters
    assert not order_placed_event.parameters

    # Ensure the correct order event was created
    # is the event the expected type
    assert payment_captured_event.type == OrderEvents.PAYMENT_AUTHORIZED
    # is the user anonymous/ the customer
    assert payment_captured_event.user == checkout_user
    # is the associated backref order valid
    assert payment_captured_event.order is order
    # ensure a date was set
    assert payment_captured_event.date
    # should not have any additional parameters
    assert "amount" in payment_captured_event.parameters.keys()
    assert "payment_id" in payment_captured_event.parameters.keys()
    assert "payment_gateway" in payment_captured_event.parameters.keys()

    expected_payload = {
        "order": get_default_order_payload(order, checkout.redirect_url),
        "recipient_email": order.get_customer_email(),
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }
    # Ensure the correct order confirmed event was created
    # should be order confirmed event
    assert order_confirmed_event.type == OrderEvents.CONFIRMED
    # ensure the user is checkout user
    assert order_confirmed_event.user == checkout_user
    # ensure the order confirmed event is related to order
    assert order_confirmed_event.order is order
    # ensure a date was set
    assert order_confirmed_event.date
    # ensure the event parameters are empty
    assert order_confirmed_event.parameters == {}

    mock_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMATION,
        expected_payload,
        channel_slug=channel_USD.slug,
    )

    # Check no event was created if the user was anonymous
    assert not CustomerEvent.objects.exists()  # should not have created any event


def test_create_order_insufficient_stock(
    checkout, customer_user, product_without_shipping
):
    variant = product_without_shipping.variants.get()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)

    add_variant_to_checkout(checkout_info, variant, 10, check_quantity=False)
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = "tracking_code"
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    with pytest.raises(InsufficientStock):
        _prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=[],
            taxes_included_in_prices=True,
        )


def test_create_order_doesnt_duplicate_order(
    checkout_with_item, customer_user, shipping_method
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    order_data = _prepare_order_data(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        discounts=[],
        taxes_included_in_prices=True,
    )

    order_1 = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=order_data,
        user=customer_user,
        app=None,
        manager=manager,
    )
    assert order_1.checkout_token == str(checkout.token)

    order_2 = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=order_data,
        user=customer_user,
        app=None,
        manager=manager,
    )
    assert order_1.pk == order_2.pk


@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_with_gift_card(
    checkout_with_gift_card, customer_user, shipping_method, is_anonymous_user
):
    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross_without_gift_cards = (
        subtotal.gross + shipping_price.gross - checkout.discount
    )
    gift_cards_balance = checkout.get_total_gift_cards_balance()

    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=None,
            taxes_included_in_prices=True,
        ),
        user=customer_user if not is_anonymous_user else AnonymousUser(),
        app=None,
        manager=manager,
    )

    assert order.gift_cards.count() == 1
    gift_card = order.gift_cards.first()
    assert gift_card.current_balance.amount == 0
    assert order.total.gross == (total_gross_without_gift_cards - gift_cards_balance)
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


def test_create_order_with_gift_card_partial_use(
    checkout_with_item, gift_card_used, customer_user, shipping_method
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    price_without_gift_card = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    gift_card_balance_before_order = gift_card_used.current_balance_amount

    checkout.gift_cards.add(gift_card_used)
    checkout.save()

    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=[],
            taxes_included_in_prices=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )

    gift_card_used.refresh_from_db()

    expected_old_balance = (
        price_without_gift_card.gross.amount + gift_card_used.current_balance_amount
    )

    assert order.gift_cards.count() > 0
    assert order.total == zero_taxed_money(order.currency)
    assert gift_card_balance_before_order == expected_old_balance
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card_used, type=GiftCardEvents.USED_IN_ORDER
    )


def test_create_order_with_many_gift_cards(
    checkout_with_item,
    gift_card_created_by_staff,
    gift_card,
    customer_user,
    shipping_method,
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    price_without_gift_card = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    gift_cards_balance_before_order = (
        gift_card_created_by_staff.current_balance.amount
        + gift_card.current_balance.amount
    )

    checkout.gift_cards.add(gift_card_created_by_staff)
    checkout.gift_cards.add(gift_card)
    checkout.save()

    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=[],
            taxes_included_in_prices=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )

    gift_card_created_by_staff.refresh_from_db()
    gift_card.refresh_from_db()
    zero_price = zero_money(gift_card.currency)
    assert order.gift_cards.count() > 0
    assert gift_card_created_by_staff.current_balance == zero_price
    assert gift_card.current_balance == zero_price
    assert price_without_gift_card.gross.amount == (
        gift_cards_balance_before_order + order.total.gross.amount
    )
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card_created_by_staff, type=GiftCardEvents.USED_IN_ORDER
    )
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


@mock.patch("saleor.giftcard.utils.send_gift_card_notification")
@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_gift_card_bought(
    send_notification_mock,
    checkout_with_gift_card_items,
    payment_txn_captured,
    customer_user,
    shipping_method,
    is_anonymous_user,
    non_shippable_gift_card_product,
):
    """Ensure that the gift cards will be fulfilled, when newly created order
    is captured."""
    # given
    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card_items
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    amount = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, customer_user.default_billing_address
    ).gross.amount

    payment_txn_captured.order = None
    payment_txn_captured.checkout = checkout
    payment_txn_captured.captured_amount = amount
    payment_txn_captured.total = amount
    payment_txn_captured.save(
        update_fields=["order", "checkout", "total", "captured_amount"]
    )

    txn = payment_txn_captured.transactions.first()
    txn.amount = amount
    txn.save(update_fields=["amount"])

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross = subtotal.gross + shipping_price.gross - checkout.discount

    # when
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=None,
            taxes_included_in_prices=True,
        ),
        user=customer_user if not is_anonymous_user else AnonymousUser(),
        app=None,
        manager=manager,
    )

    # then
    flush_post_commit_hooks()
    assert order.total.gross == total_gross
    flush_post_commit_hooks()
    gift_card = GiftCard.objects.get()
    assert (
        gift_card.initial_balance
        == order.lines.get(
            variant=non_shippable_gift_card_product.variants.first()
        ).unit_price_gross
    )
    assert GiftCardEvent.objects.filter(gift_card=gift_card, type=GiftCardEvents.BOUGHT)
    flush_post_commit_hooks()
    send_notification_mock.assert_called_once_with(
        checkout_user,
        None,
        checkout_user,
        order.user_email,
        gift_card,
        manager,
        order.channel.slug,
        resending=False,
    )


@mock.patch("saleor.giftcard.utils.send_gift_card_notification")
@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_gift_card_bought_order_not_captured_gift_cards_not_sent(
    send_notification_mock,
    checkout_with_gift_card_items,
    customer_user,
    shipping_method,
    is_anonymous_user,
):
    """Ensure that the gift cards will be not fulfilled, when newly created order
    is not captured."""
    # given
    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card_items
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross = subtotal.gross + shipping_price.gross - checkout.discount

    # when
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=None,
            taxes_included_in_prices=True,
        ),
        user=customer_user if not is_anonymous_user else AnonymousUser(),
        app=None,
        manager=manager,
    )

    # then
    flush_post_commit_hooks()
    flush_post_commit_hooks()
    assert order.total.gross == total_gross
    assert not GiftCard.objects.exists()
    send_notification_mock.assert_not_called()


@mock.patch("saleor.giftcard.utils.send_gift_card_notification")
@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_gift_card_bought_only_shippable_gift_card(
    send_notification_mock,
    checkout,
    shippable_gift_card_product,
    customer_user,
    shipping_method,
    is_anonymous_user,
):
    checkout_user = None if is_anonymous_user else customer_user
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    shippable_variant = shippable_gift_card_product.variants.get()
    add_variant_to_checkout(checkout_info, shippable_variant, 2)

    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross = subtotal.gross + shipping_price.gross - checkout.discount

    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=None,
            taxes_included_in_prices=True,
        ),
        user=customer_user if not is_anonymous_user else AnonymousUser(),
        app=None,
        manager=manager,
    )

    assert order.total.gross == total_gross
    assert not GiftCard.objects.all()
    send_notification_mock.assert_not_called()


@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_gift_card_bought_do_not_fulfill_gift_cards_automatically(
    site_settings,
    checkout_with_gift_card_items,
    customer_user,
    shipping_method,
    is_anonymous_user,
    non_shippable_gift_card_product,
):
    site_settings.automatically_fulfill_non_shippable_gift_card = False
    site_settings.save(update_fields=["automatically_fulfill_non_shippable_gift_card"])

    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card_items
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross = subtotal.gross + shipping_price.gross - checkout.discount

    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=None,
            taxes_included_in_prices=True,
        ),
        user=customer_user if not is_anonymous_user else AnonymousUser(),
        app=None,
        manager=manager,
    )

    assert order.total.gross == total_gross
    assert not GiftCard.objects.all()


def test_note_in_created_order(checkout_with_item, address, customer_user):
    checkout_with_item.shipping_address = address
    checkout_with_item.note = "test_note"
    checkout_with_item.tracking_code = "tracking_code"
    checkout_with_item.redirect_url = "https://www.example.com"
    checkout_with_item.save()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=[],
            taxes_included_in_prices=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )
    assert order.customer_note == checkout_with_item.note


def test_create_order_with_variant_tracking_false(
    checkout, customer_user, variant_without_inventory_tracking
):
    variant = variant_without_inventory_tracking
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.save()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    add_variant_to_checkout(checkout_info, variant, 10, check_quantity=False)

    lines, _ = fetch_checkout_lines(checkout)
    order_data = _prepare_order_data(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        discounts=[],
        taxes_included_in_prices=True,
    )

    order_1 = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=order_data,
        user=customer_user,
        app=None,
        manager=manager,
    )
    assert order_1.checkout_token == str(checkout.token)


@override_settings(LANGUAGE_CODE="fr")
def test_create_order_use_translations(
    checkout_with_item, customer_user, shipping_method
):
    translated_product_name = "French name"
    translated_variant_name = "French variant name"

    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.language_code = "fr"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    variant = lines[0].variant
    product = lines[0].product

    ProductTranslation.objects.create(
        language_code="fr",
        product=product,
        name=translated_product_name,
    )
    ProductVariantTranslation.objects.create(
        language_code="fr",
        product_variant=variant,
        name=translated_variant_name,
    )

    order_data = _prepare_order_data(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        discounts=[],
        taxes_included_in_prices=True,
    )
    order_line = order_data["lines"][0].line

    assert order_line.translated_product_name == translated_product_name
    assert order_line.translated_variant_name == translated_variant_name


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_complete_checkout_0_total_captured_payment_creates_expected_events(
    mock_notify, checkout_with_item_total_0, customer_user, channel_USD, app
):
    checkout = checkout_with_item_total_0
    checkout_user = customer_user

    # Ensure not events are existing prior
    assert not OrderEvent.objects.exists()
    assert not CustomerEvent.objects.exists()

    # Prepare valid checkout
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    # Place checkout
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    order, action_required, action_data = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        discounts=None,
        user=customer_user,
        app=app,
    )

    flush_post_commit_hooks()
    (
        order_marked_as_paid,
        order_placed_event,
        order_confirmed_event,
    ) = order.events.all()  # type: OrderEvent

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_placed_event.type == OrderEvents.PLACED
    # is the user anonymous/ the customer
    assert order_placed_event.user == checkout_user
    # is the associated backref order valid
    assert order_placed_event.order is order
    # ensure a date was set
    assert order_placed_event.date
    # should not have any additional parameters
    assert not order_placed_event.parameters

    # Ensure the correct order event was created
    # is the event the expected type
    assert order_marked_as_paid.type == OrderEvents.ORDER_MARKED_AS_PAID
    # is the user anonymous/ the customer
    assert order_marked_as_paid.user == checkout_user
    # is the associated backref order valid
    assert order_marked_as_paid.order is order
    # ensure a date was set
    assert order_marked_as_paid.date
    # should not have any additional parameters
    assert not order_marked_as_paid.parameters

    expected_order_payload = {
        "order": get_default_order_payload(order, checkout.redirect_url),
        "recipient_email": order.get_customer_email(),
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }

    # Ensure the correct order confirmed event was created
    # should be order confirmed event
    assert order_confirmed_event.type == OrderEvents.CONFIRMED
    # ensure the user is checkout user
    assert order_confirmed_event.user == checkout_user
    # ensure the order confirmed event is related to order
    assert order_confirmed_event.order is order
    # ensure a date was set
    assert order_confirmed_event.date
    # ensure the event parameters are empty
    assert order_confirmed_event.parameters == {}

    mock_notify.assert_has_calls(
        [
            mock.call(
                NotifyEventType.ORDER_CONFIRMATION,
                expected_order_payload,
                channel_slug=channel_USD.slug,
            )
        ],
        any_order=True,
    )

    # Ensure the correct customer event was created if the user was not anonymous
    placement_event = customer_user.events.get()  # type: CustomerEvent
    assert placement_event.type == CustomerEvents.PLACED_ORDER  # check the event type
    assert placement_event.user == customer_user  # check the backref is valid
    assert placement_event.order == order  # check the associated order is valid
    assert placement_event.date  # ensure a date was set
    assert not placement_event.parameters  # should not have any additional parameters


@mock.patch("saleor.checkout.complete_checkout._create_order")
@mock.patch(
    "saleor.checkout.complete_checkout._process_payment",
)
def test_complete_checkout_action_required_voucher_once_per_customer(
    mocked_process_payment,
    mocked_create_order,
    voucher,
    customer_user,
    checkout,
    app,
    payment_txn_to_confirm,
    action_required_gateway_response,
):
    # given
    mocked_process_payment.return_value = action_required_gateway_response

    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy", is_active=True, checkout=checkout
    )
    payment.to_confirm = True
    payment.save()

    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.voucher_code = voucher.code
    checkout.save()

    voucher.apply_once_per_customer = True
    voucher.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        discounts=None,
        user=customer_user,
        app=app,
    )
    # then
    voucher_customer = VoucherCustomer.objects.filter(
        voucher=voucher, customer_email=customer_user.email
    )
    assert not order
    assert action_required is True
    assert not voucher_customer.exists()
    mocked_create_order.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout._create_order")
def test_complete_checkout_order_not_created_when_the_refund_is_ongoing(
    mocked_create_order,
    customer_user,
    checkout,
    payment_txn_to_confirm,
):
    # given
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy", is_active=True, checkout=checkout
    )
    payment.to_confirm = False
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=False,
        kind=TransactionKind.REFUND_ONGOING,
        amount=payment.total,
        currency=payment.currency,
        token="test",
        gateway_response={},
    )

    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    order, _, _ = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        discounts=None,
        user=customer_user,
        app=None,
    )

    # then
    assert not order
    mocked_create_order.assert_not_called()


def test_process_shipping_data_for_order_store_customer_shipping_address(
    checkout_with_item, customer_user, address_usa, shipping_method
):
    # given
    checkout = checkout_with_item

    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = address_usa
    checkout.shipping_method = shipping_method
    checkout.save()

    user_address_count = customer_user.addresses.count()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    shipping_price = zero_taxed_money(checkout.currency)

    # when
    _ = _process_shipping_data_for_order(checkout_info, shipping_price, manager, lines)

    # then
    new_user_address_count = customer_user.addresses.count()
    new_address_data = address_usa.as_data()
    assert new_user_address_count == user_address_count + 1
    assert customer_user.addresses.filter(**new_address_data).exists()


def test_process_shipping_data_for_order_dont_store_customer_click_and_collect_address(
    checkout_with_item_for_cc, customer_user, address_usa, warehouse_for_cc
):
    # given
    checkout = checkout_with_item_for_cc

    warehouse_for_cc.address = address_usa
    warehouse_for_cc.save()

    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = None
    checkout.collection_point = warehouse_for_cc
    checkout.save()

    user_address_count = customer_user.addresses.count()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    shipping_price = zero_taxed_money(checkout.currency)

    # when
    _ = _process_shipping_data_for_order(checkout_info, shipping_price, manager, lines)

    # then
    new_user_address_count = customer_user.addresses.count()
    new_address_data = warehouse_for_cc.address.as_data()
    assert new_user_address_count == user_address_count
    assert not customer_user.addresses.filter(**new_address_data).exists()
