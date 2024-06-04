from datetime import timedelta
from decimal import Decimal
from unittest import mock

import before_after
import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone
from prices import TaxedMoney

from ...account import CustomerEvents
from ...account.models import CustomerEvent
from ...channel import MarkAsPaidStrategy
from ...checkout import CheckoutAuthorizeStatus
from ...core.exceptions import InsufficientStock
from ...core.notify_events import NotifyEventType
from ...core.taxes import zero_money, zero_taxed_money
from ...core.tests.utils import get_site_context_payload
from ...discount.models import VoucherCustomer
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCard, GiftCardEvent
from ...order import OrderAuthorizeStatus, OrderChargeStatus, OrderEvents
from ...order.models import OrderEvent
from ...order.notifications import get_default_order_payload
from ...payment import TransactionKind
from ...payment.interface import GatewayResponse
from ...payment.models import Payment
from ...plugins.manager import get_plugins_manager
from ...product.models import ProductTranslation, ProductVariantTranslation
from ...tests.utils import flush_post_commit_hooks
from .. import calculations
from ..complete_checkout import (
    _complete_checkout_fail_handler,
    _create_order,
    _increase_checkout_voucher_usage,
    _prepare_order_data,
    _process_shipping_data_for_order,
    _release_checkout_voucher_usage,
    complete_checkout,
)
from ..fetch import fetch_checkout_info, fetch_checkout_lines
from ..models import Checkout
from ..payment_utils import update_checkout_payment_statuses
from ..utils import add_variant_to_checkout


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_create_order_captured_payment_creates_expected_events(
    mock_notify,
    checkout_with_item,
    customer_user,
    shipping_method,
    payment_txn_captured,
    channel_USD,
    site_settings,
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=True,
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
    # should have additional parameters
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
    # should have payment_gateway in additional parameters
    assert "payment_gateway" in order_fully_paid_event.parameters

    expected_order_payload = {
        "order": get_default_order_payload(order, checkout.redirect_url),
        "recipient_email": order.get_customer_email(),
        **get_site_context_payload(site_settings.site),
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
        **get_site_context_payload(site_settings.site),
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
    site_settings,
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=True,
        ),
        user=None,
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
    # should have additional parameters
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
    # should have payment_gateway in additional parameters
    assert "payment_gateway" in order_fully_paid_event.parameters

    expected_order_payload = {
        "order": get_default_order_payload(order, checkout.redirect_url),
        "recipient_email": order.get_customer_email(),
        **get_site_context_payload(site_settings.site),
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
        **get_site_context_payload(site_settings.site),
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
    site_settings,
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=True,
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
        **get_site_context_payload(site_settings.site),
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
    site_settings,
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=True,
        ),
        user=None,
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
        **get_site_context_payload(site_settings.site),
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
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)

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
            prices_entered_with_tax=True,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    order_data = _prepare_order_data(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        prices_entered_with_tax=True,
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


@pytest.mark.parametrize("is_anonymous_user", [True, False])
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
            prices_entered_with_tax=True,
        ),
        user=customer_user if not is_anonymous_user else None,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
            prices_entered_with_tax=True,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
            prices_entered_with_tax=True,
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
@pytest.mark.parametrize("is_anonymous_user", [True, False])
def test_create_order_gift_card_bought(
    send_notification_mock,
    checkout_with_gift_card_items,
    payment_txn_captured,
    customer_user,
    shipping_method,
    is_anonymous_user,
    non_shippable_gift_card_product,
):
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
            prices_entered_with_tax=True,
        ),
        user=customer_user if not is_anonymous_user else None,
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
@pytest.mark.parametrize("is_anonymous_user", [True, False])
def test_create_order_gift_card_bought_order_not_captured_gift_cards_not_sent(
    send_notification_mock,
    checkout_with_gift_card_items,
    customer_user,
    shipping_method,
    is_anonymous_user,
):
    """Check that digital gift cards are not issued if the payment is not captured."""
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
            prices_entered_with_tax=True,
        ),
        user=customer_user if not is_anonymous_user else None,
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
@pytest.mark.parametrize("is_anonymous_user", [True, False])
def test_create_order_gift_card_bought_only_shippable_gift_card(
    send_notification_mock,
    checkout,
    shippable_gift_card_product,
    customer_user,
    shipping_method,
    is_anonymous_user,
):
    checkout_user = None if is_anonymous_user else customer_user
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    shippable_variant = shippable_gift_card_product.variants.get()
    add_variant_to_checkout(checkout_info, shippable_variant, 2)

    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
            prices_entered_with_tax=True,
        ),
        user=customer_user if not is_anonymous_user else None,
        app=None,
        manager=manager,
    )

    assert order.total.gross == total_gross
    assert not GiftCard.objects.all()
    send_notification_mock.assert_not_called()


