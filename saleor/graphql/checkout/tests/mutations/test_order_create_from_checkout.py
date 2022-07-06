from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
import pytz
from django.db.models.aggregates import Sum
from django.utils import timezone
from prices import Money

from .....checkout import calculations
from .....checkout.error_codes import OrderCreateFromCheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....core.taxes import TaxError, zero_money, zero_taxed_money
from .....giftcard import GiftCardEvents
from .....giftcard.models import GiftCard, GiftCardEvent
from .....order import OrderOrigin, OrderStatus
from .....order.models import Fulfillment, Order
from .....plugins.manager import PluginsManager, get_plugins_manager
from .....tests.utils import flush_post_commit_hooks
from .....warehouse.models import Reservation, Stock, WarehouseClickAndCollectOption
from .....warehouse.tests.utils import get_available_quantity_for_stock
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_ORDER_CREATE_FROM_CHECKOUT = """
mutation orderCreateFromCheckout($id: ID!){
    orderCreateFromCheckout(id: $id){
        order{
            id,
            token
            original
            origin
        }
        errors{
            field
            message
            code
            variants
        }
    }
}
"""


def test_order_from_checkout_with_inactive_channel(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_gift_card,
    gift_card,
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

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert (
        data["errors"][0]["code"]
        == OrderCreateFromCheckoutErrorCode.CHANNEL_INACTIVE.name
    )
    assert data["errors"][0]["field"] == "channel"


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_order_from_checkout(
    order_confirmed_mock,
    app_api_client,
    permission_handle_checkouts,
    site_settings,
    checkout_with_gift_card,
    gift_card,
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

    metadata_key = "md key"
    metadata_value = "md value"

    checkout_line.store_value_in_private_metadata({metadata_key: metadata_value})
    checkout_line.store_value_in_metadata({metadata_key: metadata_value})
    checkout_line.save()

    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant
    checkout_line_metadata = checkout_line.metadata
    checkout_line_private_metadata = checkout_line.private_metadata

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    site_settings.automatically_confirm_all_new_orders = True
    site_settings.save()

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original
    assert str(order.pk) == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert checkout_line_metadata == order_line.metadata
    assert checkout_line_private_metadata == order_line.private_metadata
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.search_vector

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )

    order_confirmed_mock.assert_called_once_with(order)


def test_order_from_checkout_by_app_with_missing_permission(
    app_api_client,
    checkout_with_item,
    customer_user,
    address,
    shipping_method,
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
    )

    assert_no_permission(response)


@patch("saleor.giftcard.utils.send_gift_card_notification")
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_order_from_checkout_gift_card_bought(
    order_confirmed_mock,
    send_notification_mock,
    site_settings,
    customer_user,
    app_api_client,
    app,
    permission_handle_checkouts,
    checkout_with_gift_card_items,
    address,
    shipping_method,
):
    checkout = checkout_with_gift_card_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.user = customer_user
    checkout.save()

    site_settings.automatically_confirm_all_new_orders = True
    site_settings.automatically_fulfill_non_shippable_gift_card = True
    site_settings.save()

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.PARTIALLY_FULFILLED

    flush_post_commit_hooks()
    gift_card = GiftCard.objects.get()
    assert GiftCardEvent.objects.filter(gift_card=gift_card, type=GiftCardEvents.BOUGHT)
    send_notification_mock.assert_called_once_with(
        None,
        app,
        customer_user,
        customer_user.email,
        gift_card,
        ANY,
        checkout.channel.slug,
        resending=False,
    )
    order_confirmed_mock.assert_called_once_with(order)
    assert Fulfillment.objects.count() == 1


def test_order_from_checkout_no_checkout_email(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_gift_card,
    address,
    shipping_method,
):
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.email = None
    checkout.save()

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert len(data["errors"]) == 1
    assert (
        data["errors"][0]["code"] == OrderCreateFromCheckoutErrorCode.EMAIL_NOT_SET.name
    )


def test_order_from_checkout_with_variant_without_sku(
    site_settings,
    app_api_client,
    checkout_with_item,
    gift_card,
    permission_handle_checkouts,
    address,
    shipping_method,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.sku = None
    checkout_line_variant.save()

    site_settings.automatically_confirm_all_new_orders = True
    site_settings.save()

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.get(pk=order_token)
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT

    order_line = order.lines.first()
    assert order_line.product_sku is None
    assert order_line.product_variant_id == order_line.variant.get_global_id()


def test_order_from_checkout_with_variant_without_price(
    site_settings,
    app_api_client,
    permission_handle_checkouts,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
):

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.channel_listings.filter(channel=checkout.channel).update(
        price_amount=None
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    errors = content["data"]["orderCreateFromCheckout"]["errors"]
    assert (
        errors[0]["code"]
        == OrderCreateFromCheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    )
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [variant_id]


@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_order_from_checkout_requires_confirmation(
    order_confirmed_mock,
    app_api_client,
    permission_handle_checkouts,
    site_settings,
    checkout_ready_to_complete,
):
    site_settings.automatically_confirm_all_new_orders = False
    site_settings.save()

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_ready_to_complete.pk),
    }
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)

    order_id = graphene.Node.from_global_id(
        content["data"]["orderCreateFromCheckout"]["order"]["id"]
    )[1]
    order = Order.objects.get(pk=order_id)
    assert order.is_unconfirmed()
    order_confirmed_mock.assert_not_called()


