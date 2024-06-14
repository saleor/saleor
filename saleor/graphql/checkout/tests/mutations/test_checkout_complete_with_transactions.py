from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import before_after
import graphene
import pytest
import pytz
from django.db.models.aggregates import Sum
from django.utils import timezone

from .....account.models import Address
from .....channel import MarkAsPaidStrategy
from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout, CheckoutLine
from .....checkout.payment_utils import update_checkout_payment_statuses
from .....core.taxes import TaxError, zero_money, zero_taxed_money
from .....discount import DiscountType, DiscountValueType, RewardValueType
from .....discount.models import CheckoutLineDiscount, PromotionRule, Voucher
from .....giftcard import GiftCardEvents
from .....giftcard.models import GiftCard, GiftCardEvent
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderOrigin, OrderStatus
from .....order.models import Fulfillment, Order
from .....payment import TransactionEventType
from .....payment.model_helpers import get_subtotal
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....plugins.manager import PluginsManager, get_plugins_manager
from .....product.models import VariantChannelListingPromotionRule
from .....tests.utils import flush_post_commit_hooks
from .....warehouse.models import Reservation, Stock, WarehouseClickAndCollectOption
from .....warehouse.tests.utils import get_available_quantity_for_stock
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


def prepare_checkout_for_test(
    checkout,
    shipping_address,
    billing_address,
    shipping_method,
    transaction_item_generator,
    transaction_events_generator,
):
    checkout.shipping_address = shipping_address
    checkout.shipping_method = shipping_method
    checkout.billing_address = billing_address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, shipping_address
    )
    transaction = transaction_item_generator(checkout_id=checkout.pk)
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
        ],
        amounts=[
            total.gross.amount,
        ],
    )
    recalculate_transaction_amounts(transaction)
    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
        checkout_has_lines=bool(lines),
    )
    return checkout


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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
        checkout_has_lines=bool(lines),
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