@pytest.mark.parametrize("is_anonymous_user", [True, False])
def test_create_order_gift_card_bought_do_not_fulfill_gift_cards_automatically(
    site_settings,
    checkout_with_gift_card_items,
    customer_user,
    shipping_method,
    is_anonymous_user,
    non_shippable_gift_card_product,
):
    channel = checkout_with_gift_card_items.channel
    channel.automatically_fulfill_non_shippable_gift_card = False
    channel.save()

    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card_items
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
            prices_entered_with_tax=True,
        ),
        user=customer_user if not is_anonymous_user else None,
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
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=True,
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
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, variant, 10, check_quantity=False)

    lines, _ = fetch_checkout_lines(checkout)
    order_data = _prepare_order_data(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        prices_entered_with_tax=True,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
        prices_entered_with_tax=True,
    )
    order_line = order_data["lines"][0].line

    assert order_line.translated_product_name == translated_product_name
    assert order_line.translated_variant_name == translated_variant_name


def test_complete_checkout_0_total_with_transaction_for_mark_as_paid(
    checkout_with_item_total_0,
    customer_user,
    app,
):
    # given
    checkout = checkout_with_item_total_0

    channel = checkout.channel
    channel.order_mark_as_paid_strategy = MarkAsPaidStrategy.TRANSACTION_FLOW
    channel.save(update_fields=["order_mark_as_paid_strategy"])

    checkout.billing_address = customer_user.default_billing_address
    checkout.save()

    update_checkout_payment_statuses(
        checkout, zero_money(checkout.currency), checkout_has_lines=True
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order, _, _ = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=app,
    )

    # then
    flush_post_commit_hooks()

    assert order
    assert order.authorize_status == OrderAuthorizeStatus.FULL
    assert order.charge_status == OrderChargeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_complete_checkout_0_total_captured_payment_creates_expected_events(
    mock_notify,
    checkout_with_item_total_0,
    customer_user,
    channel_USD,
    app,
    site_settings,
):
    checkout = checkout_with_item_total_0
    checkout_user = customer_user

    channel = checkout.channel
    channel.order_mark_as_paid_strategy = MarkAsPaidStrategy.PAYMENT_FLOW
    channel.save(update_fields=["order_mark_as_paid_strategy"])

    # Ensure not events are existing prior
    assert not OrderEvent.objects.exists()
    assert not CustomerEvent.objects.exists()

    # Prepare valid checkout
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    # Place checkout
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    order, action_required, action_data = complete_checkout(
        checkout_info=checkout_info,
        lines=lines,
        manager=manager,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=app,
    )

    flush_post_commit_hooks()
    (
        order_marked_as_paid,
        order_placed_event,
        order_fully_paid,
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
        **get_site_context_payload(site_settings.site),
    }

    assert order_fully_paid.type == OrderEvents.ORDER_FULLY_PAID
    assert order_fully_paid.user == checkout_user

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
@mock.patch("saleor.checkout.complete_checkout._process_payment")
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

    voucher_code = voucher.codes.first()

    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.voucher_code = voucher_code.code
    checkout.save()

    voucher.apply_once_per_customer = True
    voucher.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        lines=lines,
        manager=manager,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=app,
    )
    # then
    voucher_customer = VoucherCustomer.objects.filter(
        voucher_code=voucher_code, customer_email=customer_user.email
    )
    assert not order

    assert action_required is True
    assert not voucher_customer.exists()
    mocked_create_order.assert_not_called()
    checkout.refresh_from_db()
    assert checkout.is_voucher_usage_increased is False