@pytest.mark.integration
def test_order_from_checkout_with_voucher(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
):
    voucher_used_count = voucher_percentage.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.save(update_fields=["usage_limit"])

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

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.pk) == order_token
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method

    voucher_percentage.refresh_from_db()
    assert voucher_percentage.used == voucher_used_count + 1


@patch.object(PluginsManager, "preprocess_order_creation")
@pytest.mark.integration
def test_order_from_checkout_voucher_not_increase_uses_on_preprocess_creation_failure(
    mocked_preprocess_order_creation,
    app_api_client,
    permission_handle_checkouts,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
):
    mocked_preprocess_order_creation.side_effect = TaxError("tax error!")
    voucher_percentage.used = 0
    voucher_percentage.usage_limit = 1
    voucher_percentage.save(update_fields=["used", "usage_limit"])

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]

    assert data["errors"][0]["code"] == OrderCreateFromCheckoutErrorCode.TAX_ERROR.name

    voucher_percentage.refresh_from_db()
    assert voucher_percentage.used == 0


@pytest.mark.integration
def test_order_from_checkout_without_inventory_tracking(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_variant_without_inventory_tracking,
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
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.pk) == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert not order_line.allocations.all()
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method


def test_order_from_checkout_checkout_without_lines(
    site_settings,
    app_api_client,
    permission_handle_checkouts,
    checkout,
    address,
    shipping_method,
):
    checkout = checkout
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    assert not lines

    site_settings.automatically_confirm_all_new_orders = True
    site_settings.save()

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == OrderCreateFromCheckoutErrorCode.NO_LINES.name


def test_order_from_checkout_insufficient_stock(
    app,
    app_api_client,
    checkout_with_item,
    address,
    shipping_method,
    permission_handle_checkouts,
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

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    orders_count = Order.objects.count()
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()


def test_order_from_checkout_insufficient_stock_reserved_by_other_user(
    site_settings_with_reservations,
    app_api_client,
    permission_handle_checkouts,
    checkout_with_item,
    address,
    shipping_method,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)

    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=checkout_line.variant,
        quantity=quantity_available,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=stock,
        quantity_reserved=quantity_available,
        reserved_until=timezone.now() + timedelta(minutes=5),
    )

    checkout_line.quantity = 1
    checkout_line.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
    }
    orders_count = Order.objects.count()
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()


def test_order_from_checkout_own_reservation(
    site_settings_with_reservations,
    app_api_client,
    permission_handle_checkouts,
    checkout_with_item,
    address,
    shipping_method,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)

    checkout_line.quantity = quantity_available
    checkout_line.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    reservation = Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=quantity_available,
        reserved_until=timezone.now() + timedelta(minutes=5),
    )

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    orders_count = Order.objects.count()
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.pk) == order_token

    order_line = order.lines.first()
    assert order_line.quantity == quantity_available
    assert order_line.variant == checkout_line.variant

    # Reservation associated with checkout has been deleted
    with pytest.raises(Reservation.DoesNotExist):
        reservation.refresh_from_db()


def test_order_from_checkout_with_digital(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_digital_item,
    address,
):
    """Ensure it is possible to complete a digital checkout without shipping."""

    order_count = Order.objects.count()
    checkout = checkout_with_digital_item
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # Set a billing address
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address"])

    # Send the creation request
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)["data"]["orderCreateFromCheckout"]
    assert not content["errors"]

    # Ensure the order was actually created
    assert (
        Order.objects.count() == order_count + 1
    ), "The order should have been created"


