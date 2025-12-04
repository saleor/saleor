import datetime
from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from django.db import transaction
from django.db.models.aggregates import Sum
from django.test import override_settings
from django.utils import timezone
from prices import TaxedMoney

from .....account.models import Address
from .....channel import MarkAsPaidStrategy
from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    fetch_shipping_methods_for_checkout,
    get_or_fetch_checkout_deliveries,
)
from .....checkout.models import Checkout, CheckoutDelivery, CheckoutLine
from .....checkout.payment_utils import update_checkout_payment_statuses
from .....checkout.utils import PRIVATE_META_APP_SHIPPING_ID, add_voucher_to_checkout
from .....core.taxes import TaxError, zero_money, zero_taxed_money
from .....discount import DiscountType, DiscountValueType, RewardValueType
from .....discount.models import (
    CheckoutLineDiscount,
    OrderLineDiscount,
    PromotionRule,
    Voucher,
)
from .....giftcard import GiftCardEvents
from .....giftcard.models import GiftCard, GiftCardEvent
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderOrigin, OrderStatus
from .....order.models import Fulfillment, Order
from .....payment import TransactionEventType
from .....payment.model_helpers import get_subtotal
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....plugins.manager import PluginsManager, get_plugins_manager
from .....product.models import (
    ProductChannelListing,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from .....shipping.models import ShippingMethod
from .....tests import race_condition
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
                status
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
                shippingMethod {
                    id
                    name
                    metadata {
                        key
                        value
                    }
                }
                deliveryMethod {
                    ... on ShippingMethod {
                        id
                        name
                        metadata {
                            key
                            value
                        }
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
    checkout_delivery,
    transaction_item_generator,
    transaction_events_generator,
    voucher=None,
    user=None,
    save_shipping_address=None,
    save_billing_address=None,
):
    checkout.shipping_address = shipping_address
    checkout.assigned_delivery = checkout_delivery
    checkout.billing_address = billing_address
    if save_shipping_address is not None:
        checkout.save_shipping_address = save_shipping_address
    if save_billing_address is not None:
        checkout.save_billing_address = save_billing_address
    checkout.user = user
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    if voucher:
        add_voucher_to_checkout(
            manager,
            checkout_info,
            lines,
            voucher,
            voucher.codes.first(),
        )

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

    # Set price expiration to force payment status recalculcation upon fetching checkout
    # data.
    checkout.price_expiration = timezone.now()
    checkout.save()

    return checkout


def test_checkout_without_any_transaction(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
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
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
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

    assert order.lines_count == len(lines)


def test_checkout_with_total_0(
    checkout_with_item_total_0,
    user_api_client,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
    channel_USD,
    checkout_delivery,
):
    # given
    shipping_method.channel_listings.update(price_amount=Decimal(0))

    checkout = checkout_with_item_total_0
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
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
    assert order.shipping_price_gross_amount == 0
    assert order.base_shipping_price_amount == 0
    assert order.undiscounted_base_shipping_price_amount == 0

    assert order.lines_count == len(lines)


def test_checkout_with_authorized(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    customer_user,
    checkout_delivery,
    shipping_method,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.user = customer_user
    checkout.save()
    checkout.metadata_storage.save()

    user_number_of_orders = customer_user.number_of_orders

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()

    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price

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
    assert order.shipping_method.id == int(
        checkout.assigned_delivery.shipping_method_id
    )
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )
    assert order.shipping_price_gross_amount == shipping_price.amount
    assert order.base_shipping_price_amount == shipping_price.amount
    assert order.undiscounted_base_shipping_price_amount == shipping_price.amount

    assert order.lines_count == len(lines)

    assert not Checkout.objects.filter()
    assert not len(Reservation.objects.all())

    customer_user.refresh_from_db()
    assert customer_user.number_of_orders == user_number_of_orders + 1


def test_checkout_with_charged(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    customer_user,
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.user = customer_user
    checkout.save()
    checkout.metadata_storage.save()

    user_number_of_orders = customer_user.number_of_orders

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

    assigned_checkout_shipping = checkout.assigned_delivery
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata
    assert order_line.is_price_overridden is False

    assert order.shipping_address == address
    assert order.shipping_method_id == int(
        assigned_checkout_shipping.shipping_method_id
    )
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == assigned_checkout_shipping.tax_class_name
    assert (
        order.shipping_tax_class_metadata
        == assigned_checkout_shipping.tax_class_metadata
    )
    assert (
        order.shipping_tax_class_private_metadata
        == assigned_checkout_shipping.tax_class_private_metadata
    )

    assert order.lines_count == len(lines)

    assert not Checkout.objects.filter()
    assert not len(Reservation.objects.all())

    customer_user.refresh_from_db()
    assert customer_user.number_of_orders == user_number_of_orders + 1


def test_checkout_price_override(
    user_api_client,
    checkout_with_gift_card,
    transaction_item_generator,
    address,
    shipping_method,
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
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

    assigned_delivery = checkout.assigned_delivery

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata
    assert order_line.is_price_overridden is True
    assert (
        order_line.undiscounted_unit_price_gross_amount == checkout_line.price_override
    )

    assert order.shipping_address == address
    assert order.shipping_method.id == int(assigned_delivery.shipping_method_id)
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class.id == assigned_delivery.tax_class_id
    assert order.shipping_tax_class_name == assigned_delivery.tax_class_name
    assert order.shipping_tax_class_metadata == assigned_delivery.tax_class_metadata
    assert (
        order.shipping_tax_class_private_metadata
        == assigned_delivery.tax_class_private_metadata
    )

    assert order.lines_count == len(lines)

    assert not Checkout.objects.filter()


def test_checkout_paid_with_multiple_transactions(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    transaction_item_generator,
    address,
    shipping_method,
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
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
        checkout_id=checkout.pk, charged_value=total.gross.amount - Decimal(10)
    )
    second_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10)
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
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
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
        checkout_id=checkout.pk, charged_value=total.gross.amount - Decimal(10)
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
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
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
        checkout_id=checkout.pk, charged_value=total.gross.amount - Decimal(10)
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
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
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
    checkout_delivery,
):
    # given
    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
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
    assert order.shipping_method.id == int(
        checkout.assigned_delivery.shipping_method_id
    )
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
    transaction_item_generator,
    transaction_events_generator,
    checkout_delivery,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher,
        address,
        address,
        checkout_delivery(checkout_with_item_and_voucher),
        transaction_item_generator,
        transaction_events_generator,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    calculations.fetch_checkout_data(
        checkout_info,
        manager,
        lines,
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
    transaction_item_generator,
    transaction_events_generator,
    checkout_delivery,
):
    # given
    code = voucher.codes.first()
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher,
        address,
        address,
        checkout_delivery(checkout_with_item_and_voucher),
        transaction_item_generator,
        transaction_events_generator,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    calculations.fetch_checkout_data(
        checkout_info,
        manager,
        lines,
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
    checkout_delivery,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item),
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    stock.quantity = 0
    stock.save(update_fields=["quantity"])

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
    checkout_delivery,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    gift_card.expiry_date = datetime.datetime.now(
        tz=datetime.UTC
    ).date() - datetime.timedelta(days=1)
    gift_card.save(update_fields=["expiry_date"])

    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item),
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


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_with_line_without_channel_listing(
    channel_listing_model,
    listing_filter_field,
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item),
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: checkout_line.variant_id},
    ).delete()

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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
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
    address_usa,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    caplog,
    customer_user,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address_usa,
        checkout_delivery(checkout_with_gift_card),
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
    )

    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    customer_user.addresses.clear()
    user_address_count = customer_user.addresses.count()

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
    assigned_delivery = checkout.assigned_delivery

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata

    assert order.billing_address.id == address_usa.id
    assert order.shipping_address == address
    assert order.draft_save_billing_address is None
    assert order.draft_save_shipping_address is None
    assert order.shipping_method.id == int(assigned_delivery.shipping_method_id)
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class.id == assigned_delivery.tax_class_id
    assert order.shipping_tax_class_name == assigned_delivery.tax_class_name
    assert order.shipping_tax_class_metadata == assigned_delivery.tax_class_metadata
    assert (
        order.shipping_tax_class_private_metadata
        == assigned_delivery.tax_class_private_metadata
    )
    assert order.search_vector

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )
    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())
    recalculate_with_plugins_mock.assert_not_called()

    assert not len(Reservation.objects.all())

    assert (
        graphene.Node.to_global_id("Checkout", checkout_info.checkout.pk)
        == caplog.records[0].checkout_id
    )
    assert gift_card.initial_balance_amount == Decimal(
        caplog.records[0].gift_card_compensation
    )
    assert total.gross.amount == Decimal(
        caplog.records[0].total_after_gift_card_compensation
    )

    assert customer_user.addresses.count() == user_address_count + 2
    # ensure the the customer addresses are not the same instances as the order addresses
    customer_address_ids = list(customer_user.addresses.values_list("pk", flat=True))
    assert not (
        set(customer_address_ids)
        & {order.billing_address.pk, order.shipping_address.pk}
    )
    assert order.draft_save_billing_address is None
    assert order.draft_save_shipping_address is None


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata(
    order_confirmed_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata_updates_existing_keys(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())


@pytest.mark.integration
@patch("saleor.graphql.checkout.mutations.checkout_complete.complete_checkout")
def test_checkout_complete_by_app(
    mocked_complete_checkout,
    app_api_client,
    checkout_with_item,
    customer_user,
    permission_impersonate_user,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card_items,
        address,
        address,
        checkout_delivery(checkout_with_gift_card_items),
        transaction_item_generator,
        transaction_events_generator,
    )
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.email = customer_user.email
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

    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.status == OrderStatus.PARTIALLY_FULFILLED

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
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())
    assert Fulfillment.objects.count() == 1