@mock.patch("saleor.checkout.complete_checkout._create_order")
@mock.patch("saleor.checkout.complete_checkout._process_payment")
def test_complete_checkout_action_required_voucher_single_use(
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

    code = voucher.codes.first()

    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.voucher_code = code.code
    checkout.save()

    voucher.single_use = True
    voucher.save(update_fields=["single_use"])

    assert code.is_active

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        lines=lines,
        manager=manager,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=app,
    )

    # then
    voucher_customer = VoucherCustomer.objects.filter(
        voucher_code=code, customer_email=customer_user.email
    )
    assert not order
    assert action_required is True
    assert not voucher_customer.exists()
    mocked_create_order.assert_not_called()
    checkout.refresh_from_db()
    assert checkout.is_voucher_usage_increased is False
    checkout.refresh_from_db()
    assert not checkout.completing_started_at

    code.refresh_from_db()
    assert code.is_active is True

    checkout.refresh_from_db()
    assert checkout.is_voucher_usage_increased is False


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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order, _, _ = complete_checkout(
        checkout_info=checkout_info,
        lines=lines,
        manager=manager,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
    )

    # then
    assert not order
    mocked_create_order.assert_not_called()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@mock.patch("saleor.checkout.complete_checkout._create_order")
def test_complete_checkout_when_checkout_doesnt_exists(
    mocked_create_order,
    customer_user,
    checkout,
    payment_txn_to_confirm,
    order,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    order.checkout_token = checkout.token
    order.save()
    Checkout.objects.filter(token=checkout.token).delete()

    # when
    order_from_checkout, _, _ = complete_checkout(
        checkout_info=checkout_info,
        lines=lines,
        manager=manager,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
    )

    # then

    assert order.pk == order_from_checkout.pk
    mocked_create_order.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout._create_order")
@mock.patch("saleor.checkout.complete_checkout._process_payment")
def test_complete_checkout_checkout_was_deleted_before_completing(
    mocked_process_payment,
    mocked_create_order,
    customer_user,
    checkout,
    app,
    payment_txn_to_confirm,
    action_required_gateway_response,
    order,
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
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    def convert_checkout_to_order(*args, **kwargs):
        order.checkout_token = checkout.token
        order.save()
        Checkout.objects.filter(token=checkout.token).delete()

    with before_after.after(
        "saleor.checkout.complete_checkout._process_payment", convert_checkout_to_order
    ):
        order_from_checkout, action_required, _ = complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=app,
        )
    # then
    assert order.pk == order_from_checkout.pk
    assert action_required is False
    mocked_create_order.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
@mock.patch("saleor.checkout.complete_checkout._process_payment")
def test_complete_checkout_checkout_limited_use_voucher_multiple_thread(
    mocked_process_payment,
    mocked_payment_refund_or_void,
    customer_user,
    checkout_with_voucher_free_shipping,
    voucher_free_shipping,
    app,
    success_gateway_response,
):
    # given
    checkout = checkout_with_voucher_free_shipping
    address = customer_user.default_billing_address
    checkout.user = customer_user
    checkout.billing_address = address
    checkout.shipping_address = address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    voucher_free_shipping.usage_limit = 1
    voucher_free_shipping.save(update_fields=["usage_limit"])

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        checkout=checkout,
        total=total.gross.amount,
    )
    mocked_process_payment.return_value = success_gateway_response

    # when
    def call_checkout_complete(*args, **kwargs):
        lines_2, _ = fetch_checkout_lines(checkout)
        checkout_info_2 = fetch_checkout_info(checkout, lines, manager)
        complete_checkout(
            checkout_info=checkout_info_2,
            lines=lines_2,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=app,
        )

    with before_after.after(
        "saleor.checkout.complete_checkout._process_payment", call_checkout_complete
    ):
        order_from_checkout, action_required, _ = complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=app,
        )
    # then
    assert order_from_checkout
    mocked_payment_refund_or_void.assert_not_called()
    code = voucher_free_shipping.codes.first()
    assert code.used == 1