@pytest.mark.integration
def test_order_from_checkout_0_total_value(
    app_api_client,
    checkout_with_item,
    gift_card,
    permission_handle_checkouts,
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
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.pk) == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_order_from_checkout_for_click_and_collect(
    app_api_client,
    checkout_with_item_for_cc,
    address,
    warehouse_for_cc,
    permission_handle_checkouts,
):
    order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    checkout.billing_address = address
    checkout.collection_point = warehouse_for_cc

    checkout.save(
        update_fields=["shipping_address", "billing_address", "collection_point"]
    )

    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)["data"]["orderCreateFromCheckout"]

    assert not content["errors"]
    assert Order.objects.count() == order_count + 1

    order = Order.objects.first()

    assert order.collection_point == warehouse_for_cc
    assert order.shipping_method is None
    assert order.shipping_address == warehouse_for_cc.address
    assert order.shipping_price == zero_taxed_money(order.currency)


def test_order_from_checkout_raises_error_for_local_stock(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_item_for_cc,
    address,
    warehouse_for_cc,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    checkout.collection_point = warehouse_for_cc
    checkout.billing_address = address
    checkout.save(
        update_fields=["collection_point", "shipping_address", "billing_address"]
    )

    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)["data"]["orderCreateFromCheckout"]
    assert (
        content["errors"][0]["code"]
        == OrderCreateFromCheckoutErrorCode.INSUFFICIENT_STOCK.name
    )
    assert Order.objects.count() == initial_order_count


def test_order_from_checkout_for_all_warehouse_even_if_not_available_locally(
    stocks_for_cc,
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    app_api_client,
    permission_handle_checkouts,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(
        product_variant=checkout_line.variant, warehouse=warehouse_for_cc
    )
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    warehouse_for_cc.click_and_collect_option = (
        WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )
    warehouse_for_cc.save()

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["collection_point"])

    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)["data"]["orderCreateFromCheckout"]
    assert not content["errors"]
    assert Order.objects.count() == initial_order_count + 1


def test_checkout_from_order_raises_insufficient_stock_when_quantity_above_stock_sum(
    stocks_for_cc,
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    app_api_client,
    permission_handle_checkouts,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    overall_stock_quantity = (
        Stock.objects.filter(product_variant=checkout_line.variant).aggregate(
            Sum("quantity")
        )
    ).pop("quantity__sum")
    checkout_line.quantity = overall_stock_quantity + 1
    checkout_line.save()
    warehouse_for_cc.click_and_collect_option = (
        WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )
    warehouse_for_cc.save()

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    checkout.collection_point = warehouse_for_cc
    checkout.billing_address = address
    checkout.save(update_fields=["collection_point", "billing_address"])

    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)["data"]["orderCreateFromCheckout"]
    assert (
        content["errors"][0]["code"]
        == OrderCreateFromCheckoutErrorCode.INSUFFICIENT_STOCK.name
    )
    assert Order.objects.count() == initial_order_count


def test_order_from_checkout_raises_invalid_shipping_method_when_warehouse_disabled(
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    app_api_client,
    permission_handle_checkouts,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    checkout.billing_address = address
    checkout.collection_point = warehouse_for_cc

    checkout.save(
        update_fields=["shipping_address", "billing_address", "collection_point"]
    )

    warehouse_for_cc.click_and_collect_option = WarehouseClickAndCollectOption.DISABLED
    warehouse_for_cc.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    assert not checkout_info.valid_pick_up_points
    assert not checkout_info.delivery_method_info.is_method_in_valid_methods(
        checkout_info
    )

    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)["data"]["orderCreateFromCheckout"]

    assert (
        content["errors"][0]["code"]
        == OrderCreateFromCheckoutErrorCode.INVALID_SHIPPING_METHOD.name
    )
    assert Order.objects.count() == initial_order_count


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_order_from_draft_create_with_preorder_variant(
    order_confirmed_mock,
    site_settings,
    app_api_client,
    permission_handle_checkouts,
    checkout_with_item_and_preorder_item,
    address,
    shipping_method,
):
    checkout = checkout_with_item_and_preorder_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    variants_and_quantities = {line.variant_id: line.quantity for line in checkout}

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    site_settings.automatically_confirm_all_new_orders = True
    site_settings.save()

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original
    assert str(order.pk) == order_token
    assert order.total.gross == total.gross

    assert order.lines.count() == len(variants_and_quantities)
    for variant_id, quantity in variants_and_quantities.items():
        order.lines.get(variant_id=variant_id).quantity == quantity
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method

    preorder_line = order.lines.filter(variant__is_preorder=True).first()
    assert not preorder_line.allocations.exists()
    preorder_allocation = preorder_line.preorder_allocations.get()
    assert preorder_allocation.quantity == quantity

    stock_line = order.lines.filter(variant__is_preorder=False).first()
    assert stock_line.allocations.exists()
    assert not stock_line.preorder_allocations.exists()

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order)


