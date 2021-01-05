from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest

from ....checkout import calculations
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.models import Checkout
from ....checkout.utils import fetch_checkout_lines
from ....core.exceptions import InsufficientStock
from ....core.taxes import zero_money
from ....order import OrderStatus
from ....order.models import Order
from ....payment import ChargeStatus, PaymentError, TransactionKind
from ....payment.gateways.dummy_credit_card import TOKEN_VALIDATION_MAPPING
from ....payment.interface import GatewayResponse
from ....plugins.manager import PluginsManager, get_plugins_manager
from ....warehouse.models import Stock
from ....warehouse.tests.utils import get_available_quantity_for_stock
from ...tests.utils import get_graphql_content

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete($checkoutId: ID!, $redirectUrl: String) {
        checkoutComplete(checkoutId: $checkoutId, redirectUrl: $redirectUrl) {
            order {
                id,
                token
            },
            checkoutErrors {
                field,
                message,
                code
            }
            confirmationNeeded
            confirmationData
        }
    }
    """


ACTION_REQUIRED_GATEWAY_RESPONSE = GatewayResponse(
    is_success=True,
    action_required=True,
    action_required_data={
        "paymentData": "test",
        "paymentMethodType": "scheme",
        "url": "https://test.adyen.com/hpp/3d/validate.shtml",
        "data": {
            "MD": "md-test-data",
            "PaReq": "PaReq-test-data",
            "TermUrl": "http://127.0.0.1:3000/",
        },
        "method": "POST",
        "type": "redirect",
    },
    kind=TransactionKind.CAPTURE,
    amount=Decimal(3.0),
    currency="usd",
    transaction_id="1234",
    error=None,
)


def test_checkout_complete_order_already_exists(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    orders_count = Order.objects.count()
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count
    assert order_with_lines.token == order_token


def test_checkout_complete_with_inactive_channel_order_already_exists(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    order_with_lines.checkout_token = checkout.pk
    channel = order_with_lines.channel
    channel.is_active = False
    channel.save()
    order_with_lines.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["checkoutErrors"][0]["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name
    assert data["checkoutErrors"][0]["field"] == "channel"


def test_checkout_complete_with_inactive_channel(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    channel = checkout.channel
    channel.is_active = False
    channel.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager, checkout=checkout, lines=lines, address=address, discounts=[]
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["checkoutErrors"][0]["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name
    assert data["checkoutErrors"][0]["field"] == "channel"


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete(
    order_confirmed_mock,
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):

    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout, lines, address
    )
    site_settings.automatically_confirm_all_new_orders = True
    site_settings.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    redirect_url = "https://www.example.com"
    variables = {"checkoutId": checkout_id, "redirectUrl": redirect_url}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.token == order_token
    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order)


@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_requires_confirmation(
    order_confirmed_mock,
    user_api_client,
    site_settings,
    payment_dummy,
    checkout_ready_to_complete,
):
    site_settings.automatically_confirm_all_new_orders = False
    site_settings.save()
    payment = payment_dummy
    payment.checkout = checkout_ready_to_complete
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout_ready_to_complete.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)

    order_id = int(
        graphene.Node.from_global_id(
            content["data"]["checkoutComplete"]["order"]["id"]
        )[1]
    )
    order = Order.objects.get(pk=order_id)
    assert order.status == OrderStatus.UNCONFIRMED
    order_confirmed_mock.assert_not_called()


@pytest.mark.integration
def test_checkout_with_voucher_complete(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    payment_dummy,
    address,
    shipping_method,
):
    voucher_used_count = voucher_percentage.used

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)

    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    voucher_percentage.refresh_from_db()
    assert voucher_percentage.used == voucher_used_count + 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_without_inventory_tracking(
    user_api_client,
    checkout_with_variant_without_inventory_tracking,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout_with_variant_without_inventory_tracking
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert not order_line.allocations.all()
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
@pytest.mark.parametrize("token, error", list(TOKEN_VALIDATION_MAPPING.items()))
@patch(
    "saleor.payment.gateways.dummy_credit_card.plugin."
    "DummyCreditCardGatewayPlugin.DEFAULT_ACTIVE",
    True,
)
def test_checkout_complete_error_in_gateway_response_for_dummy_credit_card(
    token,
    error,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy_credit_card,
    address,
    shipping_method,
):
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout, lines, address
    )
    payment = payment_dummy_credit_card
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.token = token
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["checkoutErrors"])
    assert data["checkoutErrors"][0]["message"] == error
    assert payment.transactions.count() == 1
    assert Order.objects.count() == orders_count


ERROR_GATEWAY_RESPONSE = GatewayResponse(
    is_success=False,
    action_required=False,
    kind=TransactionKind.CAPTURE,
    amount=Decimal(0),
    currency="usd",
    transaction_id="1234",
    error="ERROR",
)


def _process_payment_transaction_returns_error(*args, **kwards):
    return ERROR_GATEWAY_RESPONSE


def _process_payment_raise_error(*args, **kwargs):
    raise PaymentError("Oops! Something went wrong.")


@pytest.fixture(
    params=[_process_payment_raise_error, _process_payment_transaction_returns_error]
)
def error_side_effect(request):
    return request.param


@patch.object(PluginsManager, "process_payment")
def test_checkout_complete_does_not_delete_checkout_after_unsuccessful_payment(
    mocked_process_payment,
    error_side_effect,
    user_api_client,
    checkout_with_voucher,
    voucher,
    payment_dummy,
    address,
    shipping_method,
):
    mocked_process_payment.side_effect = error_side_effect
    expected_voucher_usage_count = voucher.used
    checkout = checkout_with_voucher
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    taxed_total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = taxed_total.gross.amount
    payment.currency = taxed_total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    get_graphql_content(response)

    assert Order.objects.count() == orders_count

    payment.refresh_from_db(fields=["order"])
    transaction = payment.transactions.get()
    assert transaction.error
    assert payment.order is None

    # ensure the voucher usage count was not incremented
    voucher.refresh_from_db(fields=["used"])
    assert voucher.used == expected_voucher_usage_count

    assert Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should not have been deleted"

    mocked_process_payment.assert_called_once()


def test_checkout_complete_invalid_checkout_id(user_api_client):
    checkout_id = "invalidId"
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert (
        data["checkoutErrors"][0]["message"] == "Couldn't resolve to a node: invalidId"
    )
    assert data["checkoutErrors"][0]["field"] == "checkoutId"
    assert orders_count == Order.objects.count()


def test_checkout_complete_no_payment(
    user_api_client, checkout_with_item, address, shipping_method
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["checkoutErrors"][0]["message"] == (
        "Provided payment methods can not cover the checkout's total amount"
    )
    assert orders_count == Order.objects.count()


@patch.object(PluginsManager, "process_payment")
def test_checkout_complete_confirmation_needed(
    mocked_process_payment,
    user_api_client,
    checkout_with_item,
    address,
    payment_dummy,
    shipping_method,
):
    mocked_process_payment.return_value = ACTION_REQUIRED_GATEWAY_RESPONSE

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]
    assert data["confirmationNeeded"] is True
    assert data["confirmationData"]

    new_orders_count = Order.objects.count()
    assert new_orders_count == orders_count
    checkout.refresh_from_db()
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active
    assert payment_dummy.to_confirm

    mocked_process_payment.assert_called_once()


@patch.object(PluginsManager, "confirm_payment")
def test_checkout_confirm(
    mocked_confirm_payment,
    user_api_client,
    checkout_with_item,
    payment_txn_to_confirm,
    address,
    shipping_method,
):
    response = ACTION_REQUIRED_GATEWAY_RESPONSE
    response.action_required = False
    mocked_confirm_payment.return_value = response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    payment = payment_txn_to_confirm
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    orders_count = Order.objects.count()

    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["checkoutErrors"]
    assert not data["confirmationNeeded"]

    mocked_confirm_payment.assert_called_once()

    new_orders_count = Order.objects.count()
    assert new_orders_count == orders_count + 1


def test_checkout_complete_insufficient_stock(
    user_api_client, checkout_with_item, address, payment_dummy, shipping_method
):
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["checkoutErrors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()


@patch("saleor.checkout.complete_checkout.gateway.refund")
def test_checkout_complete_insufficient_stock_payment_refunded(
    gateway_refund_mock,
    checkout_with_item,
    address,
    shipping_method,
    payment_dummy,
    user_api_client,
):
    # given
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["checkoutErrors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()

    gateway_refund_mock.assert_called_once_with(payment)


@patch("saleor.checkout.complete_checkout.gateway.void")
def test_checkout_complete_insufficient_stock_payment_voided(
    gateway_void_mock,
    checkout_with_item,
    address,
    shipping_method,
    payment_txn_preauth,
    user_api_client,
):
    # given
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )

    payment = payment_txn_preauth
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.charge_status = ChargeStatus.NOT_CHARGED
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["checkoutErrors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()

    gateway_void_mock.assert_called_once_with(payment)


def test_checkout_complete_without_redirect_url(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):

    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout, lines, address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.total.gross == total.gross

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
def test_checkout_complete_payment_payment_total_different_than_checkout(
    gateway_refund_or_void_mock,
    checkout_with_items,
    payment_dummy,
    user_api_client,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount - Decimal(10)
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert (
        data["checkoutErrors"][0]["code"]
        == CheckoutErrorCode.CHECKOUT_NOT_FULLY_PAID.name
    )
    assert orders_count == Order.objects.count()

    gateway_refund_or_void_mock.assert_called_with(payment)


def test_order_already_exists(
    user_api_client, checkout_ready_to_complete, payment_dummy, order_with_lines
):

    checkout = checkout_ready_to_complete
    order_with_lines.checkout_token = checkout.token
    order_with_lines.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    checkout.delete()
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.token == order_token

    assert Checkout.objects.count() == 0


@patch("saleor.checkout.complete_checkout._create_order")
def test_create_order_raises_insufficient_stock(
    mocked_create_order, user_api_client, checkout_ready_to_complete, payment_dummy
):
    mocked_create_order.side_effect = InsufficientStock("InsufficientStock")
    checkout = checkout_ready_to_complete
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout, lines, checkout.shipping_address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert (
        data["checkoutErrors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    )
    assert mocked_create_order.called

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED


def test_checkout_complete_with_digital(
    api_client, checkout_with_digital_item, address, payment_dummy
):
    """Ensure it is possible to complete a digital checkout without shipping."""

    order_count = Order.objects.count()
    checkout = checkout_with_digital_item
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}

    # Set a billing address
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address"])

    # Create a dummy payment to charge
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    # Send the creation request
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert not content["checkoutErrors"]

    # Ensure the order was actually created
    assert (
        Order.objects.count() == order_count + 1
    ), "The order should have been created"


@pytest.mark.integration
def test_checkout_complete_0_total_value(
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):

    assert not gift_card.last_used_on

    checkout = checkout_with_item
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    product_type = checkout_line_variant.product.product_type
    product_type.is_shipping_required = False
    product_type.save(update_fields=["is_shipping_required"])

    checkout_line_variant.cost_price_amount = Decimal(0)
    checkout_line_variant.price_amount = Decimal(0)
    checkout_line_variant.save()

    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["checkoutErrors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