@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_shipping_voucher_and_gift_card(
    order_confirmed_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    checkout_delivery,
    voucher_free_shipping,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    shipping_listing = shipping_method.channel_listings.get(
        channel_id=checkout_with_gift_card.channel_id
    )
    shipping_listing.price_amount = Decimal(35)
    shipping_listing.save(update_fields=["price_amount"])

    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
        voucher=voucher_free_shipping,
    )
    shipping_price = shipping_listing.price

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
    subtotal = get_subtotal(order.lines.all(), order.currency).gross
    assert order.subtotal.gross == subtotal
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata
    transaction = order.payment_transactions.first()
    assert transaction
    assert order.total_charged_amount == transaction.charged_value
    assert order.total_authorized == zero_money(order.currency)
    assert order.shipping_price == zero_taxed_money(order.currency)
    assert order.undiscounted_total == TaxedMoney(
        net=subtotal + shipping_price, gross=subtotal + shipping_price
    )

    order_line = order.lines.first()
    line_tax_class = order_line.tax_class
    assigned_delivery = checkout.assigned_delivery

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata

    assert order.shipping_address == address
    assert order.shipping_method.id == int(assigned_delivery.shipping_method_id)
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class.id == assigned_delivery.tax_class_id
    assert order.shipping_tax_class_name == assigned_delivery.tax_class_name
    assert order.shipping_tax_class_metadata == assigned_delivery.tax_class_metadata
    assert (
        order.shipping_tax_class_private_metadata
        == assigned_delivery.tax_class_private_metadata
    )
    assert order.search_vector

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )
    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())

    assert not len(Reservation.objects.all())