@mock.patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
@mock.patch("saleor.checkout.complete_checkout._process_payment")
def test_complete_checkout_checkout_completed_in_the_meantime(
    mocked_process_payment,
    mocked_payment_refund_or_void,
    customer_user,
    checkout,
    app,
    success_gateway_response,
):
    # given
    address = customer_user.default_billing_address
    checkout.user = customer_user
    checkout.billing_address = address
    checkout.shipping_address = address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        checkout=checkout,
        total=total.gross.amount,
    )
    mocked_process_payment.return_value = success_gateway_response

    # when
    def call_checkout_complete(*args, **kwargs):
        lines_2, _ = fetch_checkout_lines(checkout)
        checkout_info_2 = fetch_checkout_info(checkout, lines, manager)
        complete_checkout(
            checkout_info=checkout_info_2,
            lines=lines_2,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=app,
        )

    with before_after.after(
        "saleor.checkout.complete_checkout._reserve_stocks_without_availability_check",
        call_checkout_complete,
    ):
        order_from_checkout, action_required, _ = complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=app,
        )
    # then
    assert order_from_checkout
    mocked_payment_refund_or_void.assert_not_called()


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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    shipping_price = zero_taxed_money(checkout.currency)
    base_shipping_price = zero_money(checkout.currency)

    # when
    _ = _process_shipping_data_for_order(
        checkout_info, base_shipping_price, shipping_price, manager, lines
    )

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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    shipping_price = zero_taxed_money(checkout.currency)
    base_shipping_price = zero_money(checkout.currency)

    # when
    _ = _process_shipping_data_for_order(
        checkout_info, base_shipping_price, shipping_price, manager, lines
    )

    # then
    new_user_address_count = customer_user.addresses.count()
    new_address_data = warehouse_for_cc.address.as_data()
    assert new_user_address_count == user_address_count
    assert not customer_user.addresses.filter(**new_address_data).exists()


def test_create_order_update_display_gross_prices(checkout_with_item, customer_user):
    # given
    checkout = checkout_with_item
    channel = checkout.channel
    tax_configuration = channel.tax_configuration

    tax_configuration.display_gross_prices = False
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    lines, _ = fetch_checkout_lines(checkout)
    order_data = _prepare_order_data(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        prices_entered_with_tax=True,
    )

    # when
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=order_data,
        user=customer_user,
        app=None,
        manager=manager,
    )

    # then
    assert not order.display_gross_prices


def test_create_order_store_shipping_prices(
    checkout_with_items_and_shipping, shipping_method, customer_user
):
    # given
    checkout = checkout_with_items_and_shipping

    expected_base_shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price
    expected_shipping_price = TaxedMoney(
        net=expected_base_shipping_price * Decimal("0.9"),
        gross=expected_base_shipping_price,
    )
    expected_shipping_tax_rate = Decimal("0.1")

    manager = get_plugins_manager(allow_replica=False)
    manager.get_checkout_shipping_tax_rate = mock.Mock(
        return_value=expected_shipping_tax_rate
    )
    manager.calculate_checkout_shipping = mock.Mock(
        return_value=expected_shipping_price
    )

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )

    # then
    assert order.base_shipping_price == expected_base_shipping_price
    assert order.shipping_price == expected_shipping_price
    manager.calculate_checkout_shipping.assert_called_once_with(
        checkout_info, lines, checkout.shipping_address, plugin_ids=None
    )
    assert order.shipping_tax_rate == expected_shipping_tax_rate
    manager.get_checkout_shipping_tax_rate.assert_called_once_with(
        checkout_info,
        lines,
        checkout.shipping_address,
        expected_shipping_price,
        plugin_ids=None,
    )


def test_create_order_store_shipping_prices_with_free_shipping_voucher(
    checkout_with_voucher_free_shipping,
    shipping_method,
    customer_user,
):
    # given
    checkout = checkout_with_voucher_free_shipping
    manager = get_plugins_manager(allow_replica=False)

    expected_base_shipping_price = zero_money(checkout.currency)
    expected_shipping_price = zero_taxed_money(checkout.currency)
    expected_shipping_tax_rate = Decimal("0.0")

    manager.get_checkout_shipping_tax_rate = mock.Mock(
        return_value=expected_shipping_tax_rate
    )
    manager.calculate_checkout_shipping = mock.Mock(
        return_value=expected_shipping_price
    )

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )

    # then
    assert order.base_shipping_price == expected_base_shipping_price
    assert order.shipping_price == expected_shipping_price
    manager.calculate_checkout_shipping.assert_called_once_with(
        checkout_info, lines, checkout.shipping_address, plugin_ids=None
    )
    assert order.shipping_tax_rate == expected_shipping_tax_rate
    manager.get_checkout_shipping_tax_rate.assert_called_once_with(
        checkout_info,
        lines,
        checkout.shipping_address,
        expected_shipping_price,
        plugin_ids=None,
    )


