from decimal import Decimal

from .....channel import MarkAsPaidStrategy
from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....checkout.payment_utils import update_checkout_payment_statuses
from .....core.taxes import zero_money
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderOrigin, OrderStatus
from .....order.models import Order
from .....payment import TransactionEventType
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....plugins.manager import get_plugins_manager
from .....warehouse.models import Reservation
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
                authorizeStatus
                chargeStatus
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


def test_checkout_without_any_transaction(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.CHECKOUT_NOT_FULLY_PAID.name


def test_checkout_with_total_0(
    checkout_with_item_total_0,
    user_api_client,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
    channel_USD,
):
    # given
    shipping_method.channel_listings.update(price_amount=Decimal(0))

    checkout = checkout_with_item_total_0
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.order_mark_as_paid_strategy = MarkAsPaidStrategy.TRANSACTION_FLOW
    channel.save()

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)

    order = Order.objects.get()
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert to_global_id_or_none(order) == data["order"]["id"]

    assert order.total_charged == zero_money(order.currency)
    assert order.total_authorized == zero_money(order.currency)
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.authorize_status == OrderAuthorizeStatus.FULL


def test_checkout_with_authorized(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, authorized_value=total.gross.amount
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    order = Order.objects.get()
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert to_global_id_or_none(order) == data["order"]["id"]

    assert order.total_charged == zero_money(order.currency)
    assert order.total_authorized_amount == transaction.authorized_value
    assert order.charge_status == OrderChargeStatus.NONE
    assert order.authorize_status == OrderAuthorizeStatus.FULL

    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT

    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    line_tax_class = order_line.tax_class
    shipping_tax_class = shipping_method.tax_class

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata

    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )

    assert not Checkout.objects.filter()
    assert not len(Reservation.objects.all())


def test_checkout_with_charged(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=total.gross.amount
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    order = Order.objects.get()
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert to_global_id_or_none(order) == data["order"]["id"]

    assert order.total_charged_amount == transaction.charged_value
    assert order.total_authorized == zero_money(order.currency)
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.authorize_status == OrderAuthorizeStatus.FULL

    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT

    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    line_tax_class = order_line.tax_class
    shipping_tax_class = shipping_method.tax_class

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata

    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )

    assert not Checkout.objects.filter()
    assert not len(Reservation.objects.all())


def test_checkout_paid_with_multiple_transactions(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=total.gross.amount - Decimal("10")
    )
    second_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal("10")
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    order = Order.objects.get()
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert to_global_id_or_none(order) == data["order"]["id"]

    assert (
        order.total_charged_amount
        == transaction.charged_value + second_transaction.charged_value
    )
    assert order.total_authorized == zero_money(order.currency)
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.authorize_status == OrderAuthorizeStatus.FULL


def test_checkout_partially_paid(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=total.gross.amount - Decimal("10")
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == CheckoutErrorCode.CHECKOUT_NOT_FULLY_PAID.name


def test_checkout_with_pending_charged(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
    transaction_events_generator,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CHARGE_REQUEST,
        ],
        amounts=[
            total.gross.amount,
        ],
    )
    recalculate_transaction_amounts(transaction)

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    order = Order.objects.get()
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert to_global_id_or_none(order) == data["order"]["id"]

    assert order.total_charged == zero_money(order.currency)
    assert order.total_authorized == zero_money(order.currency)
    assert order.charge_status == OrderChargeStatus.NONE
    assert order.authorize_status == OrderAuthorizeStatus.NONE


def test_checkout_with_pending_authorized(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
    transaction_events_generator,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_REQUEST,
        ],
        amounts=[
            total.gross.amount,
        ],
    )
    recalculate_transaction_amounts(transaction)

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    order = Order.objects.get()
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert to_global_id_or_none(order) == data["order"]["id"]

    assert order.total_charged == zero_money(order.currency)
    assert order.total_authorized == zero_money(order.currency)
    assert order.charge_status == OrderChargeStatus.NONE
    assert order.authorize_status == OrderAuthorizeStatus.NONE

    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT

    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    line_tax_class = order_line.tax_class
    shipping_tax_class = shipping_method.tax_class

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata

    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )

    assert not Checkout.objects.filter()
    assert not len(Reservation.objects.all())