def test_checkout_complete_with_variant_without_sku(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item),
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


@pytest.mark.parametrize(
    (
        "legacy_discount_propagation",
        "expected_unit_discount_amount",
        "expected_unit_discount_reason",
    ),
    [
        (True, Decimal(1), "Entire order voucher code: saleor"),
        (False, Decimal(0), None),
    ],
)
@pytest.mark.integration
def test_checkout_with_voucher_complete(
    legacy_discount_propagation,
    expected_unit_discount_amount,
    expected_unit_discount_reason,
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    channel = checkout_with_voucher_percentage.channel
    channel.use_legacy_line_discount_propagation_for_order = legacy_discount_propagation
    channel.save()

    code = voucher_percentage.codes.first()
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        checkout_delivery(checkout_with_voucher_percentage, shipping_method),
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

    total = calculations.calculate_checkout_total(
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )

    order_line = order.lines.first()
    assert order_line.unit_discount_amount == expected_unit_discount_amount
    assert order_line.unit_discount_reason == expected_unit_discount_reason


@pytest.mark.parametrize(
    (
        "legacy_propagation",
        "expected_unit_discount_amount",
    ),
    [
        (True, Decimal("1.67")),
        (
            False,
            Decimal(0),
        ),
    ],
)
@pytest.mark.integration
def test_checkout_with_order_promotion_complete(
    legacy_propagation,
    expected_unit_discount_amount,
    user_api_client,
    checkout_with_item_and_order_discount,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_item_and_order_discount

    channel = checkout.channel
    channel.use_legacy_line_discount_propagation_for_order = legacy_propagation
    channel.save()

    checkout = prepare_checkout_for_test(
        checkout,
        address,
        address,
        checkout_delivery(checkout, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )

    discount_amount = checkout.discount

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total(
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )

    order_line = order.lines.first()
    assert order_line.unit_discount_amount == expected_unit_discount_amount
    assert order_line.unit_discount_reason is None

    order_discount = order.discounts.filter(type=DiscountType.ORDER_PROMOTION).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )


@pytest.mark.integration
def test_checkout_complete_with_entire_order_voucher_paid_with_gift_card_and_transaction(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    gift_card,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout_with_voucher_percentage.gift_cards.add(gift_card)
    code = voucher_percentage.codes.first()

    shipping_listing = shipping_method.channel_listings.get(
        channel_id=checkout_with_voucher_percentage.channel_id
    )
    shipping_listing.price_amount = Decimal(35)
    shipping_listing.save(update_fields=["price_amount"])

    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        checkout_delivery(checkout_with_voucher_percentage, shipping_method),
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

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price
    gift_card_initial_balance = gift_card.initial_balance_amount

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
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal.gross == subtotal.gross
    assert order.undiscounted_total == subtotal + shipping_price + discount_amount

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
        - gift_card_initial_balance
    )
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )

    order_line = order.lines.first()
    assert (
        order_line.unit_discount_amount
        == (discount_amount / order_line.quantity).amount
    )
    assert order_line.unit_discount_reason

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


@pytest.mark.integration
def test_checkout_complete_with_voucher_paid_with_gift_card(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    gift_card,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        checkout_delivery(checkout_with_voucher_percentage, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )
    checkout.gift_cards.add(gift_card)

    code = voucher_percentage.codes.first()
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.save(update_fields=["usage_limit"])

    expected_voucher_discount = checkout.discount

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total_without_gc = calculations.calculate_checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    gift_card.initial_balance_amount = total_without_gc.gross.amount + Decimal(1)
    gift_card.current_balance_amount = total_without_gc.gross.amount + Decimal(1)
    gift_card.save()

    expected_gc_balance_amount = (
        gift_card.initial_balance_amount - total_without_gc.gross.amount
    )

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price

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

    order = Order.objects.get()
    assert order.total == total
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal.gross == subtotal.gross
    assert (
        order.undiscounted_total
        == subtotal + shipping_price + expected_voucher_discount
    )

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert order_discount.amount_value == expected_voucher_discount.amount
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )

    order_line = order.lines.first()
    assert (
        order_line.unit_discount_amount
        == (expected_voucher_discount / order_line.quantity).amount
    )
    assert order_line.unit_discount_reason

    gift_card.refresh_from_db()
    assert gift_card.current_balance.amount == expected_gc_balance_amount
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


@pytest.mark.parametrize(
    (
        "use_legacy_discount_propagation",
        "expected_voucher_discount_value_type",
        "expected_voucher_discount_value",
    ),
    [
        (True, DiscountValueType.FIXED, Decimal(1)),
        (False, DiscountValueType.PERCENTAGE, Decimal(10)),
    ],
)
@pytest.mark.integration
def test_checkout_complete_with_voucher_apply_once_per_order(
    use_legacy_discount_propagation,
    expected_voucher_discount_value_type,
    expected_voucher_discount_value,
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    channel_USD,
):
    # given
    channel_USD.use_legacy_line_discount_propagation_for_order = (
        use_legacy_discount_propagation
    )
    channel_USD.save()

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
        checkout_delivery(checkout, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total(
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
    order_line_discount = OrderLineDiscount.objects.get()
    assert order_line_discount
    assert (
        order_line_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.voucher == voucher_percentage
    assert order_line_discount.voucher_code == code.code
    assert order_line_discount.value_type == expected_voucher_discount_value_type
    assert order_line_discount.value == expected_voucher_discount_value

    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not order.discounts.exists()

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


@pytest.mark.integration
def test_checkout_complete_with_voucher_apply_once_per_order_and_gift_card(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    gift_card,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_voucher_percentage
    checkout_with_voucher_percentage.gift_cards.add(gift_card)
    code = voucher_percentage.codes.first()

    shipping_listing = shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    )
    shipping_listing.price_amount = Decimal(35)
    shipping_listing.save(update_fields=["price_amount"])

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
        checkout_delivery(checkout, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price
    gift_card_initial_balance = gift_card.initial_balance_amount

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
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal.gross == subtotal.gross
    assert order.undiscounted_total == subtotal + shipping_price + discount_amount

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_line_discount = OrderLineDiscount.objects.get()
    assert order_line_discount
    assert (
        order_line_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
        - gift_card_initial_balance
    )
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.voucher == voucher_percentage
    assert order_line_discount.voucher_code == code.code
    assert order_line_discount.value_type == DiscountValueType.FIXED

    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


@pytest.mark.integration
def test_checkout_complete_with_voucher_single_use(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    code = voucher_percentage.codes.first()
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        checkout_delivery(checkout_with_voucher_percentage, shipping_method),
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

    total = calculations.calculate_checkout_total(
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_shipping_voucher(
    order_confirmed_mock,
    user_api_client,
    checkout_with_voucher_free_shipping,
    address,
    shipping_method,
    checkout_delivery,
    voucher_free_shipping,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_voucher_free_shipping
    shipping_listing = shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    )
    shipping_listing.price_amount = Decimal(35)
    shipping_listing.save(update_fields=["price_amount"])
    checkout.discount = shipping_listing.price
    checkout.save(update_fields=["discount_amount"])

    checkout = prepare_checkout_for_test(
        checkout,
        address,
        address,
        checkout_delivery(checkout, shipping_method),
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
    assert order.voucher == voucher_free_shipping
    assert not order.original
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert str(order.id) == order_token
    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata
    transaction = order.payment_transactions.first()
    assert transaction
    assert order.total_charged_amount == transaction.charged_value
    assert order.shipping_price == zero_taxed_money(order.currency)

    order_line = order.lines.first()
    line_tax_class = order_line.tax_class
    shipping_tax_class = shipping_method.tax_class

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata
    assert not order_line.unit_discount_reason
    assert not order_line.unit_discount_amount

    assert order.shipping_address == address
    assert order.shipping_method.id == int(
        checkout.assigned_delivery.shipping_method_id
    )
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )
    assert order.search_vector

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())

    assert not len(Reservation.objects.all())


def test_checkout_with_voucher_complete_product_on_sale(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    catalogue_promotion_without_rules,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        checkout_delivery(checkout_with_voucher_percentage, shipping_method),
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
    reward_value = Decimal(5)
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

    total = calculations.calculate_checkout_total(
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


@pytest.mark.parametrize(
    (
        "use_legacy_discount_propagation",
        "expected_voucher_discount_value_type",
        "expected_voucher_discount_value",
    ),
    [
        (True, DiscountValueType.FIXED, Decimal(3)),
        (False, DiscountValueType.PERCENTAGE, Decimal(10)),
    ],
)
def test_checkout_with_voucher_on_specific_product_complete(
    use_legacy_discount_propagation,
    expected_voucher_discount_value_type,
    expected_voucher_discount_value,
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    channel_USD,
):
    # given
    channel_USD.use_legacy_line_discount_propagation_for_order = (
        use_legacy_discount_propagation
    )
    channel_USD.save()

    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address,
        checkout_delivery(
            checkout_with_item_and_voucher_specific_products, shipping_method
        ),
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

    total = calculations.calculate_checkout_total(
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

    order_line_discount = OrderLineDiscount.objects.get()
    assert order_line_discount
    assert (
        order_line_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.voucher == voucher_specific_product_type
    assert order_line_discount.voucher_code == code.code
    assert order_line_discount.value_type == expected_voucher_discount_value_type
    assert order_line_discount.value == expected_voucher_discount_value

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    assert order.voucher == voucher_specific_product_type
    assert order.voucher.code == code.code

    assert not order.discounts.exists()

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


def test_checkout_complete_with_voucher_on_specific_product_and_gift_card(
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    gift_card,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    checkout_with_item_and_voucher_specific_products.gift_cards.add(gift_card)

    shipping_listing = shipping_method.channel_listings.get(
        channel_id=checkout_with_item_and_voucher_specific_products.channel_id
    )
    shipping_listing.price_amount = Decimal(35)
    shipping_listing.save(update_fields=["price_amount"])

    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address,
        checkout_delivery(
            checkout_with_item_and_voucher_specific_products, shipping_method
        ),
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

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price
    gift_card_initial_balance = gift_card.initial_balance_amount

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
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
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal.gross == subtotal.gross
    assert (
        order.undiscounted_total
        == subtotal
        + (order_line.undiscounted_total_price - order_line.total_price)
        + shipping_price
    )

    order_line_discount = OrderLineDiscount.objects.get()
    assert order_line_discount
    assert (
        order_line_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
        - gift_card_initial_balance
    )
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.voucher == voucher_specific_product_type
    assert order_line_discount.voucher_code == code.code
    assert order_line_discount.value_type == DiscountValueType.FIXED

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    assert order.voucher == voucher_specific_product_type
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


def test_checkout_complete_product_on_promotion(
    user_api_client,
    checkout_with_item,
    catalogue_promotion_without_rules,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel

    reward_value = Decimal(5)
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

    total = calculations.calculate_checkout_total(
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
    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


def test_checkout_complete_multiple_rules_applied(
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    checkout_delivery,
    catalogue_promotion_without_rules,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel

    reward_value_1 = Decimal(2)
    reward_value_2 = Decimal(10)
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

    total = calculations.calculate_checkout_total(
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
    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


@pytest.mark.parametrize(
    (
        "use_legacy_discount_propagation",
        "expected_voucher_discount_value_type",
        "expected_voucher_discount_value",
    ),
    [
        (True, DiscountValueType.FIXED, Decimal(3)),
        (False, DiscountValueType.PERCENTAGE, Decimal(10)),
    ],
)
def test_checkout_with_voucher_on_specific_product_complete_with_product_on_promotion(
    use_legacy_discount_propagation,
    expected_voucher_discount_value_type,
    expected_voucher_discount_value,
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    catalogue_promotion_with_single_rule,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    channel_USD,
):
    # given
    channel_USD.use_legacy_line_discount_propagation_for_order = (
        use_legacy_discount_propagation
    )
    channel_USD.save()

    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address,
        checkout_delivery(
            checkout_with_item_and_voucher_specific_products, shipping_method
        ),
        transaction_item_generator,
        transaction_events_generator,
    )
    code = voucher_specific_product_type.codes.first()
    voucher_used_count = code.used
    voucher_specific_product_type.usage_limit = voucher_used_count + 1
    voucher_specific_product_type.save(update_fields=["usage_limit"])

    voucher_expected_value = Decimal(10)
    voucher_specific_product_type.channel_listings.update(
        discount_value=voucher_expected_value
    )
    assert (
        voucher_specific_product_type.discount_value_type
        == DiscountValueType.PERCENTAGE
    )

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

    total = calculations.calculate_checkout_total(
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

    line_voucher_discount = order_line.discounts.get(type=DiscountType.VOUCHER)
    assert line_voucher_discount.value_type == expected_voucher_discount_value_type
    assert line_voucher_discount.value == expected_voucher_discount_value

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1

    assert not order.discounts.exists()

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


@patch.object(PluginsManager, "preprocess_order_creation")
@pytest.mark.integration
def test_checkout_with_voucher_not_increase_uses_on_preprocess_order_creation_failure(
    mocked_preprocess_order_creation,
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_voucher_percentage,
        address,
        address,
        checkout_delivery(checkout_with_voucher_percentage, shipping_method),
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

    assert Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout shouldn't have been deleted"
    )


@pytest.mark.integration
def test_checkout_complete_without_inventory_tracking(
    user_api_client,
    checkout_with_variant_without_inventory_tracking,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_variant_without_inventory_tracking,
        address,
        address,
        checkout_delivery(
            checkout_with_variant_without_inventory_tracking, shipping_method
        ),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout,
        address,
        address,
        checkout_delivery(checkout, shipping_method),
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
    checkout_delivery,
    channel_USD,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item, shipping_method),
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
        undiscounted_unit_price_amount=checkout_line.variant.channel_listings.get(
            channel=channel_USD
        ).price_amount,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=stock,
        quantity_reserved=quantity_available,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
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
    checkout_delivery,
    channel_USD,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)

    checkout_line.quantity = quantity_available
    checkout_line.save()

    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )

    reservation = Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=quantity_available,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )

    # Reservation associated with checkout has been deleted
    with pytest.raises(Reservation.DoesNotExist):
        reservation.refresh_from_db()


def test_checkout_complete_without_redirect_url(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    shipping_method,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card, shipping_method),
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )


def test_checkout_complete_with_digital(
    api_client,
    checkout_with_digital_item,
    address,
    address_usa,
    transaction_events_generator,
    transaction_item_generator,
    customer_user,
):
    # given
    customer_user.addresses.clear()
    user_address_count = customer_user.addresses.count()

    checkout = prepare_checkout_for_test(
        checkout_with_digital_item,
        address,
        address_usa,
        None,
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
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

    order = Order.objects.first()
    # Ensure the order was actually created
    assert order, "The order should have been created"

    assert order.shipping_address
    assert order.billing_address
    assert order.draft_save_billing_address is None
    assert order.draft_save_shipping_address is None

    assert customer_user.addresses.count() == user_address_count + 2


def test_checkout_complete_with_digital_no_shipping_address_set(
    api_client,
    checkout_with_digital_item,
    address,
    transaction_events_generator,
    transaction_item_generator,
    customer_user,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_digital_item,
        None,
        address,
        None,
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
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

    order = Order.objects.first()
    # Ensure the order was actually created
    assert order, "The order should have been created"
    assert not order.shipping_address
    assert order.billing_address


def test_checkout_complete_with_digital_saving_addresses_off(
    api_client,
    checkout_with_digital_item,
    address,
    address_usa,
    transaction_events_generator,
    transaction_item_generator,
    customer_user,
):
    # given
    customer_user.addresses.clear()
    user_address_count = customer_user.addresses.count()

    checkout = prepare_checkout_for_test(
        checkout_with_digital_item,
        address,
        address_usa,
        None,
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
        save_billing_address=False,
        save_shipping_address=False,
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

    order = Order.objects.first()
    # Ensure the order was actually created
    assert order, "The order should have been created"

    assert order.shipping_address
    assert order.billing_address
    assert order.draft_save_billing_address is None
    assert order.draft_save_shipping_address is None

    assert customer_user.addresses.count() == user_address_count


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
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

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
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(
        product_variant=checkout_line.variant, warehouse=warehouse_for_cc
    )
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()
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
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    overall_stock_quantity = (
        Stock.objects.filter(product_variant=checkout_line.variant).aggregate(
            Sum("quantity")
        )
    ).pop("quantity__sum")
    checkout_line.quantity = overall_stock_quantity + 1
    checkout_line.save()
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
    assert not checkout_info.get_delivery_method_info().is_method_in_valid_methods(
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_preorder_item,
        address,
        address,
        checkout_delivery(checkout_with_item_and_preorder_item, shipping_method),
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

    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())


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
    assert not checkout_info.get_delivery_method_info().is_method_in_valid_methods(
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        checkout_delivery(checkout_with_items, shipping_method),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        checkout_delivery(checkout_with_items, shipping_method),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        checkout_delivery(checkout_with_items, shipping_method),
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
    "available_for_purchase",
    [None, datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=1)],
)
def test_checkout_complete_product_channel_listing_not_available_for_purchase(
    user_api_client,
    checkout_with_items,
    address,
    shipping_method,
    checkout_delivery,
    available_for_purchase,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_items,
        address,
        address,
        checkout_delivery(checkout_with_items, shipping_method),
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
    checkout_delivery,
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
        checkout_delivery(checkout_with_item, shipping_method),
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
    checkout_delivery,
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
        checkout_delivery(checkout_with_item),
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
    checkout_delivery,
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
        checkout_delivery(checkout_with_item),
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
    checkout_delivery,
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
        checkout_delivery(checkout_with_item),
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
    checkout_delivery,
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
        checkout_delivery(checkout_with_gift_card),
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
    checkout_delivery,
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
        checkout_delivery(checkout_with_gift_card),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
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
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
        transaction_item_generator,
        transaction_events_generator,
    )

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    def delete_order_line(*args, **kwargs):
        CheckoutLine.objects.get(id=checkout.lines.first().id).delete()

    # when
    with race_condition.RunBefore(
        "saleor.graphql.checkout.mutations.checkout_complete.complete_checkout",
        delete_order_line,
    ):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["order"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.NO_LINES.name
    assert data["errors"][0]["field"] == "lines"


def test_checkout_complete_with_invalid_address(
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    checkout_delivery,
    customer_user,
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
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.user = customer_user
    checkout.save()

    customer_user.addresses.clear()
    user_address_count = customer_user.addresses.count()

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
    assert customer_user.addresses.count() == user_address_count + 1
    assert order.draft_save_billing_address is None
    assert order.draft_save_shipping_address is None
    assert customer_user.addresses.first().id != order.shipping_address.id
    assert customer_user.addresses.first().id != order.billing_address.id


@patch("saleor.checkout.complete_checkout._get_unit_discount_reason")
def test_checkout_complete_log_unknown_discount_reason(
    mocked_discount_reason,
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    caplog,
):
    # given
    mocked_discount_reason.return_value = None

    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address,
        checkout_delivery(checkout_with_item_and_voucher_specific_products),
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
    assert not data["errors"]

    order = Order.objects.first()
    order_line = order.lines.first()
    assert not order_line.unit_discount_reason
    assert "Unknown discount reason" in caplog.text
    assert caplog.records[0].checkout_id == to_global_id_or_none(checkout)


@patch("saleor.order.calculations._recalculate_with_plugins")
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_empty_product_translation(
    order_confirmed_mock,
    recalculate_with_plugins_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    caplog,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
        transaction_item_generator,
        transaction_events_generator,
    )

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant
    checkout_line_product = checkout_line_variant.product

    checkout_line_product.translations.create(language_code="en")
    checkout_line_variant.translations.create(language_code="en")

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

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order_line.translated_product_name == ""
    assert order_line.translated_variant_name == ""

    assert order.shipping_address == address
    assert order.shipping_method.id == int(
        checkout.assigned_delivery.shipping_method_id
    )
    assert order.search_vector

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )
    assert not Checkout.objects.filter(pk=checkout.pk).exists(), (
        "Checkout should have been deleted"
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())
    recalculate_with_plugins_mock.assert_not_called()

    assert not len(Reservation.objects.all())


def test_complete_checkout_order_status_changed_after_creation(
    checkout_with_item_total_0,
    customer_user,
    user_api_client,
):
    """Ensure order status is valid in the mutation response.

    In case that order is created with `UNCONFIRMED` and then changed into `UNFULFILLED`
    in post commit action, the returned order status should be upt-to-date.
    """
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

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    def immediate_on_commit(func):
        func()

    # when
    with patch.object(transaction, "on_commit", side_effect=immediate_on_commit):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = data["order"]
    assert order
    assert order["status"] == OrderStatus.UNFULFILLED.upper()


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_complete_with_external_shipping_method(
    mocked_sync_webhook,
    user_api_client,
    checkout_with_item,
    transaction_item_generator,
    address,
    shipping_app,
):
    # given
    external_shipping_method_id = "ABC"
    external_shipping_name = "Provider - Economy"
    external_shipping_metadata_key = "external_metadata_key"
    external_shipping_metadata_value = "external_metadata_value"
    external_shipping_metadata = {
        external_shipping_metadata_key: external_shipping_metadata_value
    }
    graphql_external_method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{external_shipping_method_id}"
    )
    mock_json_response = [
        {
            "id": external_shipping_method_id,
            "name": external_shipping_name,
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
            "metadata": external_shipping_metadata,
        }
    ]
    mocked_sync_webhook.return_value = mock_json_response

    checkout = checkout_with_item
    checkout.assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        external_shipping_method_id=graphql_external_method_id,
        name=external_shipping_name,
        price_amount="10.00",
        currency="USD",
        maximum_delivery_days=7,
        is_external=True,
    )
    checkout.shipping_address = address
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction_item_generator(
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
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    order = Order.objects.get()
    assert (
        order.private_metadata[PRIVATE_META_APP_SHIPPING_ID]
        == graphql_external_method_id
    )
    assert order.shipping_method_metadata == external_shipping_metadata
    assert data["order"]["shippingMethod"]["name"] == external_shipping_name
    expected_metadata = [
        {
            "key": external_shipping_metadata_key,
            "value": external_shipping_metadata_value,
        }
    ]
    assert data["order"]["shippingMethod"]["metadata"] == expected_metadata
    assert data["order"]["deliveryMethod"]["metadata"] == expected_metadata


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_complete_with_external_shipping_method_private_metadata(
    mocked_sync_webhook,
    staff_api_client,
    checkout_with_item,
    transaction_item_generator,
    address,
    shipping_app,
    permission_manage_shipping,
):
    mutation_checkout_complete_with_private_metadata = """
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
                shippingMethod {
                    privateMetadata {
                        key
                        value
                    }
                }
                deliveryMethod {
                    ... on ShippingMethod {
                        privateMetadata {
                            key
                            value
                        }
                    }
                }
            }
            errors {
                field,
                message,
                variants,
                code
            }
        }
    }
    """

    # given
    external_shipping_method_id = "ABC"
    external_shipping_name = "External provider - Economy"
    external_shipping_private_metadata_key = "external_private_metadata_key"
    external_shipping_private_metadata_value = "external_private_metadata_value"
    external_shipping_private_metadata = {
        external_shipping_private_metadata_key: external_shipping_private_metadata_value
    }
    graphql_external_method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{external_shipping_method_id}"
    )
    mock_json_response = [
        {
            "id": external_shipping_method_id,
            "name": external_shipping_name,
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
            "private_metadata": external_shipping_private_metadata,
        }
    ]
    mocked_sync_webhook.return_value = mock_json_response

    checkout = checkout_with_item
    checkout.assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        external_shipping_method_id=graphql_external_method_id,
        name=external_shipping_name,
        price_amount="10.00",
        currency="USD",
        maximum_delivery_days=7,
        is_external=True,
    )
    checkout.shipping_address = address
    checkout.billing_address = address
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    transaction_item_generator(
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
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    response = staff_api_client.post_graphql(
        mutation_checkout_complete_with_private_metadata, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    order = Order.objects.get()
    expected_private_metadata = [
        {
            "key": external_shipping_private_metadata_key,
            "value": external_shipping_private_metadata_value,
        }
    ]
    assert order.shipping_method_private_metadata == external_shipping_private_metadata
    assert (
        data["order"]["shippingMethod"]["privateMetadata"] == expected_private_metadata
    )
    assert (
        data["order"]["deliveryMethod"]["privateMetadata"] == expected_private_metadata
    )


def test_checkout_complete_saving_addresses_off(
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    address,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    customer_user,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address,
        checkout_delivery(checkout_with_item_and_voucher_specific_products),
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
        save_billing_address=False,
        save_shipping_address=False,
    )

    customer_user.addresses.clear()
    user_address_count = customer_user.addresses.count()

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

    order = Order.objects.first()
    assert order.billing_address
    assert order.shipping_address
    assert customer_user.addresses.count() == user_address_count


def test_checkout_complete_saving_addresses_on(
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    address,
    address_usa,
    checkout_delivery,
    transaction_events_generator,
    transaction_item_generator,
    customer_user,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item_and_voucher_specific_products,
        address,
        address_usa,
        checkout_delivery(checkout_with_item_and_voucher_specific_products),
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
        save_billing_address=True,
        save_shipping_address=True,
    )

    customer_user.addresses.clear()
    user_address_count = customer_user.addresses.count()

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

    order = Order.objects.first()
    assert order.billing_address
    assert order.shipping_address
    assert customer_user.addresses.count() == user_address_count + 2
    # ensure the the customer addresses are not the same instances as the order addresses
    customer_address_ids = list(customer_user.addresses.values_list("pk", flat=True))
    assert not (
        set(customer_address_ids)
        & {order.billing_address.pk, order.shipping_address.pk}
    )

    assert order.draft_save_billing_address is None
    assert order.draft_save_shipping_address is None


def test_checkout_complete_with_different_email_than_user_email(
    user_api_client,
    checkout_ready_to_complete,
    address,
    address_usa,
    transaction_events_generator,
    transaction_item_generator,
    customer_user,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_ready_to_complete,
        address,
        address_usa,
        checkout_ready_to_complete.assigned_delivery,
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
        save_billing_address=True,
        save_shipping_address=True,
    )

    checkout.email = "different_email@example.com"
    checkout.user = customer_user
    checkout.save(update_fields=["email", "user"])
    assert checkout.user is not None
    assert checkout.user.email != checkout.email

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

    order = Order.objects.first()
    assert order.user_email == checkout.email
    assert order.user.email == checkout.user.email


def test_checkout_complete_sets_product_type_id_for_all_order_lines(
    user_api_client,
    checkout_ready_to_complete,
    address,
    address_usa,
    transaction_events_generator,
    transaction_item_generator,
    customer_user,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_ready_to_complete,
        address,
        address_usa,
        checkout_ready_to_complete.assigned_delivery,
        transaction_item_generator,
        transaction_events_generator,
        user=customer_user,
        save_billing_address=True,
        save_shipping_address=True,
    )

    lines, _ = fetch_checkout_lines(checkout)

    variant_id_to_product_type_id_map = {
        line.variant.id: line.product_type.id for line in lines
    }

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

    order = Order.objects.first()
    for line in order.lines.all():
        assert (
            line.product_type_id == variant_id_to_product_type_id_map[line.variant_id]
        )


@patch(
    "saleor.graphql.checkout.mutations.checkout_complete."
    "get_or_fetch_checkout_deliveries",
    wraps=get_or_fetch_checkout_deliveries,
)
def test_complete_refreshes_shipping_methods_when_stale(
    mocked_get_or_fetch_checkout_deliveries,
    user_api_client,
    checkout_ready_to_complete,
    transaction_item_generator,
    checkout_delivery,
):
    # given
    checkout = checkout_ready_to_complete
    checkout.delivery_methods_stale_at = timezone.now()
    checkout.save(update_fields=["delivery_methods_stale_at"])
    checkout.gift_cards.all().delete()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, None
    )

    transaction_item_generator(
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
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]
    assert mocked_get_or_fetch_checkout_deliveries.called


def test_checkout_complete_race_condition_on_preparing_checkout(
    user_api_client,
    checkout_with_item,
    address,
    shipping_method,
    transaction_events_generator,
    transaction_item_generator,
    order,
    checkout_delivery,
):
    # given
    checkout = prepare_checkout_for_test(
        checkout_with_item,
        address,
        address,
        checkout_delivery(checkout_with_item, shipping_method),
        transaction_item_generator,
        transaction_events_generator,
    )
    order.checkout_token = checkout.token
    order.save(update_fields=["checkout_token"])

    redirect_url = "https://www.example.com/new"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    def delete_checkout(*args, **kwargs):
        checkout.delete()

    # when
    with race_condition.RunAfter(
        "saleor.checkout.complete_checkout.clean_checkout_shipping", delete_checkout
    ):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]
    assert data["order"]


@patch(
    "saleor.checkout.fetch.fetch_shipping_methods_for_checkout",
    wraps=fetch_shipping_methods_for_checkout,
)
def test_complete_do_not_refresh_shipping_methods_when_not_stale(
    mocked_fetch_checkout_deliveries,
    user_api_client,
    checkout_ready_to_complete,
    transaction_item_generator,
    checkout_delivery,
):
    # given
    checkout = checkout_ready_to_complete
    checkout.delivery_methods_stale_at = timezone.now() + datetime.timedelta(hours=1)
    checkout.save(update_fields=["delivery_methods_stale_at"])
    checkout.gift_cards.all().delete()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, None
    )

    transaction_item_generator(
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
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]
    assert not mocked_fetch_checkout_deliveries.called


@patch(
    "saleor.checkout.fetch.fetch_shipping_methods_for_checkout",
    wraps=fetch_shipping_methods_for_checkout,
)
def test_complete_do_not_refresh_shipping_methods_when_cc_is_used(
    mocked_fetch_checkout_deliveries,
    user_api_client,
    checkout_with_delivery_method_for_cc,
    transaction_item_generator,
    checkout_delivery,
    address,
):
    # given
    checkout = checkout_with_delivery_method_for_cc
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, None
    )

    transaction_item_generator(
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
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]
    assert not mocked_fetch_checkout_deliveries.called


@patch(
    "saleor.graphql.checkout.mutations.checkout_complete."
    "get_or_fetch_checkout_deliveries",
    wraps=get_or_fetch_checkout_deliveries,
)
def test_complete_refreshes_shipping_methods_when_stale_and_invalid(
    mocked_get_or_fetch_checkout_deliveries,
    user_api_client,
    checkout_ready_to_complete,
    transaction_item_generator,
    checkout_delivery,
):
    # given
    checkout = checkout_ready_to_complete
    checkout.delivery_methods_stale_at = timezone.now()
    checkout.save(update_fields=["delivery_methods_stale_at"])
    checkout.gift_cards.all().delete()

    # Shipping is not available anymore
    ShippingMethod.objects.all().delete()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, None
    )

    transaction_item_generator(
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
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID_SHIPPING_METHOD.name

    assert Order.objects.count() == 0
    assert mocked_get_or_fetch_checkout_deliveries.called