def test_checkout_without_any_transaction_allow_to_create_order(
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
    channel.allow_unpaid_orders = True
    channel.order_mark_as_paid_strategy = MarkAsPaidStrategy.TRANSACTION_FLOW
    channel.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
        checkout_has_lines=bool(lines),
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
    assert order.charge_status == OrderChargeStatus.NONE
    assert order.authorize_status == OrderAuthorizeStatus.NONE
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross


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

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross


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

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
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

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
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
    assert order_line.is_price_overridden is False

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


def test_checkout_price_override(
    user_api_client,
    checkout_with_gift_card,
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
    checkout_line.price_override = Decimal("2.0")
    checkout_line.save(update_fields=["price_override"])

    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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
    assert order_line.is_price_overridden is True

    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )

    assert not Checkout.objects.filter()


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

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross


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

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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


def test_checkout_partially_paid_allow_unpaid_order(
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
    channel.allow_unpaid_orders = True
    channel.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=total.gross.amount - Decimal("10")
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
        checkout_has_lines=bool(lines),
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
    assert order.charge_status == OrderChargeStatus.PARTIAL
    assert order.authorize_status == OrderAuthorizeStatus.PARTIAL


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

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross


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

    manager = get_plugins_manager(allow_replica=False)
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
        checkout_has_lines=bool(lines),
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
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
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


def test_checkout_with_voucher_not_applicable(
    user_api_client,
    checkout_with_item_and_voucher,
    voucher,
    address,
    shipping_method,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    Voucher.objects.all().delete()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["field"] == "voucherCode"
    assert data["errors"][0]["code"] == CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.name


def test_checkout_with_voucher_inactive_code(
    user_api_client,
    checkout_with_item_and_voucher,
    voucher,
    address,
    shipping_method,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    code = voucher.codes.first()
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    code.is_active = False
    code.save(update_fields=["is_active"])

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["field"] == "voucherCode"
    assert data["errors"][0]["code"] == CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.name


def test_checkout_with_insufficient_stock(
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name


def test_checkout_with_gift_card_not_applicable(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=1)
    gift_card.save(update_fields=["expiry_date"])

    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["field"] == "giftCards"
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name


def test_checkout_with_variant_without_price(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.channel_listings.filter(channel=checkout.channel).update(
        price_amount=None
    )

    variant_id = to_global_id_or_none(checkout_line_variant)
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutComplete"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [variant_id]


def test_checkout_complete_with_inactive_channel(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    channel = checkout.channel
    channel.is_active = False
    channel.save()

    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name
    assert data["errors"][0]["field"] == "channel"


@pytest.mark.integration
@patch("saleor.order.calculations._recalculate_with_plugins")
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete(
    order_confirmed_mock,
    recalculate_with_plugins_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert str(order.id) == order_token
    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata
    transaction = order.payment_transactions.first()
    assert transaction
    assert order.total_charged_amount == transaction.charged_value
    assert order.total_authorized == zero_money(order.currency)

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
    assert order.search_vector

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )
    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order)
    recalculate_with_plugins_mock.assert_not_called()

    assert not len(Reservation.objects.all())


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata(
    order_confirmed_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    redirect_url = "https://www.example.com"
    metadata_value = "metaValue"
    metadata_key = "metaKey"
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": redirect_url,
        "metadata": [{"key": metadata_key, "value": metadata_value}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    # then
    assert not data["errors"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original

    assert order.metadata == {
        **checkout.metadata_storage.metadata,
        metadata_key: metadata_value,
    }
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order)


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata_updates_existing_keys(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    meta_key = "testKey"
    new_meta_value = "newValue"

    checkout.metadata_storage.store_value_in_metadata(items={meta_key: "oldValue"})
    checkout.metadata_storage.save()

    assert checkout.metadata_storage.metadata[meta_key] != new_meta_value

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    redirect_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": redirect_url,
        "metadata": [{"key": meta_key, "value": new_meta_value}],
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_COMPLETE,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    # then
    assert not data["errors"]
    order = Order.objects.first()
    assert order.metadata == {meta_key: new_meta_value}


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata_checkout_without_metadata(
    order_confirmed_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    # delete the current metadata
    checkout.metadata_storage.delete()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    redirect_url = "https://www.example.com"
    metadata_value = "metaValue"
    metadata_key = "metaKey"
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": redirect_url,
        "metadata": [{"key": metadata_key, "value": metadata_value}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    # then
    assert not data["errors"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original

    assert order.metadata == {
        **checkout.metadata_storage.metadata,
        metadata_key: metadata_value,
    }
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order)


@pytest.mark.integration
@patch("saleor.graphql.checkout.mutations.checkout_complete.complete_checkout")
def test_checkout_complete_by_app(
    mocked_complete_checkout,
    app_api_client,
    checkout_with_item,
    customer_user,
    permission_impersonate_user,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    mocked_complete_checkout.return_value = (None, True, {})
    checkout.user = customer_user
    checkout.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_COMPLETE,
        variables,
        permissions=[permission_impersonate_user],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]

    mocked_complete_checkout.assert_called_once_with(
        checkout_info=ANY,
        lines=ANY,
        manager=ANY,
        payment_data=ANY,
        store_source=ANY,
        user=checkout.user,
        app=ANY,
        site_settings=ANY,
        redirect_url=ANY,
        metadata_list=ANY,
    )


@pytest.mark.integration
@patch("saleor.graphql.checkout.mutations.checkout_complete.complete_checkout")
def test_checkout_complete_by_app_with_missing_permission(
    mocked_complete_checkout,
    app_api_client,
    checkout_with_item,
    customer_user,
    permission_manage_users,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    mocked_complete_checkout.return_value = (None, True, {})
    checkout.user = customer_user
    checkout.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_COMPLETE,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]

    mocked_complete_checkout.assert_called_once_with(
        checkout_info=ANY,
        lines=ANY,
        manager=ANY,
        payment_data=ANY,
        store_source=ANY,
        user=None,
        app=ANY,
        site_settings=ANY,
        redirect_url=ANY,
        metadata_list=ANY,
    )


@patch("saleor.giftcard.utils.send_gift_card_notification")
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_gift_card_bought(
    order_confirmed_mock,
    send_notification_mock,
    site_settings,
    customer_user,
    user_api_client,
    checkout_with_gift_card_items,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card_items,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()
    checkout.user = customer_user
    checkout.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.automatically_fulfill_non_shippable_gift_card = True
    channel.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    flush_post_commit_hooks()
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.status == OrderStatus.PARTIALLY_FULFILLED

    flush_post_commit_hooks()
    gift_card = GiftCard.objects.get()
    assert GiftCardEvent.objects.filter(gift_card=gift_card, type=GiftCardEvents.BOUGHT)
    send_notification_mock.assert_called_once_with(
        customer_user,
        None,
        customer_user,
        customer_user.email,
        gift_card,
        ANY,
        checkout.channel.slug,
        resending=False,
    )
    order_confirmed_mock.assert_called_once_with(order)
    assert Fulfillment.objects.count() == 1


def test_checkout_complete_with_variant_without_sku(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.sku = None
    checkout_line_variant.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_id = graphene.Node.from_global_id(data["order"]["id"])[1]
    assert Order.objects.count() == 1
    order = Order.objects.get(id=order_id)
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT

    order_line = order.lines.first()
    assert order_line.product_sku is None
    assert order_line.product_variant_id == order_line.variant.get_global_id()


@pytest.mark.integration
def test_checkout_with_voucher_complete(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    code = voucher_percentage.codes.first()
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.save(update_fields=["usage_limit"])

    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()

    discount_amount = checkout.discount

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + discount_amount

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"

    order_line = order.lines.first()
    assert (
        order_line.unit_discount_amount
        == (discount_amount / order_line.quantity).amount
    )
    assert order_line.unit_discount_reason


@pytest.mark.integration
def test_checkout_complete_with_voucher_apply_once_per_order(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_voucher_percentage

    code = voucher_percentage.codes.first()
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.apply_once_per_order = True
    voucher_percentage.save(update_fields=["apply_once_per_order", "usage_limit"])

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    discount_amount = checkout_line_variant.channel_listings.get(
        channel=checkout.channel
    ).price * (
        voucher_percentage.channel_listings.get(channel=checkout.channel).discount_value
        / 100
    )
    checkout.discount = discount_amount
    checkout = prepare_checkout_for_test(
        checkout,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + discount_amount

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_with_voucher_single_use(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    code = voucher_percentage.codes.first()
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    voucher_percentage.single_use = True
    voucher_percentage.save(update_fields=["single_use"])

    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()

    discount_amount = checkout.discount

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + discount_amount

    code.refresh_from_db()
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )
    code.refresh_from_db()
    assert code.is_active is False
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_with_voucher_complete_product_on_sale(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    catalogue_promotion_without_rules,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    code = voucher_percentage.codes.first()
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.save(update_fields=["usage_limit"])

    old_sale_id = 1
    catalogue_promotion_without_rules.old_sale_id = old_sale_id
    catalogue_promotion_without_rules.save(update_fields=["old_sale_id"])

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel
    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id(
                        "Product", checkout_line_variant.product.id
                    )
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=checkout_line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        amount_value=reward_value,
        currency=channel.currency_code,
        promotion_rule=rule,
        reason=f"Sale: {graphene.Node.to_global_id('Sale', old_sale_id)}",
    )

    catalogue_promotion_without_rules.name = ""
    catalogue_promotion_without_rules.save(update_fields=["name"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )
    assert order_line.sale_id == graphene.Node.to_global_id(
        "Sale", catalogue_promotion_without_rules.old_sale_id
    )
    assert order_line.unit_discount_reason == (
        f"Entire order voucher code: {code.code} & Sale: {order_line.sale_id}"
    )

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_with_voucher_on_specific_product_complete(
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    code = voucher_specific_product_type.codes.first()
    voucher_used_count = code.used
    voucher_specific_product_type.usage_limit = voucher_used_count + 1
    voucher_specific_product_type.save(update_fields=["usage_limit"])

    checkout.lines.first()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    assert order.voucher == voucher_specific_product_type
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_complete_product_on_promotion(
    user_api_client,
    checkout_with_item,
    catalogue_promotion_without_rules,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id(
                        "Product", checkout_line_variant.product.id
                    )
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=checkout_line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        amount_value=reward_value,
        currency=channel.currency_code,
        promotion_rule=rule,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )
    assert order_line.sale_id == graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )
    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_complete_multiple_rules_applied(
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    catalogue_promotion_without_rules,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel

    reward_value_1 = Decimal("2")
    reward_value_2 = Decimal("10")
    rule_1, rule_2 = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Percentage promotion rule 1",
                promotion=catalogue_promotion_without_rules,
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value_1,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "Product", checkout_line_variant.product_id
                            )
                        ]
                    }
                },
            ),
            PromotionRule(
                name="Percentage promotion rule 2",
                promotion=catalogue_promotion_without_rules,
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=reward_value_2,
                catalogue_predicate={
                    "variantPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "ProductVariant", checkout_line_variant.id
                            )
                        ]
                    }
                },
            ),
        ]
    )

    rule_1.channels.add(channel)
    rule_2.channels.add(channel)

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )
    discount_amount_2 = reward_value_2 / 100 * variant_channel_listing.price.amount
    discounted_price = (
        variant_channel_listing.price.amount - reward_value_1 - discount_amount_2
    )
    variant_channel_listing.discounted_price_amount = discounted_price
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.bulk_create(
        [
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_channel_listing,
                promotion_rule=rule_1,
                discount_amount=reward_value_1,
                currency=channel.currency_code,
            ),
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_channel_listing,
                promotion_rule=rule_2,
                discount_amount=discount_amount_2,
                currency=channel.currency_code,
            ),
        ]
    )

    CheckoutLineDiscount.objects.bulk_create(
        [
            CheckoutLineDiscount(
                line=checkout_line,
                type=DiscountType.PROMOTION,
                value_type=DiscountValueType.FIXED,
                amount_value=reward_value_1,
                currency=channel.currency_code,
                promotion_rule=rule_1,
            ),
            CheckoutLineDiscount(
                line=checkout_line,
                type=DiscountType.PROMOTION,
                value_type=DiscountValueType.FIXED,
                amount_value=discount_amount_2,
                currency=channel.currency_code,
                promotion_rule=rule_2,
            ),
        ]
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    assert order_line.sale_id == graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )
    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_with_voucher_on_specific_product_complete_with_product_on_promotion(
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    catalogue_promotion_with_single_rule,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    code = voucher_specific_product_type.codes.first()
    voucher_used_count = code.used
    voucher_specific_product_type.usage_limit = voucher_used_count + 1
    voucher_specific_product_type.save(update_fields=["usage_limit"])

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant_id = graphene.Node.to_global_id(
        "ProductVariant", checkout_line_variant.id
    )

    rule = catalogue_promotion_with_single_rule.rules.first()
    predicate = {"variantPredicate": {"ids": [checkout_line_variant_id]}}
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert order.total == total
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@patch.object(PluginsManager, "preprocess_order_creation")
@pytest.mark.integration
def test_checkout_with_voucher_not_increase_uses_on_preprocess_order_creation_failure(
    mocked_preprocess_order_creation,
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    mocked_preprocess_order_creation.side_effect = TaxError("tax error!")
    code = voucher_percentage.codes.first()
    code.used = 0
    voucher_percentage.usage_limit = 1
    voucher_percentage.save(update_fields=["usage_limit"])
    code.save(update_fields=["used"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["code"] == CheckoutErrorCode.TAX_ERROR.name

    code.refresh_from_db()
    assert code.used == 0

    assert Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout shouldn't have been deleted"


@pytest.mark.integration
def test_checkout_complete_without_inventory_tracking(
    user_api_client,
    checkout_with_variant_without_inventory_tracking,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_variant_without_inventory_tracking,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert not order_line.allocations.all()


def test_checkout_complete_checkout_without_lines(
    site_settings,
    user_api_client,
    checkout,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    assert not lines
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.NO_LINES.name


def test_checkout_complete_insufficient_stock_reserved_by_other_user(
    site_settings_with_reservations,
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    channel_USD,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

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

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()


def test_checkout_complete_own_reservation(
    site_settings_with_reservations,
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    channel_USD,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)

    checkout_line.quantity = quantity_available
    checkout_line.save()

    reservation = Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=quantity_available,
        reserved_until=timezone.now() + timedelta(minutes=5),
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert order_line.quantity == quantity_available
    assert order_line.variant == checkout_line.variant

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"

    # Reservation associated with checkout has been deleted
    with pytest.raises(Reservation.DoesNotExist):
        reservation.refresh_from_db()


def test_checkout_complete_without_redirect_url(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )
    variables = {"id": to_global_id_or_none(checkout)}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_complete_with_digital(
    api_client,
    checkout_with_digital_item,
    address,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_digital_item,
        address,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert not content["errors"]

    # Ensure the order was actually created
    assert Order.objects.count() == 1, "The order should have been created"


def test_complete_checkout_for_local_click_and_collect(
    api_client,
    checkout_with_item_for_cc,
    address,
    warehouse_for_cc,
    warehouse,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_for_cc,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )
    checkout.collection_point = warehouse_for_cc
    checkout.shipping_address = None
    checkout.save(update_fields=["collection_point", "shipping_address"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    line = checkout.lines.first()
    variant = line.variant

    # create another stock for the variant with the bigger quantity available
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=15)

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert not content["errors"]
    assert Order.objects.count() == 1

    order = Order.objects.first()

    assert order.collection_point == warehouse_for_cc
    assert order.shipping_method is None
    assert order.shipping_address
    assert order.shipping_address.id != warehouse_for_cc.address.id
    assert order.shipping_price == zero_taxed_money(order.channel.currency_code)
    assert order.lines.count() == 1

    # ensure the allocation is made on the correct warehouse
    assert order.lines.first().allocations.first().stock.warehouse == warehouse_for_cc


def test_complete_checkout_for_global_click_and_collect(
    api_client,
    checkout_with_item_for_cc,
    address,
    warehouse_for_cc,
    warehouse,
    transaction_events_generator,
    transaction_item_generator,
):
    """Test that click-and-collect prefers the local stock even if other warehouses hold more stock."""
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_for_cc,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )

    warehouse_for_cc.click_and_collect_option = (
        WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )
    warehouse_for_cc.save(update_fields=["click_and_collect_option"])

    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["collection_point"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    line = checkout.lines.first()
    variant = line.variant

    # create another stock for the variant with the bigger quantity available
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=50)

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert not content["errors"]
    assert Order.objects.count() == 1

    order = Order.objects.latest("created_at")

    assert order.collection_point == warehouse_for_cc
    assert order.shipping_method is None
    assert order.shipping_address
    assert order.shipping_address.id != warehouse_for_cc.address.id
    assert order.shipping_price == zero_taxed_money(order.channel.currency_code)
    assert order.lines.count() == 1

    # ensure the allocation is made on the correct warehouse
    assert order.lines.first().allocations.first().stock.warehouse == warehouse_for_cc


def test_complete_checkout_raises_error_for_local_stock(
    api_client,
    checkout_with_item_for_cc,
    address,
    warehouse_for_cc,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_for_cc,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "rediirectUrl": "https://www.example.com",
    }

    checkout.collection_point = warehouse_for_cc
    checkout.save(
        update_fields=[
            "collection_point",
        ]
    )

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert content["errors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert Order.objects.count() == 0


def test_comp_checkout_builds_order_for_all_warehouse_even_if_not_available_locally(
    stocks_for_cc,
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    api_client,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_for_cc,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )
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

    variables = {
        "id": to_global_id_or_none(checkout),
        "rediirectUrl": "https://www.example.com",
    }

    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["collection_point"])

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert not content["errors"]
    assert Order.objects.count() == 1


def test_checkout_complete_raises_InsufficientStock_when_quantity_above_stock_sum(
    stocks_for_cc,
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    api_client,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_for_cc,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )
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

    variables = {
        "id": to_global_id_or_none(checkout),
        "rediirectUrl": "https://www.example.com",
    }

    checkout.collection_point = warehouse_for_cc
    checkout.save(
        update_fields=[
            "collection_point",
        ]
    )

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert content["errors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert Order.objects.count() == 0


def test_checkout_complete_raises_InvalidShippingMethod_when_warehouse_disabled(
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    api_client,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_for_cc,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    checkout.collection_point = warehouse_for_cc

    checkout.save(update_fields=["collection_point"])

    warehouse_for_cc.click_and_collect_option = WarehouseClickAndCollectOption.DISABLED
    warehouse_for_cc.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    assert not checkout_info.valid_pick_up_points
    assert not checkout_info.delivery_method_info.is_method_in_valid_methods(
        checkout_info
    )
    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert (
        content["errors"][0]["code"] == CheckoutErrorCode.INVALID_SHIPPING_METHOD.name
    )
    assert Order.objects.count() == 0


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_preorder_variant(
    order_confirmed_mock,
    site_settings,
    user_api_client,
    checkout_with_item_and_preorder_item,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_preorder_item,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    variants_and_quantities = {line.variant_id: line.quantity for line in checkout}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    assert order.subtotal.gross == get_subtotal(order.lines.all(), order.currency).gross

    assert order.lines.count() == len(variants_and_quantities)
    for variant_id, quantity in variants_and_quantities.items():
        assert order.lines.get(variant_id=variant_id).quantity == quantity

    preorder_line = order.lines.filter(variant__is_preorder=True).first()
    assert not preorder_line.allocations.exists()
    preorder_allocation = preorder_line.preorder_allocations.get()
    assert preorder_allocation.quantity == preorder_line.quantity

    stock_line = order.lines.filter(variant__is_preorder=False).first()
    assert stock_line.allocations.exists()
    assert not stock_line.preorder_allocations.exists()

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order)


def test_checkout_complete_with_click_collect_preorder_fails_for_disabled_warehouse(
    warehouse_for_cc,
    checkout_with_items_for_cc,
    address,
    api_client,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items_for_cc,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

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

    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["collection_point"])

    warehouse_for_cc.click_and_collect_option = WarehouseClickAndCollectOption.DISABLED
    warehouse_for_cc.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    assert not checkout_info.valid_pick_up_points
    assert not checkout_info.delivery_method_info.is_method_in_valid_methods(
        checkout_info
    )

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert (
        content["errors"][0]["code"] == CheckoutErrorCode.INVALID_SHIPPING_METHOD.name
    )
    assert Order.objects.count() == 0


def test_checkout_complete_variant_channel_listing_does_not_exist(
    user_api_client,
    checkout_with_items,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.channel_listings.get(channel__id=checkout.channel_id).delete()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == 0
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_complete_variant_channel_listing_no_price(
    user_api_client,
    checkout_with_items,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    variants = []
    for line in checkout.lines.all()[:2]:
        checkout_line_variant = line.variant
        variants.append(checkout_line_variant)
        variant_channel_listing = checkout_line_variant.channel_listings.get(
            channel__id=checkout.channel_id
        )
        variant_channel_listing.price_amount = None
        variant_channel_listing.save(update_fields=["price_amount"])

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert set(errors[0]["variants"]) == {
        graphene.Node.to_global_id("ProductVariant", variant.pk) for variant in variants
    }

    assert Order.objects.count() == 0
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_complete_product_channel_listing_does_not_exist(
    user_api_client,
    checkout_with_items,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.product.channel_listings.get(
        channel__id=checkout.channel_id
    ).delete()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == 0
    assert Checkout.objects.filter(pk=checkout.pk).exists()


@pytest.mark.parametrize(
    "available_for_purchase", [None, datetime.now(pytz.UTC) + timedelta(days=1)]
)
def test_checkout_complete_product_channel_listing_not_available_for_purchase(
    user_api_client,
    checkout_with_items,
    address,
    shipping_method,
    available_for_purchase,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    product_channel_listings = checkout_line_variant.product.channel_listings.get(
        channel__id=checkout.channel_id
    )
    product_channel_listings.available_for_purchase_at = available_for_purchase
    product_channel_listings.save(update_fields=["available_for_purchase_at"])

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == 0
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_complete_error_when_shipping_address_doesnt_have_all_required_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    shipping_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
    )  # missing postalCode

    checkout = prepare_checkout_for_test(
        checkout_with_item,
        shipping_address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1

    assert data["errors"][0]["code"] == "REQUIRED"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == 0


def test_checkout_complete_error_when_shipping_address_doesnt_have_all_valid_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    shipping_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
        postal_code="XX-ABC",
    )  # incorrect postalCode

    checkout = prepare_checkout_for_test(
        checkout_with_item,
        shipping_address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1

    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == 0


def test_checkout_complete_error_when_billing_address_doesnt_have_all_required_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    billing_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
    )  # missing postalCode

    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        billing_address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "REQUIRED"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == 0


def test_checkout_complete_error_when_billing_address_doesnt_have_all_valid_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    billing_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
        postal_code="XX-ABC",
    )  # incorrect postalCode

    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        billing_address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1

    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == 0


def test_checkout_complete_with_not_normalized_shipping_address(
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given

    shipping_address = Address.objects.create(
        country="US",
        city="Washington",
        country_area="District of Columbia",
        street_address_1="1600 Pennsylvania Avenue NW",
        postal_code="20500",
    )
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        shipping_address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.first()
    shipping_address = order.shipping_address
    assert shipping_address
    assert shipping_address.city == "WASHINGTON"
    assert shipping_address.country_area == "DC"


def test_checkout_complete_with_not_normalized_billing_address(
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    billing_address = Address.objects.create(
        country="US",
        city="Washington",
        country_area="District of Columbia",
        street_address_1="1600 Pennsylvania Avenue NW",
        postal_code="20500",
    )
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        billing_address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.first()
    billing_address = order.billing_address
    assert billing_address
    assert billing_address.city == "WASHINGTON"
    assert billing_address.country_area == "DC"


def test_checkout_complete_reservations_drop(
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert not len(Reservation.objects.all())


@pytest.mark.integration
def test_checkout_complete_line_deleted_in_the_meantime(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        shipping_method,
        transaction_item_generator,
        transaction_events_generator,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    def delete_order_line(*args, **kwargs):
        CheckoutLine.objects.get(id=checkout.lines.first().id).delete()

    # when
    with before_after.before(
        "saleor.graphql.checkout.mutations.checkout_complete.complete_checkout",
        delete_order_line,
    ):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["order"]
    assert not data["errors"]
    assert Order.objects.count() == 1
    assert not Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_complete_with_invalid_address(
    user_api_client,
    checkout_with_item,
    transaction_item_generator,
    address,
    shipping_method,
):
    """Check if checkout can be completed with invalid address.

    After introducing `AddressInput.skip_validation`, Saleor may have invalid address
    stored in database.
    """
    # given
    checkout = checkout_with_item

    invalid_postal_code = "invalid postal code"
    address.postal_code = invalid_postal_code
    address.validation_skipped = True
    address.save(update_fields=["validation_skipped", "postal_code"])

    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.allow_unpaid_orders = True
    channel.order_mark_as_paid_strategy = MarkAsPaidStrategy.TRANSACTION_FLOW
    channel.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    update_checkout_payment_statuses(
        checkout=checkout_info.checkout,
        checkout_total_gross=total.gross,
        checkout_has_lines=bool(lines),
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
    assert order.shipping_address.postal_code == invalid_postal_code
    assert order.billing_address.postal_code == invalid_postal_code