@mock.patch("saleor.payment.gateway.payment_refund_or_void")
def test_complete_checkout_invalid_shipping_method(
    mocked_payment_refund_or_void,
    voucher,
    customer_user,
    checkout_ready_to_complete,
    app,
    payment_txn_to_confirm,
):
    """Check that if _prepare_checkout_with_payment fails, the payment is refunded."""
    # given
    checkout = checkout_ready_to_complete

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

    voucher_code = voucher.codes.first()
    checkout.voucher_code = voucher_code.code
    checkout.save()

    # make the current shipping method invalid
    checkout.shipping_method.channel_listings.filter(channel=checkout.channel).delete()

    voucher.apply_once_per_customer = True
    voucher.save()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    with pytest.raises(ValidationError):
        complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=app,
        )

    # then
    voucher_customer = VoucherCustomer.objects.filter(
        voucher_code=voucher_code, customer_email=customer_user.email
    )
    assert not voucher_customer.exists()

    mocked_payment_refund_or_void.called_once_with(
        payment, manager, channel_slug=checkout.channel.slug
    )
    checkout.refresh_from_db()
    assert checkout.is_voucher_usage_increased is False


@mock.patch("saleor.checkout.complete_checkout.complete_checkout_with_transaction")
def test_checkout_complete_pick_transaction_flow(
    mocked_flow,
    order,
    checkout_ready_to_complete,
    customer_user,
    transaction_item_generator,
):
    # given
    checkout = checkout_ready_to_complete
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    transaction_item_generator(checkout_id=checkout.pk)
    mocked_flow.return_value = order, False, {}

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
    )

    # then
    mocked_flow.assert_called_once_with(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        user=customer_user,
        app=None,
        redirect_url=None,
        metadata_list=None,
        private_metadata_list=None,
    )


@mock.patch("saleor.checkout.complete_checkout.complete_checkout_with_transaction")
def test_checkout_complete_pick_transaction_flow_when_checkout_total_zero(
    mocked_flow, order, checkout_with_item_total_0, customer_user, channel_USD
):
    # given
    checkout = checkout_with_item_total_0
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    checkout.total = zero_taxed_money(checkout.currency)
    update_checkout_payment_statuses(
        checkout=checkout,
        checkout_total_gross=checkout.total.gross,
        checkout_has_lines=bool(lines),
    )

    mocked_flow.return_value = order, False, {}
    channel_USD.order_mark_as_paid_strategy = MarkAsPaidStrategy.TRANSACTION_FLOW
    channel_USD.save()

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
    )

    # then
    mocked_flow.assert_called_once_with(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        user=customer_user,
        app=None,
        redirect_url=None,
        metadata_list=None,
        private_metadata_list=None,
    )


@mock.patch("saleor.checkout.complete_checkout.complete_checkout_with_transaction")
def test_checkout_complete_pick_transaction_flow_not_authorized_no_active_payment(
    mocked_flow,
    order,
    checkout_ready_to_complete,
    customer_user,
    transaction_item_generator,
    payment,
):
    # given
    checkout = checkout_ready_to_complete
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"

    # checkout is not fully authorized
    checkout.authorize_status = CheckoutAuthorizeStatus.PARTIAL

    # transaction item exists
    transaction_item_generator(checkout_id=checkout.pk)
    assert checkout.payment_transactions.exists()

    # there is no active payments
    payment.checkout = checkout
    payment.is_active = False
    payment.save(update_fields=["checkout", "is_active"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    transaction_item_generator(checkout_id=checkout.pk)
    mocked_flow.return_value = order, False, {}

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
    )

    # then
    mocked_flow.assert_called_once_with(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        user=customer_user,
        app=None,
        redirect_url=None,
        metadata_list=None,
        private_metadata_list=None,
    )


@mock.patch("saleor.checkout.complete_checkout.complete_checkout_with_payment")
def test_checkout_complete_pick_payment_flow(
    mocked_flow, order, checkout_ready_to_complete, customer_user
):
    # given
    checkout = checkout_ready_to_complete
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    mocked_flow.return_value = order, False, {}

    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy", is_active=True, checkout=checkout
    )
    payment.to_confirm = True
    payment.save()

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        lines=lines,
        manager=manager,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
    )

    # then
    mocked_flow.assert_called_once_with(
        manager=manager,
        checkout_pk=checkout.pk,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
        site_settings=None,
        redirect_url=None,
        metadata_list=None,
        private_metadata_list=None,
    )


