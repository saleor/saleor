from unittest.mock import patch

import graphene
import pytest

from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....core.taxes import zero_money
from .....order import OrderOrigin, OrderStatus
from .....order.models import Order
from .....plugins.manager import get_plugins_manager
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete($checkoutId: ID, $token: UUID, $redirectUrl: String) {
        checkoutComplete(
            checkoutId: $checkoutId, token: $token, redirectUrl: $redirectUrl
        ) {
            order {
                id,
                token
                original
                origin
            },
            errors {
                field,
                message,
                variants,
                code
            }
            confirmationNeeded
            confirmationData
        }
    }
    """


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
    assert not data["errors"]

    order_data = data["order"]
    assert Order.objects.count() == orders_count
    assert str(order_with_lines.id) == order_data["token"]
    assert order_data["origin"] == order_with_lines.origin.upper()
    assert not order_data["original"]


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
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
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
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original
    assert str(order.id) == order_token
    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

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


def test_checkout_complete_order_already_exists_neither_token_and_id_given(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()
    variables = {"redirectUrl": "https://www.example.com"}
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert not data["order"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_complete_order_already_exists_both_token_and_id_given(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {
        "checkoutId": checkout_id,
        "token": checkout.token,
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert not data["order"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_complete_order_already_exists_for_token_as_input(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    # given
    checkout = checkout_with_gift_card
    orders_count = Order.objects.count()
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()

    variables = {"token": checkout.token, "redirectUrl": "https://www.example.com"}
    checkout.delete()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_data = data["order"]
    assert Order.objects.count() == orders_count
    assert str(order_with_lines.id) == order_data["token"]
    assert order_data["origin"] == order_with_lines.origin.upper()
    assert not order_data["original"]


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_for_token_as_input(
    order_confirmed_mock,
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"token": checkout.token, "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original
    assert str(order.id) == order_token
    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

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
