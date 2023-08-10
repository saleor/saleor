import graphene
import pytest
from prices import Money

from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....order import OrderStatus
from .....order.models import Order
from .....plugins.manager import get_plugins_manager
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete(
            $id: ID,
            $redirectUrl: String,
            $metadata: [MetadataInput!],
        ) {
        checkoutComplete(
                id: $id,
                redirectUrl: $redirectUrl,
                metadata: $metadata,
            ) {
            order {
                id
                token
                original
                origin
                deliveryMethod {
                    ... on Warehouse {
                        id
                    }
                    ... on ShippingMethod {
                        id
                    }
                }
                total {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
                undiscountedTotal {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            }
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


def test_checkout_complete_unconfirmed_order_already_exists(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    orders_count = Order.objects.count()
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_data = data["order"]
    assert Order.objects.count() == orders_count
    assert order_data["id"] == graphene.Node.to_global_id("Order", order_with_lines.id)
    assert str(order_with_lines.id) == order_data["token"]
    assert order_data["origin"] == order_with_lines.origin.upper()
    assert not order_data["original"]


def test_checkout_complete_order_already_exists(
    user_api_client,
    order_with_lines,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    orders_count = Order.objects.count()
    order_with_lines.checkout_token = checkout.pk
    order_with_lines.save()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_data = data["order"]
    assert Order.objects.count() == orders_count
    assert order_data["id"] == graphene.Node.to_global_id("Order", order_with_lines.id)
    assert str(order_with_lines.id) == order_data["token"]
    assert order_data["origin"] == order_with_lines.origin.upper()
    assert not order_data["original"]


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

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name
    assert data["errors"][0]["field"] == "channel"


def test_checkout_complete_no_checkout_email(
    user_api_client,
    checkout_with_gift_card,
):
    checkout = checkout_with_gift_card
    checkout.email = None
    checkout.save(update_fields=["email"])

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.EMAIL_NOT_SET.name


@pytest.mark.integration
def test_checkout_complete_0_total_value_no_payment(
    user_api_client,
    checkout_with_item_total_0,
    address,
):
    checkout = checkout_with_item_total_0
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

    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_0_total_value_from_voucher(
    user_api_client,
    checkout_without_shipping_required,
    shipping_method,
    address,
    voucher,
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.voucher_code = voucher.code
    checkout.discount = Money("10.00", "USD")

    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_0_total_value_from_giftcard(
    user_api_client,
    checkout_without_shipping_required,
    address,
    gift_card,
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.gift_cards.add(gift_card)
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