@mock.patch("saleor.checkout.complete_checkout.complete_checkout_with_payment")
def test_checkout_complete_pick_payment_flow_not_authorized_active_payment(
    mocked_flow,
    order,
    checkout_ready_to_complete,
    customer_user,
    transaction_item_generator,
    payment,
):
    # given
    checkout = checkout_ready_to_complete
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"

    # checkout is not fully authorized
    checkout.authorize_status = CheckoutAuthorizeStatus.PARTIAL

    # transaction item exists
    transaction_item_generator(checkout_id=checkout.pk)
    assert checkout.payment_transactions.exists()

    # there is no active payments
    payment.checkout = checkout
    payment.save(update_fields=["checkout"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    transaction_item_generator(checkout_id=checkout.pk)
    mocked_flow.return_value = order, False, {}

    # when
    order, action_required, _ = complete_checkout(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
    )

    # then
    mocked_flow.assert_called_once_with(
        manager=manager,
        checkout_pk=checkout.pk,
        payment_data={},
        store_source=False,
        user=customer_user,
        app=None,
        site_settings=None,
        redirect_url=None,
        metadata_list=None,
        private_metadata_list=None,
    )


@mock.patch("saleor.checkout.calculations.get_tax_calculation_strategy_for_checkout")
@mock.patch("saleor.checkout.complete_checkout._create_order")
@mock.patch("saleor.checkout.complete_checkout._process_payment")
def test_complete_checkout_ensure_prices_are_not_recalculated_in_post_payment_part(
    mocked_process_payment,
    mocked_create_order,
    mocked_get_tax_calculation_strategy_for_checkout,
    customer_user,
    checkout_with_item,
    shipping_method,
    app,
    address,
    payment_dummy,
):
    # given
    checkout = checkout_with_item
    mocked_process_payment.return_value = GatewayResponse(
        is_success=True,
        action_required=False,
        action_required_data={},
        kind=TransactionKind.CAPTURE,
        amount=Decimal(3.0),
        currency="usd",
        transaction_id="1234",
        error=None,
    )
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    calculation_call_count = mocked_get_tax_calculation_strategy_for_checkout.call_count

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.price_expiration = timezone.now() + timedelta(hours=2)
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    def update_price_expiration(*args, **kwargs):
        # Invalidate checkout prices just after processing payment
        checkout.price_expiration = timezone.now() - timedelta(hours=2)
        checkout.save(update_fields=["price_expiration"])

    # when
    with before_after.after(
        "saleor.checkout.complete_checkout._process_payment", update_price_expiration
    ):
        order, action_required, _ = complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=app,
        )

    # then
    assert order

    assert (
        mocked_get_tax_calculation_strategy_for_checkout.call_count
        == calculation_call_count
    )


@mock.patch("saleor.checkout.complete_checkout.increase_voucher_usage")
def test_increase_checkout_voucher_usage(
    increase_voucher_usage_mock, checkout_with_voucher, voucher
):
    # given
    code = voucher.codes.first()

    # when
    _increase_checkout_voucher_usage(checkout_with_voucher, code, voucher, None)

    # then
    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.is_voucher_usage_increased is True
    increase_voucher_usage_mock.assert_called_once()


@mock.patch("saleor.checkout.complete_checkout.increase_voucher_usage")
def test_increase_checkout_voucher_usage_checkout_usage_already_increased(
    increase_voucher_usage_mock, checkout_with_voucher, voucher
):
    # given
    code = voucher.codes.first()
    checkout_with_voucher.is_voucher_usage_increased = True
    checkout_with_voucher.save(update_fields=["is_voucher_usage_increased"])

    # when
    _increase_checkout_voucher_usage(checkout_with_voucher, code, voucher, None)

    # then
    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.is_voucher_usage_increased is True
    increase_voucher_usage_mock.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout.release_voucher_code_usage")
def test_release_checkout_voucher_usage(
    release_voucher_usage_mock, checkout_with_voucher, voucher
):
    # given
    code = voucher.codes.first()
    checkout_with_voucher.is_voucher_usage_increased = True
    checkout_with_voucher.save(update_fields=["is_voucher_usage_increased"])

    # when
    _release_checkout_voucher_usage(checkout_with_voucher, code, voucher, None)

    # then
    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.is_voucher_usage_increased is False
    release_voucher_usage_mock.assert_called_once()


@mock.patch("saleor.checkout.complete_checkout.release_voucher_code_usage")
def test_release_checkout_voucher_usage_checkout_usage_not_increased(
    release_voucher_usage_mock, checkout_with_voucher, voucher
):
    # given
    code = voucher.codes.first()
    checkout_with_voucher.is_voucher_usage_increased = False
    checkout_with_voucher.save(update_fields=["is_voucher_usage_increased"])

    # when
    _release_checkout_voucher_usage(checkout_with_voucher, code, voucher, None)

    # then
    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.is_voucher_usage_increased is False
    release_voucher_usage_mock.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout.release_voucher_code_usage")
def test_release_checkout_voucher_usage_no_voucher_code(
    release_voucher_usage_mock, checkout_with_voucher, voucher
):
    # given
    checkout_with_voucher.is_voucher_usage_increased = True
    checkout_with_voucher.save(update_fields=["is_voucher_usage_increased"])

    # when
    _release_checkout_voucher_usage(checkout_with_voucher, None, voucher, None)

    # then
    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.is_voucher_usage_increased is False
    release_voucher_usage_mock.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
@mock.patch("saleor.checkout.complete_checkout._release_checkout_voucher_usage")
def test_complete_checkout_fail_handler(
    _release_checkout_voucher_usage_mock,
    _payment_refund_or_void_mock,
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.completing_started_at = timezone.now()
    checkout.save(update_fields=["completing_started_at"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    _complete_checkout_fail_handler(checkout_info, manager)

    # then
    checkout.refresh_from_db()
    assert not checkout.completing_started_at
    _payment_refund_or_void_mock.assert_not_called()
    _release_checkout_voucher_usage_mock.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
@mock.patch("saleor.checkout.complete_checkout._release_checkout_voucher_usage")
def test_complete_checkout_fail_handler_with_voucher(
    _release_checkout_voucher_usage_mock,
    _payment_refund_or_void_mock,
    checkout_with_voucher,
    voucher,
):
    # given
    checkout = checkout_with_voucher
    checkout.completing_started_at = timezone.now()
    checkout.save(update_fields=["completing_started_at"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    _complete_checkout_fail_handler(checkout_info, manager, voucher=voucher)

    # then
    checkout.refresh_from_db()
    assert not checkout.completing_started_at
    _payment_refund_or_void_mock.assert_not_called()
    _release_checkout_voucher_usage_mock.assert_called_once()


@mock.patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
@mock.patch("saleor.checkout.complete_checkout._release_checkout_voucher_usage")
def test_complete_checkout_fail_handler_with_payment(
    _release_checkout_voucher_usage_mock,
    _payment_refund_or_void_mock,
    checkout_with_item,
    payment,
):
    # given
    checkout = checkout_with_item
    checkout.completing_started_at = timezone.now()
    checkout.save(update_fields=["completing_started_at"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    _complete_checkout_fail_handler(checkout_info, manager, payment=payment)

    # then
    checkout.refresh_from_db()
    assert not checkout.completing_started_at
    _payment_refund_or_void_mock.assert_called_once()
    _release_checkout_voucher_usage_mock.assert_not_called()


@mock.patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
@mock.patch("saleor.checkout.complete_checkout._release_checkout_voucher_usage")
def test_complete_checkout_fail_handler_with_voucher_and_payment(
    _release_checkout_voucher_usage_mock,
    _payment_refund_or_void_mock,
    checkout_with_voucher,
    payment,
    voucher,
):
    # given
    checkout = checkout_with_voucher
    checkout.completing_started_at = timezone.now()
    checkout.save(update_fields=["completing_started_at"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    _complete_checkout_fail_handler(
        checkout_info, manager, voucher=voucher, payment=payment
    )

    # then
    checkout.refresh_from_db()
    assert not checkout.completing_started_at
    _payment_refund_or_void_mock.assert_called_once()
    _release_checkout_voucher_usage_mock.assert_called_once()