def test_order_from_draft_create_click_collect_preorder_fails_for_disabled_warehouse(
    warehouse_for_cc,
    checkout_with_items_for_cc,
    address,
    app_api_client,
    permission_handle_checkouts,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_items_for_cc
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    checkout.billing_address = address
    checkout.collection_point = warehouse_for_cc

    checkout_line = checkout.lines.first()
    checkout_line.variant.is_preorder = True
    checkout_line.variant.preorder_global_threshold = 100
    checkout_line.variant.save()

    for line in checkout.lines.all():
        if line.variant.channel_listings.filter(channel=checkout.channel).exists():
            continue

        line.variant.channel_listings.create(
            channel=checkout.channel,
            price_amount=Decimal(15),
            currency=checkout.currency,
        )

    checkout.save(
        update_fields=["shipping_address", "billing_address", "collection_point"]
    )

    warehouse_for_cc.click_and_collect_option = WarehouseClickAndCollectOption.DISABLED
    warehouse_for_cc.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    assert not checkout_info.valid_pick_up_points
    assert not checkout_info.delivery_method_info.is_method_in_valid_methods(
        checkout_info
    )

    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)["data"]["orderCreateFromCheckout"]

    assert (
        content["errors"][0]["code"]
        == OrderCreateFromCheckoutErrorCode.INVALID_SHIPPING_METHOD.name
    )
    assert Order.objects.count() == initial_order_count


def test_order_from_draft_create_variant_channel_listing_does_not_exist(
    checkout_with_items,
    address,
    shipping_method,
    app_api_client,
    permission_handle_checkouts,
):

    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.channel_listings.get(channel__id=checkout.channel_id).delete()

    lines, _ = fetch_checkout_lines(checkout)

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == OrderCreateFromCheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    )
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_order_from_draft_create_variant_channel_listing_no_price(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_items,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    variants = []
    for line in checkout.lines.all()[:2]:
        checkout_line_variant = line.variant
        variants.append(checkout_line_variant)
        variant_channel_listing = checkout_line_variant.channel_listings.get(
            channel__id=checkout.channel_id
        )
        variant_channel_listing.price_amount = None
        variant_channel_listing.save(update_fields=["price_amount"])

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == OrderCreateFromCheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    )
    assert errors[0]["field"] == "lines"
    assert set(errors[0]["variants"]) == {
        graphene.Node.to_global_id("ProductVariant", variant.pk) for variant in variants
    }

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_order_from_draft_create_product_channel_listing_does_not_exist(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_items,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.product.channel_listings.get(
        channel__id=checkout.channel_id
    ).delete()

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == OrderCreateFromCheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    )
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()


@pytest.mark.parametrize(
    "available_for_purchase", [None, datetime.now(pytz.UTC) + timedelta(days=1)]
)
def test_order_from_draft_create_product_channel_listing_not_available_for_purchase(
    app_api_client,
    permission_handle_checkouts,
    checkout_with_items,
    address,
    shipping_method,
    available_for_purchase,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    product_channel_listings = checkout_line_variant.product.channel_listings.get(
        channel__id=checkout.channel_id
    )
    product_channel_listings.available_for_purchase_at = available_for_purchase
    product_channel_listings.save(update_fields=["available_for_purchase_at"])

    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == OrderCreateFromCheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    )
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()


@pytest.mark.integration
def test_order_from_draft_create_0_total_value_from_voucher(
    app_api_client,
    permission_handle_checkouts,
    checkout_without_shipping_required,
    shipping_method,
    address,
    voucher,
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.voucher_code = voucher.code
    checkout.discount = Money("10.00", "USD")

    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )

    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.pk) == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_order_from_draft_create_0_total_value_from_giftcard(
    app_api_client,
    permission_handle_checkouts,
    checkout_without_shipping_required,
    address,
    gift_card,
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout.gift_cards.add(gift_card)
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CREATE_FROM_CHECKOUT,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCreateFromCheckout"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.pk) == order_token
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata
    assert order.private_metadata == checkout.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
