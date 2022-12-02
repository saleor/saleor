from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import reduce
from operator import getitem
from unittest.mock import ANY, MagicMock, Mock, call, patch

import graphene
import pytest
import pytz
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db.models import Sum
from django.utils import timezone
from freezegun import freeze_time
from measurement.measures import Weight
from prices import Money, TaxedMoney

from ....account.models import CustomerEvent
from ....checkout import AddressType
from ....checkout.utils import PRIVATE_META_APP_SHIPPING_ID
from ....core.anonymize import obfuscate_email
from ....core.notify_events import NotifyEventType
from ....core.postgres import FlatConcatSearchVector
from ....core.prices import quantize_price
from ....core.taxes import TaxError, zero_taxed_money
from ....discount.models import OrderDiscount, VoucherChannelListing
from ....giftcard import GiftCardEvents
from ....giftcard.events import gift_cards_bought_event, gift_cards_used_in_order_event
from ....order import FulfillmentStatus, OrderEvents, OrderOrigin, OrderStatus
from ....order import events as order_events
from ....order.error_codes import OrderErrorCode
from ....order.events import order_replacement_created
from ....order.fetch import fetch_order_info
from ....order.interface import OrderTaxedPricesData
from ....order.models import Order, OrderEvent, OrderLine, get_order_number
from ....order.notifications import get_default_order_payload
from ....order.search import (
    prepare_order_search_vector_value,
    update_order_search_vector,
)
from ....order.utils import update_order_authorize_data, update_order_charge_data
from ....payment import ChargeStatus, PaymentError, TransactionAction, TransactionStatus
from ....payment.interface import TransactionActionData
from ....payment.models import Payment, TransactionEvent, TransactionItem
from ....plugins.base_plugin import ExcludedShippingMethod
from ....plugins.manager import PluginsManager, get_plugins_manager
from ....product.models import ProductVariant, ProductVariantChannelListing
from ....shipping.models import ShippingMethod, ShippingMethodChannelListing
from ....tests.consts import TEST_SERVER_DOMAIN
from ....thumbnail.models import Thumbnail
from ....warehouse.models import Allocation, PreorderAllocation, Stock, Warehouse
from ....warehouse.tests.utils import get_available_quantity_for_stock
from ...core.enums import ThumbnailFormatEnum
from ...core.utils import to_global_id_or_none
from ...payment.enums import TransactionStatusEnum
from ...payment.types import PaymentChargeStatusEnum
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ..enums import OrderAuthorizeStatusEnum, OrderChargeStatusEnum
from ..mutations.order_cancel import clean_order_cancel
from ..mutations.order_capture import clean_order_capture
from ..mutations.order_refund import clean_refund_payment
from ..mutations.utils import try_payment_action
from ..utils import validate_draft_order
from .utils import assert_order_and_payment_ids


@pytest.fixture
def orders_query_with_filter():
    query = """
      query ($filter: OrderFilterInput!, ) {
        orders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """
    return query


@pytest.fixture
def draft_orders_query_with_filter():
    query = """
      query ($filter: OrderDraftFilterInput!, ) {
        draftOrders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """
    return query


@pytest.fixture
def orders(customer_user, channel_USD, channel_PLN):
    return Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                status=OrderStatus.CANCELED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNFULFILLED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.PARTIALLY_FULFILLED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                channel=channel_PLN,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.DRAFT,
                channel=channel_PLN,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNCONFIRMED,
                channel=channel_PLN,
            ),
        ]
    )


def assert_proper_webhook_called_once(order, status, draft_mock, order_mock):
    if status == OrderStatus.DRAFT:
        draft_mock.assert_called_once_with(order)
        order_mock.assert_not_called()
    else:
        draft_mock.assert_not_called()
        order_mock.assert_called_once_with(order)


def test_orderline_query(staff_api_client, permission_manage_orders, fulfilled_order):
    order = fulfilled_order
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        lines {
                            thumbnail(size: 540) {
                                url
                            }
                            variant {
                                id
                            }
                            quantity
                            allocations {
                                id
                                quantity
                                warehouse {
                                    id
                                }
                            }
                            unitPrice {
                                currency
                                gross {
                                    amount
                                }
                            }
                            totalPrice {
                                currency
                                gross {
                                    amount
                                }
                            }
                            metadata {
                                key
                                value
                            }
                            privateMetadata {
                                key
                                value
                            }
                        }
                    }
                }
            }
        }
    """
    line = order.lines.first()

    metadata_key = "md key"
    metadata_value = "md value"

    line.store_value_in_private_metadata({metadata_key: metadata_value})
    line.store_value_in_metadata({metadata_key: metadata_value})
    line.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    first_order_data_line = order_data["lines"][0]
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)

    assert first_order_data_line["thumbnail"] is None
    assert first_order_data_line["variant"]["id"] == variant_id
    assert first_order_data_line["quantity"] == line.quantity
    assert first_order_data_line["unitPrice"]["currency"] == line.unit_price.currency
    assert first_order_data_line["metadata"] == [
        {"key": metadata_key, "value": metadata_value}
    ]
    assert first_order_data_line["privateMetadata"] == [
        {"key": metadata_key, "value": metadata_value}
    ]
    expected_unit_price = Money(
        amount=str(first_order_data_line["unitPrice"]["gross"]["amount"]),
        currency="USD",
    )
    assert first_order_data_line["totalPrice"]["currency"] == line.unit_price.currency
    assert expected_unit_price == line.unit_price.gross

    expected_total_price = Money(
        amount=str(first_order_data_line["totalPrice"]["gross"]["amount"]),
        currency="USD",
    )
    assert expected_total_price == line.unit_price.gross * line.quantity

    allocation = line.allocations.first()
    allocation_id = graphene.Node.to_global_id("Allocation", allocation.pk)
    warehouse_id = graphene.Node.to_global_id(
        "Warehouse", allocation.stock.warehouse.pk
    )
    assert first_order_data_line["allocations"] == [
        {
            "id": allocation_id,
            "quantity": allocation.quantity_allocated,
            "warehouse": {"id": warehouse_id},
        }
    ]


def test_order_line_with_allocations(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    # given
    order = order_with_lines
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        lines {
                            id
                            allocations {
                                id
                                quantity
                                warehouse {
                                    id
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    lines = content["data"]["orders"]["edges"][0]["node"]["lines"]

    for line in lines:
        _, _id = graphene.Node.from_global_id(line["id"])
        order_line = order.lines.get(pk=_id)
        allocations_from_query = {
            allocation["quantity"] for allocation in line["allocations"]
        }
        allocations_from_db = set(
            order_line.allocations.values_list("quantity_allocated", flat=True)
        )
        assert allocations_from_query == allocations_from_db


ORDERS_QUERY = """
query OrdersQuery {
    orders(first: 1) {
        edges {
            node {
                number
                canFinalize
                status
                channel {
                    slug
                }
                languageCodeEnum
                statusDisplay
                paymentStatus
                paymentStatusDisplay
                userEmail
                isPaid
                actions
                totalAuthorized{
                    amount
                    currency
                }
                totalCaptured{
                    amount
                    currency
                }
                totalBalance{
                    amount
                    currency
                }
                shippingPrice {
                    gross {
                        amount
                    }
                }
                shippingTaxRate
                lines {
                    id
                    unitPrice{
                        gross{
                            amount
                        }
                    }
                    unitDiscount{
                        amount
                    }
                    undiscountedUnitPrice{
                        gross{
                            amount
                        }
                    }
                }
                discounts{
                    id
                    valueType
                    value
                    reason
                    amount{
                        amount
                    }
                }
                fulfillments {
                    fulfillmentOrder
                }
                payments{
                    id
                    actions
                    total{
                        currency
                        amount
                    }
                }
                transactions{
                    reference
                    type
                    status
                    modifiedAt
                    createdAt
                    authorizedAmount{
                        amount
                        currency
                    }
                    voidedAmount{
                        currency
                        amount
                    }
                    chargedAmount{
                        currency
                        amount
                    }
                    refundedAmount{
                        currency
                        amount
                    }
                    events{
                       status
                       reference
                       name
                       createdAt
                    }
                }
                authorizeStatus
                chargeStatus
                subtotal {
                    net {
                        amount
                    }
                }
                total {
                    net {
                        amount
                    }
                }
                availableShippingMethods {
                    id
                    name
                    description
                    price{
                      amount
                    }
                    minimumOrderPrice {
                      amount
                    }
                    maximumOrderPrice{
                      amount
                    }
                    maximumDeliveryDays
                    minimumDeliveryDays
                    metadata{
                      key
                      value
                    }
                    privateMetadata{
                      key
                      value
                    }
                }
                shippingMethods{
                  id
                  name
                  description
                  price{
                    amount
                  }
                  maximumOrderPrice{
                    amount
                  }
                  minimumOrderPrice{
                    amount
                  }
                  maximumDeliveryDays
                  minimumDeliveryDays
                  metadata{
                    key
                    value
                  }
                  privateMetadata{
                    key
                    value
                  }
                }
                shippingMethod{
                    id
                    name
                    description
                    active
                    message
                    price{
                        amount
                    }
                    maximumOrderPrice{
                        amount
                    }
                    minimumOrderPrice{
                        amount
                    }
                    maximumDeliveryDays
                    minimumDeliveryDays
                    metadata{
                        key
                        value
                    }
                    privateMetadata{
                        key
                        value
                    }
                }
                availableCollectionPoints {
                    id
                    name
                }
                shippingMethod{
                    id
                    name
                    price {
                        amount
                        currency
                    }

                }
                deliveryMethod {
                    __typename
                    ... on ShippingMethod {
                        id
                    }
                    ... on Warehouse {
                        id
                    }
                }
            }
        }
    }
}
"""


def test_order_query(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("10"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    private_value = "abc123"
    public_value = "123abc"
    order.shipping_method.store_value_in_metadata({"test": public_value})
    order.shipping_method.store_value_in_private_metadata({"test": private_value})
    order.shipping_method.save()
    order.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["number"] == str(order.number)
    assert order_data["channel"]["slug"] == order.channel.slug
    assert order_data["canFinalize"] is True
    assert order_data["status"] == order.status.upper()
    assert order_data["statusDisplay"] == order.get_status_display()
    payment_charge_status = PaymentChargeStatusEnum.NOT_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )
    assert order_data["isPaid"] == order.is_fully_paid()
    assert order_data["userEmail"] == order.user_email
    assert order_data["languageCodeEnum"] == order.language_code.upper()
    expected_price = Money(
        amount=str(order_data["shippingPrice"]["gross"]["amount"]), currency="USD"
    )
    assert expected_price == shipping_price.gross
    assert order_data["shippingTaxRate"] == float(shipping_tax_rate)
    assert order_data["shippingMethod"]["active"] is True
    assert order_data["shippingMethod"]["message"] == ""
    assert public_value == order_data["shippingMethod"]["metadata"][0]["value"]
    assert private_value == order_data["shippingMethod"]["privateMetadata"][0]["value"]
    assert len(order_data["lines"]) == order.lines.count()
    fulfillment = order.fulfillments.first().fulfillment_order
    fulfillment_order = order_data["fulfillments"][0]["fulfillmentOrder"]

    assert fulfillment_order == fulfillment
    assert len(order_data["payments"]) == order.payments.count()

    expected_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=order.get_subtotal().gross,
        weight=order.get_total_weight(),
        country_code=order.shipping_address.country.code,
        channel_id=order.channel_id,
    )
    expected_collection_points = Warehouse.objects.applicable_for_click_and_collect(
        lines_qs=order.lines, channel_id=order.channel.id
    )

    assert len(order_data["availableShippingMethods"]) == (expected_methods.count())
    assert len(order_data["availableCollectionPoints"]) == (
        expected_collection_points.count()
    )

    method = order_data["availableShippingMethods"][0]
    expected_method = expected_methods.first()
    expected_shipping_price = expected_method.channel_listings.get(
        channel_id=order.channel_id
    )

    assert float(expected_shipping_price.price.amount) == method["price"]["amount"]
    assert float(expected_shipping_price.minimum_order_price.amount) == (
        method["minimumOrderPrice"]["amount"]
    )
    assert order_data["deliveryMethod"]["id"] == order_data["shippingMethod"]["id"]


def test_order_query_total_price_is_0(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
    shipping_zone,
):
    """Ensure the payment status is FULLY_CHARGED when the order total is 0
    and there is no payment."""
    # given
    order = fulfilled_order
    price = zero_taxed_money(order.currency)
    order.shipping_price = price
    order.total = price
    shipping_tax_rate = Decimal("0")
    order.shipping_tax_rate = shipping_tax_rate
    private_value = "abc123"
    public_value = "123abc"
    order.shipping_method.store_value_in_metadata({"test": public_value})
    order.shipping_method.store_value_in_private_metadata({"test": private_value})
    order.shipping_method.save()
    order.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["number"] == str(order.number)
    assert order_data["channel"]["slug"] == order.channel.slug
    assert order_data["canFinalize"] is True
    assert order_data["status"] == order.status.upper()
    assert order_data["statusDisplay"] == order.get_status_display()
    payment_charge_status = PaymentChargeStatusEnum.FULLY_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )


@pytest.mark.parametrize(
    "total_authorized, total_charged, expected_status",
    [
        (Decimal("98.40"), Decimal("0"), OrderAuthorizeStatusEnum.FULL.name),
        (Decimal("0"), Decimal("98.40"), OrderAuthorizeStatusEnum.FULL.name),
        (Decimal("10"), Decimal("88.40"), OrderAuthorizeStatusEnum.FULL.name),
        (Decimal("0"), Decimal("0"), OrderAuthorizeStatusEnum.NONE.name),
        (Decimal("11"), Decimal("0"), OrderAuthorizeStatusEnum.PARTIAL.name),
        (Decimal("0"), Decimal("50.00"), OrderAuthorizeStatusEnum.PARTIAL.name),
        (Decimal("10"), Decimal("40.40"), OrderAuthorizeStatusEnum.PARTIAL.name),
    ],
)
def test_order_query_authorize_status(
    total_authorized,
    total_charged,
    expected_status,
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    assert fulfilled_order.total.gross.amount == Decimal("98.40")
    fulfilled_order.total_authorized_amount = total_authorized
    fulfilled_order.total_charged_amount = total_charged
    fulfilled_order.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["authorizeStatus"] == expected_status


@pytest.mark.parametrize(
    "total_authorized, total_charged, expected_status",
    [
        (Decimal("10.40"), Decimal("0"), OrderChargeStatusEnum.NONE.name),
        (Decimal("98.40"), Decimal("0"), OrderChargeStatusEnum.NONE.name),
        (Decimal("0"), Decimal("0"), OrderChargeStatusEnum.NONE.name),
        (Decimal("0"), Decimal("11.00"), OrderChargeStatusEnum.PARTIAL.name),
        (Decimal("88.40"), Decimal("10.00"), OrderChargeStatusEnum.PARTIAL.name),
        (Decimal("0"), Decimal("98.40"), OrderChargeStatusEnum.FULL.name),
    ],
)
def test_order_query_charge_status(
    total_authorized,
    total_charged,
    expected_status,
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    assert fulfilled_order.total.gross.amount == Decimal("98.40")
    fulfilled_order.total_authorized_amount = total_authorized
    fulfilled_order.total_charged_amount = total_charged
    fulfilled_order.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["chargeStatus"] == expected_status


def test_order_query_payment_status_with_total_fulfillment_refund_equal_to_order_total(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    fulfilled_order.fulfillments.create(
        tracking_number="123", total_refund_amount=fulfilled_order.total.gross.amount
    )

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_REFUNDED.name


def test_order_query_with_transactions_details(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("100"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    private_value = "abc123"
    public_value = "123abc"
    order.shipping_method.store_value_in_metadata({"test": public_value})
    order.shipping_method.store_value_in_private_metadata({"test": private_value})
    order.shipping_method.save()
    order.save()
    transactions = TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                status="Authorized",
                type="Credit card",
                reference="123",
                currency="USD",
                authorized_value=Decimal("15"),
                available_actions=[TransactionAction.CHARGE, TransactionAction.VOID],
            ),
            TransactionItem(
                order_id=order.id,
                status="Authorized second credit card",
                type="Credit card",
                reference="321",
                currency="USD",
                authorized_value=Decimal("10"),
                available_actions=[TransactionAction.CHARGE, TransactionAction.VOID],
            ),
            TransactionItem(
                order_id=order.id,
                status="Captured",
                type="Credit card",
                reference="321",
                currency="USD",
                charged_value=Decimal("15"),
                available_actions=[TransactionAction.REFUND],
            ),
        ]
    )
    update_order_authorize_data(order)
    update_order_charge_data(order)
    event_status = TransactionStatus.FAILURE
    event_reference = "PSP-ref"
    event_name = "Failed authorization"
    TransactionEvent.objects.bulk_create(
        [
            TransactionEvent(
                name=event_name,
                status=event_status,
                reference=event_reference,
                transaction=transaction,
            )
            for transaction in transactions
        ]
    )

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]

    payment_charge_status = PaymentChargeStatusEnum.PARTIALLY_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )
    assert order_data["isPaid"] == order.is_fully_paid()

    assert len(order_data["payments"]) == order.payments.count()
    assert Decimal(order_data["totalAuthorized"]["amount"]) == Decimal("25")
    assert Decimal(order_data["totalCaptured"]["amount"]) == Decimal("15")

    assert Decimal(str(order_data["totalBalance"]["amount"])) == Decimal("-83.4")

    for transaction in order_data["transactions"]:
        assert len(transaction["events"]) == 1
        event = transaction["events"][0]
        assert event["name"] == event_name
        assert event["status"] == TransactionStatusEnum.FAILURE.name
        assert event["reference"] == event_reference


def test_order_query_shipping_method_channel_listing_does_not_exist(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    order_with_lines,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save()

    shipping_method = order.shipping_method
    ShippingMethodChannelListing.objects.filter(
        shipping_method=shipping_method, channel=order.channel
    ).delete()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["shippingMethod"] is None


def test_order_query_external_shipping_method(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    order_with_lines,
):
    external_shipping_method_id = graphene.Node.to_global_id("app", "1:external123")

    # given
    order = order_with_lines
    order.shipping_method = None
    order.private_metadata = {PRIVATE_META_APP_SHIPPING_ID: external_shipping_method_id}
    order.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["shippingMethod"]["id"] == external_shipping_method_id
    assert order_data["shippingMethod"]["name"] == order.shipping_method_name
    assert order_data["shippingMethod"]["price"]["amount"] == float(
        order.shipping_price_gross.amount
    )


def test_order_discounts_query(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    draft_order_with_fixed_discount_order,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNFULFILLED
    order.save()

    discount = order.discounts.get()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    discounts_data = order_data.get("discounts")
    assert len(discounts_data) == 1
    discount_data = discounts_data[0]
    _, discount_id = graphene.Node.from_global_id(discount_data["id"])
    assert discount_id == str(discount.id)
    assert discount_data["valueType"] == discount.value_type.upper()
    assert discount_data["value"] == discount.value
    assert discount_data["amount"]["amount"] == discount.amount_value
    assert discount_data["reason"] == discount.reason


def test_order_line_discount_query(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    draft_order_with_fixed_discount_order,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNFULFILLED
    order.save()

    unit_discount_value = Decimal("5.0")
    line = order.lines.first()
    line.unit_discount = Money(unit_discount_value, currency=order.currency)
    line.unit_price -= line.unit_discount
    line.save()

    line_with_discount_id = graphene.Node.to_global_id("OrderLine", line.pk)

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    lines_data = order_data.get("lines")
    line_with_discount = [
        line for line in lines_data if line["id"] == line_with_discount_id
    ][0]

    unit_gross_amount = quantize_price(
        Decimal(line_with_discount["unitPrice"]["gross"]["amount"]),
        currency=order.currency,
    )
    unit_discount_amount = quantize_price(
        Decimal(line_with_discount["unitDiscount"]["amount"]), currency=order.currency
    )
    undiscounted_unit_price = quantize_price(
        Decimal(line_with_discount["undiscountedUnitPrice"]["gross"]["amount"]),
        currency=order.currency,
    )

    expected_unit_price_gross_amount = quantize_price(
        line.unit_price.gross.amount, currency=order.currency
    )
    expected_unit_discount_amount = quantize_price(
        line.unit_discount.amount, currency=order.currency
    )
    expected_undiscounted_unit_price = quantize_price(
        line.undiscounted_unit_price.gross.amount, currency=order.currency
    )

    assert unit_gross_amount == expected_unit_price_gross_amount
    assert unit_discount_amount == expected_unit_discount_amount
    assert undiscounted_unit_price == expected_undiscounted_unit_price


def test_order_query_in_pln_channel(
    staff_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    order_with_lines_channel_PLN,
    shipping_zone,
    channel_PLN,
):
    shipping_zone.channels.add(channel_PLN)
    order = order_with_lines_channel_PLN
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["number"] == str(order.number)
    assert order_data["channel"]["slug"] == order.channel.slug
    assert order_data["canFinalize"] is True
    assert order_data["status"] == order.status.upper()
    assert order_data["statusDisplay"] == order.get_status_display()
    payment_charge_status = PaymentChargeStatusEnum.NOT_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )
    assert order_data["isPaid"] == order.is_fully_paid()
    assert order_data["userEmail"] == order.user_email
    expected_price = Money(
        amount=str(order_data["shippingPrice"]["gross"]["amount"]),
        currency=channel_PLN.currency_code,
    )
    assert expected_price == order.shipping_price.gross
    assert len(order_data["lines"]) == order.lines.count()
    assert len(order_data["payments"]) == order.payments.count()

    expected_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=order.get_subtotal().gross,
        weight=order.get_total_weight(),
        country_code=order.shipping_address.country.code,
        channel_id=order.channel_id,
    )
    assert len(order_data["availableShippingMethods"]) == (expected_methods.count())

    method = order_data["availableShippingMethods"][0]
    expected_method = expected_methods.first()
    expected_shipping_price = expected_method.channel_listings.get(
        channel_id=order.channel_id
    )
    assert float(expected_shipping_price.price.amount) == method["price"]["amount"]
    assert float(expected_shipping_price.minimum_order_price.amount) == (
        method["minimumOrderPrice"]["amount"]
    )


ORDERS_QUERY_SHIPPING_METHODS = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    availableShippingMethods {
                        name
                        price {
                            amount
                        }
                    }
                }
            }
        }
    }
"""


def test_order_query_without_available_shipping_methods(
    staff_api_client,
    permission_manage_orders,
    order,
    shipping_method_channel_PLN,
    channel_USD,
):
    order.channel = channel_USD
    order.shipping_method = shipping_method_channel_PLN
    order.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["availableShippingMethods"]) == 0


@pytest.mark.parametrize("minimum_order_weight_value", [0, 2, None])
def test_order_available_shipping_methods_with_weight_based_shipping_method(
    staff_api_client,
    order_line,
    shipping_method_weight_based,
    permission_manage_orders,
    minimum_order_weight_value,
):

    shipping_method = shipping_method_weight_based
    order = order_line.order
    if minimum_order_weight_value is not None:
        weight = Weight(kg=minimum_order_weight_value)
        shipping_method.minimum_order_weight = weight
        order.weight = weight
        order.save(update_fields=["weight"])
    else:
        shipping_method.minimum_order_weight = minimum_order_weight_value

    shipping_method.save(update_fields=["minimum_order_weight"])

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    shipping_methods = [
        method["name"] for method in order_data["availableShippingMethods"]
    ]
    assert shipping_method.name in shipping_methods


def test_order_available_shipping_methods_weight_method_with_higher_minimal_weigh(
    staff_api_client, order_line, shipping_method_weight_based, permission_manage_orders
):
    order = order_line.order

    shipping_method = shipping_method_weight_based
    weight_value = 5
    shipping_method.minimum_order_weight = Weight(kg=weight_value)
    shipping_method.save(update_fields=["minimum_order_weight"])

    order.weight = Weight(kg=1)
    order.save(update_fields=["weight"])

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    shipping_methods = [
        method["name"] for method in order_data["availableShippingMethods"]
    ]
    assert shipping_method.name not in shipping_methods


def test_order_query_shipping_zones_with_available_shipping_methods(
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    shipping_zone,
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["availableShippingMethods"]) == 1


def test_order_query_shipping_zones_without_channel(
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    shipping_zone,
    channel_USD,
):
    channel_USD.shipping_zones.clear()
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    assert len(order_data["availableShippingMethods"]) == 0


def test_order_query_shipping_methods_excluded_postal_codes(
    staff_api_client,
    permission_manage_orders,
    order_with_lines_channel_PLN,
    channel_PLN,
):
    order = order_with_lines_channel_PLN
    order.shipping_method.postal_code_rules.create(start="HB3", end="HB6")
    order.shipping_address.postal_code = "HB5"
    order.shipping_address.save(update_fields=["postal_code"])

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["availableShippingMethods"] == []


def test_order_available_shipping_methods_query(
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    shipping_zone,
):
    query = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    availableShippingMethods {
                        id
                        price {
                            amount
                        }
                    }
                }
            }
        }
    }
    """
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_price = shipping_method.channel_listings.get(
        channel_id=fulfilled_order.channel_id
    ).price

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    method = order_data["availableShippingMethods"][0]

    assert shipping_price.amount == method["price"]["amount"]


def test_order_query_customer(api_client):
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    response = api_client.post_graphql(query)
    assert_no_permission(response)


def test_order_query_gift_cards(
    staff_api_client, permission_manage_orders, order_with_lines, gift_card
):
    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            giftCards {
                last4CodeChars
                currentBalance {
                    amount
                }
            }
        }
    }
    """

    order_with_lines.gift_cards.add(gift_card)

    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    gift_card_data = content["data"]["order"]["giftCards"][0]

    assert gift_card.display_code == gift_card_data["last4CodeChars"]
    assert (
        gift_card.current_balance.amount == gift_card_data["currentBalance"]["amount"]
    )


def test_order_query_shows_non_draft_orders(
    staff_api_client, permission_manage_orders, orders
):
    query = """
    query OrdersQuery {
        orders(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["orders"]["edges"]

    assert len(edges) == Order.objects.non_draft().count()


ORDERS_QUERY_LINE_THUMBNAIL = """
    query OrdersQuery($size: Int, $format: ThumbnailFormatEnum) {
        orders(first: 1) {
            edges {
                node {
                    lines {
                        id
                        thumbnail(size: $size, format: $format) {
                            url
                        }
                    }
                }
            }
        }
    }
"""


def test_order_query_no_thumbnail(
    staff_api_client,
    permission_manage_orders,
    order_line,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["lines"]) == 1
    assert not order_data["lines"][0]["thumbnail"]


def test_order_query_product_image_size_and_format_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    product_with_image,
):
    # given
    order_line.variant.product = product_with_image
    media = product_with_image.media.first()
    format = ThumbnailFormatEnum.WEBP.name
    variables = {
        "size": 120,
        "format": format,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/thumbnail/{media_id}/128/{format.lower()}/"
    )


def test_order_query_product_image_size_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    product_with_image,
):
    # given
    order_line.variant.product = product_with_image
    media = product_with_image.media.first()
    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/thumbnail/{media_id}/128/"
    )


def test_order_query_product_image_size_given_thumbnail_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    product_with_image,
):
    # given
    order_line.variant.product = product_with_image
    media = product_with_image.media.first()

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(product_media=media, size=128, image=thumbnail_mock)

    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_order_query_variant_image_size_and_format_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    variant_with_image,
):
    # given
    order_line.variant = variant_with_image
    media = variant_with_image.media.first()
    format = ThumbnailFormatEnum.WEBP.name
    variables = {
        "size": 120,
        "format": format,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/thumbnail/{media_id}/128/{format.lower()}/"
    )


def test_order_query_variant_image_size_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    variant_with_image,
):
    # given
    order_line.variant = variant_with_image
    media = variant_with_image.media.first()
    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/thumbnail/{media_id}/128/"
    )


def test_order_query_variant_image_size_given_thumbnail_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    variant_with_image,
):
    # given
    order_line.variant = variant_with_image
    media = variant_with_image.media.first()

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(product_media=media, size=128, image=thumbnail_mock)

    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/media/thumbnails/{thumbnail_mock.name}"
    )


ORDER_CONFIRM_MUTATION = """
    mutation orderConfirm($id: ID!) {
        orderConfirm(id: $id) {
            errors {
                field
                code
            }
            order {
                status
            }
        }
    }
"""


@patch("saleor.order.actions.handle_fully_paid_order")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.payment.gateway.capture")
def test_order_confirm(
    capture_mock,
    mocked_notify,
    handle_fully_paid_order_mock,
    staff_api_client,
    order_unconfirmed,
    permission_manage_orders,
    payment_txn_preauth,
    site_settings,
):
    # given
    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.captured_amount = order_unconfirmed.total.gross.amount
    payment_txn_preauth.total = order_unconfirmed.total.gross.amount
    payment_txn_preauth.save(update_fields=["order", "captured_amount", "total"])

    order_unconfirmed.total_charged = order_unconfirmed.total.gross
    order_unconfirmed.save(update_fields=["total_charged_amount"])

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    assert not OrderEvent.objects.exists()

    # when
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )

    # then
    order_data = get_graphql_content(response)["data"]["orderConfirm"]["order"]

    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()
    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.status == OrderStatus.UNFULFILLED
    assert OrderEvent.objects.count() == 2
    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.CONFIRMED,
    ).exists()

    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.PAYMENT_CAPTURED,
        parameters__amount=payment_txn_preauth.get_total().amount,
    ).exists()

    capture_mock.assert_called_once_with(
        payment_txn_preauth, ANY, channel_slug=order_unconfirmed.channel.slug
    )
    expected_payload = {
        "order": get_default_order_payload(order_unconfirmed, ""),
        "recipient_email": order_unconfirmed.user.email,
        "requester_user_id": to_global_id_or_none(staff_api_client.user),
        "requester_app_id": None,
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMED,
        expected_payload,
        channel_slug=order_unconfirmed.channel.slug,
    )
    order_info = fetch_order_info(order_unconfirmed)
    handle_fully_paid_order_mock.assert_called_once_with(
        ANY, order_info, staff_api_client.user, None, site_settings
    )


@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.payment.gateway.capture")
def test_order_confirm_without_sku(
    capture_mock,
    mocked_notify,
    staff_api_client,
    order_unconfirmed,
    permission_manage_orders,
    payment_txn_preauth,
):
    order_unconfirmed.lines.update(product_sku=None)
    ProductVariant.objects.update(sku=None)

    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.save()
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    assert not OrderEvent.objects.exists()
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )
    order_data = get_graphql_content(response)["data"]["orderConfirm"]["order"]

    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()
    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.status == OrderStatus.UNFULFILLED
    assert OrderEvent.objects.count() == 2
    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.CONFIRMED,
    ).exists()

    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.PAYMENT_CAPTURED,
        parameters__amount=payment_txn_preauth.get_total().amount,
    ).exists()

    capture_mock.assert_called_once_with(
        payment_txn_preauth, ANY, channel_slug=order_unconfirmed.channel.slug
    )
    expected_payload = {
        "order": get_default_order_payload(order_unconfirmed, ""),
        "recipient_email": order_unconfirmed.user.email,
        "requester_user_id": to_global_id_or_none(staff_api_client.user),
        "requester_app_id": None,
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMED,
        expected_payload,
        channel_slug=order_unconfirmed.channel.slug,
    )


def test_order_confirm_unfulfilled(staff_api_client, order, permission_manage_orders):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION, {"id": graphene.Node.to_global_id("Order", order.id)}
    )
    content = get_graphql_content(response)["data"]["orderConfirm"]
    errors = content["errors"]

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED
    assert content["order"] is None
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


def test_order_confirm_no_products_in_order(
    staff_api_client, order_unconfirmed, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_unconfirmed.lines.set([])
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )
    content = get_graphql_content(response)["data"]["orderConfirm"]
    errors = content["errors"]

    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.is_unconfirmed()
    assert content["order"] is None
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


@patch("saleor.payment.gateway.capture")
def test_order_confirm_wont_call_capture_for_non_active_payment(
    capture_mock,
    staff_api_client,
    order_unconfirmed,
    permission_manage_orders,
    payment_txn_preauth,
):
    payment_txn_preauth.order = order_unconfirmed
    payment_txn_preauth.is_active = False
    payment_txn_preauth.save()
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    assert not OrderEvent.objects.exists()
    response = staff_api_client.post_graphql(
        ORDER_CONFIRM_MUTATION,
        {"id": graphene.Node.to_global_id("Order", order_unconfirmed.id)},
    )
    order_data = get_graphql_content(response)["data"]["orderConfirm"]["order"]

    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()
    order_unconfirmed.refresh_from_db()
    assert order_unconfirmed.status == OrderStatus.UNFULFILLED
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.filter(
        order=order_unconfirmed,
        user=staff_api_client.user,
        type=order_events.OrderEvents.CONFIRMED,
    ).exists()
    assert not capture_mock.called


def test_orders_with_channel(
    staff_api_client, permission_manage_orders, orders, channel_USD
):
    query = """
    query OrdersQuery($channel: String) {
        orders(first: 10, channel: $channel) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    edges = get_graphql_content(response)["data"]["orders"]["edges"]

    assert len(edges) == 3


def test_orders_without_channel(staff_api_client, permission_manage_orders, orders):
    query = """
    query OrdersQuery {
        orders(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["orders"]["edges"]

    assert len(edges) == Order.objects.non_draft().count()


def test_draft_order_query(staff_api_client, permission_manage_orders, orders):
    query = """
    query DraftOrdersQuery {
        draftOrders(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == Order.objects.drafts().count()


ORDERS_FULFILLED_EVENTS = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    events {
                        date
                        type
                        user {
                            email
                        }
                        app {
                            name
                        }
                        message
                        email
                        emailType
                        amount
                        quantity
                        composedId
                        orderNumber
                        fulfilledItems {
                            quantity
                            orderLine {
                                productName
                                variantName
                            }
                        }
                        paymentId
                        paymentGateway
                        warehouse {
                            name
                        }
                    }
                }
            }
        }
    }
"""


def test_nested_order_events_query(
    staff_api_client,
    permission_manage_orders,
    permission_manage_apps,
    fulfilled_order,
    fulfillment,
    staff_user,
    warehouse,
):
    query = ORDERS_FULFILLED_EVENTS

    event = order_events.fulfillment_fulfilled_items_event(
        order=fulfilled_order,
        user=staff_user,
        app=None,
        fulfillment_lines=fulfillment.lines.all(),
    )
    event.parameters.update(
        {
            "message": "Example note",
            "email_type": order_events.OrderEventsEmails.PAYMENT,
            "amount": "80.00",
            "quantity": "10",
            "composed_id": "10-10",
            "warehouse": warehouse.pk,
        }
    )
    event.save()

    staff_api_client.user.user_permissions.add(
        permission_manage_orders, permission_manage_apps
    )
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]
    assert data["message"] == event.parameters["message"]
    assert data["amount"] == float(event.parameters["amount"])
    assert data["emailType"] == "PAYMENT_CONFIRMATION"
    assert data["quantity"] == int(event.parameters["quantity"])
    assert data["composedId"] == event.parameters["composed_id"]
    assert data["user"]["email"] == staff_user.email
    assert data["type"] == "FULFILLMENT_FULFILLED_ITEMS"
    assert data["date"] == event.date.isoformat()
    assert data["orderNumber"] == str(fulfilled_order.number)
    assert data["fulfilledItems"] == [
        {
            "quantity": line.quantity,
            "orderLine": {
                "productName": line.order_line.product_name,
                "variantName": line.order_line.variant_name,
            },
        }
        for line in fulfillment.lines.all()
    ]
    assert data["paymentId"] is None
    assert data["paymentGateway"] is None
    assert data["warehouse"]["name"] == warehouse.name


def test_nested_order_events_query_for_app(
    staff_api_client,
    permission_manage_orders,
    permission_manage_apps,
    fulfilled_order,
    fulfillment,
    app,
    warehouse,
):
    query = ORDERS_FULFILLED_EVENTS

    event = order_events.fulfillment_fulfilled_items_event(
        order=fulfilled_order,
        user=None,
        app=app,
        fulfillment_lines=fulfillment.lines.all(),
    )
    event.parameters.update(
        {
            "message": "Example note",
            "email_type": order_events.OrderEventsEmails.PAYMENT,
            "amount": "80.00",
            "quantity": "10",
            "composed_id": "10-10",
            "warehouse": warehouse.pk,
        }
    )
    event.save()

    staff_api_client.user.user_permissions.add(
        permission_manage_orders, permission_manage_apps
    )
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]
    assert data["message"] == event.parameters["message"]
    assert data["amount"] == float(event.parameters["amount"])
    assert data["emailType"] == "PAYMENT_CONFIRMATION"
    assert data["quantity"] == int(event.parameters["quantity"])
    assert data["composedId"] == event.parameters["composed_id"]
    assert data["user"] is None
    assert data["app"]["name"] == app.name
    assert data["type"] == "FULFILLMENT_FULFILLED_ITEMS"
    assert data["date"] == event.date.isoformat()
    assert data["orderNumber"] == str(fulfilled_order.number)
    assert data["fulfilledItems"] == [
        {
            "quantity": line.quantity,
            "orderLine": {
                "productName": line.order_line.product_name,
                "variantName": line.order_line.variant_name,
            },
        }
        for line in fulfillment.lines.all()
    ]
    assert data["paymentId"] is None
    assert data["paymentGateway"] is None
    assert data["warehouse"]["name"] == warehouse.name


def test_related_order_events_query(
    staff_api_client, permission_manage_orders, order, payment_dummy, staff_user
):
    query = """
        query OrdersQuery {
            orders(first: 2) {
                edges {
                    node {
                        id
                        events {
                            relatedOrder{
                                id
                            }
                        }
                    }
                }
            }
        }
    """

    new_order = deepcopy(order)
    new_order.id = None
    new_order.number = get_order_number()
    new_order.save()

    related_order_id = graphene.Node.to_global_id("Order", new_order.id)

    order_replacement_created(
        original_order=order, replace_order=new_order, user=staff_user, app=None
    )

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)

    data = content["data"]["orders"]["edges"]
    for order_data in data:
        events_data = order_data["node"]["events"]
        if order_data["node"]["id"] != related_order_id:
            assert events_data[0]["relatedOrder"]["id"] == related_order_id


def test_related_order_events_query_for_app(
    staff_api_client, permission_manage_orders, order, payment_dummy, app
):
    query = """
        query OrdersQuery {
            orders(first: 2) {
                edges {
                    node {
                        id
                        events {
                            relatedOrder{
                                id
                            }
                        }
                    }
                }
            }
        }
    """

    new_order = deepcopy(order)
    new_order.id = None
    new_order.number = get_order_number()
    new_order.save()

    related_order_id = graphene.Node.to_global_id("Order", new_order.id)

    order_replacement_created(
        original_order=order, replace_order=new_order, user=None, app=app
    )

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)

    data = content["data"]["orders"]["edges"]
    for order_data in data:
        events_data = order_data["node"]["events"]
        if order_data["node"]["id"] != related_order_id:
            assert events_data[0]["relatedOrder"]["id"] == related_order_id


def test_order_events_without_permission(
    staff_api_client,
    permission_manage_orders,
    order_with_lines_and_events,
    customer_user,
):
    query = """
        query OrdersQuery {
            orders(first: 2) {
                edges {
                    node {
                        id
                        events {
                            user {
                                id
                            }
                        }
                    }
                }
            }
        }
    """
    last_event = order_with_lines_and_events.events.last()
    last_event.user = customer_user
    last_event.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)

    response_events = content["data"]["orders"]["edges"][0]["node"]["events"]
    assert response_events[-1]["user"] is None


ORDERS_PAYMENTS_EVENTS_QUERY = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    events {
                        type
                        user {
                            email
                        }
                        app {
                            name
                        }
                        message
                        email
                        emailType
                        amount
                        quantity
                        composedId
                        orderNumber
                        lines {
                            quantity
                        }
                        paymentId
                        paymentGateway
                    }
                }
            }
        }
    }
"""


def test_payment_information_order_events_query(
    staff_api_client,
    permission_manage_orders,
    permission_manage_apps,
    order,
    payment_dummy,
    staff_user,
):
    query = ORDERS_PAYMENTS_EVENTS_QUERY

    amount = order.total.gross.amount

    order_events.payment_captured_event(
        order=order, user=staff_user, app=None, amount=amount, payment=payment_dummy
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders, permission_manage_apps
    )
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    assert data["message"] is None
    assert Money(str(data["amount"]), "USD") == order.total.gross
    assert data["emailType"] is None
    assert data["quantity"] is None
    assert data["composedId"] is None
    assert data["lines"] is None
    assert data["user"]["email"] == staff_user.email
    assert data["app"] is None
    assert data["type"] == "PAYMENT_CAPTURED"
    assert data["orderNumber"] == str(order.number)
    assert data["paymentId"] == payment_dummy.token
    assert data["paymentGateway"] == payment_dummy.gateway


def test_payment_information_order_events_query_for_app(
    staff_api_client,
    permission_manage_orders,
    permission_manage_apps,
    order,
    payment_dummy,
    app,
):
    query = ORDERS_PAYMENTS_EVENTS_QUERY

    amount = order.total.gross.amount

    order_events.payment_captured_event(
        order=order, user=None, app=app, amount=amount, payment=payment_dummy
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders, permission_manage_apps
    )
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    assert data["message"] is None
    assert Money(str(data["amount"]), "USD") == order.total.gross
    assert data["emailType"] is None
    assert data["quantity"] is None
    assert data["composedId"] is None
    assert data["lines"] is None
    assert data["app"]["name"] == app.name
    assert data["type"] == "PAYMENT_CAPTURED"
    assert data["orderNumber"] == str(order.number)
    assert data["paymentId"] == payment_dummy.token
    assert data["paymentGateway"] == payment_dummy.gateway


QUERY_ORDER_BY_ID = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            number
        }
    }
"""


def test_non_staff_user_can_see_his_order(user_api_client, order):
    # given
    query = QUERY_ORDER_BY_ID
    ID = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": ID}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data["number"] == str(order.number)


def test_query_order_as_app(app_api_client, order):
    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            id
        }
    }
    """
    ID = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": ID}
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data["id"] == graphene.Node.to_global_id("Order", order.id)


def test_staff_query_order_by_old_id(staff_api_client, order, permission_manage_orders):
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])
    variables = {"id": graphene.Node.to_global_id("Order", order.number)}
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content_from_response(response)
    assert content["data"]["order"]["number"] == str(order.number)


def test_staff_query_order_by_old_id_for_order_with_use_old_id_set_to_false(
    staff_api_client, order
):
    assert not order.use_old_id
    variables = {"id": graphene.Node.to_global_id("Order", order.number)}
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content_from_response(response)
    assert content["data"]["order"] is None


def test_staff_query_order_by_invalid_id(staff_api_client, order):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["order"] is None


def test_staff_query_order_with_invalid_object_type(staff_api_client, order):
    variables = {"id": graphene.Node.to_global_id("Checkout", order.pk)}
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["order"] is None


QUERY_ORDER_FIELDS_BY_ID = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            number
            billingAddress{
                city
                streetAddress1
                postalCode
            }
            shippingAddress{
                city
                streetAddress1
                postalCode
            }
            userEmail
            invoices {
                number
            }
        }
    }
"""


def test_query_order_fields_order_with_new_id_by_staff_no_perm(order, staff_api_client):
    """Ensure that all fields that are available for order owner can be fetched with
    use of new id by staff user without permissions."""
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_order_with_new_id_by_anonymous_user(order, api_client):
    """Ensure that all fields that are available for order owner can be fetched with
    use of new id by the customer user."""
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_staff_no_perms(order, staff_api_client):
    """Ensure that all fields that are available for order owner cannot be fetched with
    use of old id by staff user without permissions."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    assert_no_permission(response)


def test_query_order_fields_by_old_id_by_order_owner(order, user_api_client):
    """Ensure that all fields that are available for order owner can be fetched with
    use of old id by order owner."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_staff_with_perm(
    order, staff_api_client, permission_manage_orders
):
    """Ensure that all fields that are available for order owner can be fetched with
    use of old id by staff user with manage orders permission."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_FIELDS_BY_ID, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_app_with_perm(
    order, app_api_client, permission_manage_orders
):
    """Ensure that all fields that are available for order owner can be fetched with
    use of old id by app with manage orders permission."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_FIELDS_BY_ID, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_order_with_old_id_staff_with_perm(
    order, app_api_client, permission_manage_orders
):
    """Ensure that all fields that are available for order owner can be fetched with
    use of old id by app with manage orders permission."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_FIELDS_BY_ID, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_app_no_perm(order, app_api_client):
    """Ensure that all fields that are available for order owner cannot be fetched with
    use of old id by app without permissions."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = app_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    assert_no_permission(response)


DRAFT_ORDER_CREATE_MUTATION = """
    mutation draftCreate(
        $user: ID, $discount: PositiveDecimal, $lines: [OrderLineCreateInput!],
        $shippingAddress: AddressInput, $billingAddress: AddressInput,
        $shippingMethod: ID, $voucher: ID, $customerNote: String, $channel: ID,
        $redirectUrl: String
        ) {
            draftOrderCreate(
                input: {user: $user, discount: $discount,
                lines: $lines, shippingAddress: $shippingAddress,
                billingAddress: $billingAddress,
                shippingMethod: $shippingMethod, voucher: $voucher,
                channelId: $channel,
                redirectUrl: $redirectUrl,
                customerNote: $customerNote}) {
                    errors {
                        field
                        code
                        variants
                        message
                        addressType
                    }
                    order {
                        discount {
                            amount
                        }
                        discountName
                        redirectUrl
                        lines {
                            productName
                            productSku
                            quantity
                        }
                        billingAddress{
                            city
                            streetAddress1
                            postalCode
                        }
                        shippingAddress{
                            city
                            streetAddress1
                            postalCode
                        }
                        status
                        voucher {
                            code
                        }
                        customerNote
                        total {
                            gross {
                                amount
                            }
                        }
                    }
                }
        }
    """


def test_draft_order_create(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "billingAddress": shipping_address,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
        "redirectUrl": redirect_url,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note
    assert data["redirectUrl"] == redirect_url
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.billing_address
    assert order.shipping_address
    assert order.search_vector

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 2

    order_lines = list(order.lines.all())
    assert event_parameters["lines"][0]["item"] == str(order_lines[0])
    assert event_parameters["lines"][0]["line_pk"] == str(order_lines[0].pk)
    assert event_parameters["lines"][0]["quantity"] == 2

    assert event_parameters["lines"][1]["item"] == str(order_lines[1])
    assert event_parameters["lines"][1]["line_pk"] == str(order_lines[1].pk)
    assert event_parameters["lines"][1]["quantity"] == 1


def test_draft_order_create_with_same_variant_and_force_new_line(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)

    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
        {"variantId": variant_id, "quantity": 1, "forceNewLine": True},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "billingAddress": shipping_address,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
        "redirectUrl": redirect_url,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note
    assert data["redirectUrl"] == redirect_url
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.billing_address
    assert order.shipping_address
    assert order.search_vector

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 2

    order_lines = list(order.lines.all())
    assert event_parameters["lines"][0]["item"] == str(order_lines[0])
    assert event_parameters["lines"][0]["line_pk"] == str(order_lines[0].pk)
    assert event_parameters["lines"][0]["quantity"] == 1

    assert event_parameters["lines"][1]["item"] == str(order_lines[1])
    assert event_parameters["lines"][1]["line_pk"] == str(order_lines[1].pk)
    assert event_parameters["lines"][1]["quantity"] == 2


def test_draft_order_create_with_inactive_channel(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    channel_USD.is_active = False
    channel_USD.save()
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note

    order = Order.objects.first()
    assert order.user == customer_user
    # billing address shouldn't be set
    assert not order.billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_create_without_sku(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    ProductVariant.objects.update(sku=None)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "billingAddress": shipping_address,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
        "redirectUrl": redirect_url,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note
    assert data["redirectUrl"] == redirect_url
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.billing_address
    assert order.shipping_address

    order_line = order.lines.get(variant=variant)
    assert order_line.product_sku is None
    assert order_line.product_variant_id == variant.get_global_id()

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_create_variant_with_0_price(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant.price = Money(0, "USD")
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {
        "user": user_id,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "channel": channel_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()

    order = Order.objects.first()
    assert order.user == customer_user
    # billing address shouldn't be copied from user
    assert not order.billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


@patch("saleor.graphql.order.mutations.draft_order_create.create_order_line")
def test_draft_order_create_tax_error(
    create_order_line_mock,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    err_msg = "Test error"
    create_order_line_mock.side_effect = TaxError(err_msg)
    query = DRAFT_ORDER_CREATE_MUTATION
    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderCreate"]
    errors = data["errors"]
    assert not data["order"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.TAX_ERROR.name
    assert errors[0]["message"] == f"Unable to calculate taxes - {err_msg}"

    order_count = Order.objects.all().count()
    assert order_count == 0


def test_draft_order_create_with_voucher_not_assigned_to_order_channel(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    query = DRAFT_ORDER_CREATE_MUTATION

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher.channel_listings.all().delete()
    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "voucher"


def test_draft_order_create_with_product_and_variant_not_assigned_to_order_channel(
    staff_api_client,
    permission_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data,
):
    query = DRAFT_ORDER_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variant.product.channel_listings.all().delete()
    variant.channel_listings.all().delete()
    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "customerNote": customer_note,
        "channel": channel_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.PRODUCT_NOT_PUBLISHED.name
    assert error["field"] == "lines"
    assert error["variants"] == [variant_id]


def test_draft_order_create_with_variant_not_assigned_to_order_channel(
    staff_api_client,
    permission_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data,
):
    query = DRAFT_ORDER_CREATE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variant.channel_listings.all().delete()
    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "customerNote": customer_note,
        "channel": channel_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "lines"
    assert error["variants"] == [variant_id]


def test_draft_order_create_without_channel(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    variables = {
        "user": user_id,
        "lines": variant_list,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.REQUIRED.name
    assert error["field"] == "channel"


def test_draft_order_create_with_negative_quantity_line(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    channel_USD,
    variant,
    voucher,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": -2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    variables = {
        "user": user_id,
        "lines": variant_list,
        "channel": channel_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.ZERO_QUANTITY.name
    assert error["field"] == "quantity"


def test_draft_order_create_with_channel_with_unpublished_product(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    channel_listing = variant_1.product.channel_listings.get()
    channel_listing.is_published = False
    channel_listing.save()

    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "user": user_id,
        "discount": discount,
        "channel": channel_id,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.PRODUCT_NOT_PUBLISHED.name
    assert error["variants"] == [variant_1_id]


def test_draft_order_create_with_channel_with_unpublished_product_by_date(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()
    next_day = datetime.now(pytz.UTC) + timedelta(days=1)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    channel_listing = variant_1.product.channel_listings.get()
    channel_listing.published_at = next_day
    channel_listing.save()

    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "user": user_id,
        "discount": discount,
        "channel": channel_id,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]

    assert error["field"] == "lines"
    assert error["code"] == "PRODUCT_NOT_PUBLISHED"
    assert error["variants"] == [variant_1_id]


def test_draft_order_create_with_channel(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()

    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "user": user_id,
        "discount": discount,
        "channel": channel_id,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.channel.id == channel_USD.id
    # billing address should be copied
    assert not order.billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_create_invalid_billing_address(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    billing_address = graphql_address_data.copy()
    del billing_address["country"]
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "billingAddress": billing_address,
        "shippingAddress": graphql_address_data,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
        "redirectUrl": redirect_url,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["draftOrderCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "country"
    assert errors[0]["code"] == OrderErrorCode.REQUIRED.name
    assert errors[0]["addressType"] == AddressType.BILLING.upper()


def test_draft_order_create_invalid_shipping_address(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data.copy()
    del shipping_address["country"]
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "billingAddress": graphql_address_data,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "channel": channel_id,
        "redirectUrl": redirect_url,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["draftOrderCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "country"
    assert errors[0]["code"] == OrderErrorCode.REQUIRED.name
    assert errors[0]["addressType"] == AddressType.SHIPPING.upper()


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_draft_order_create_price_recalculation(
    mock_fetch_order_prices_if_expired,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    product_available_in_many_channels,
    product_variant_list,
    channel_PLN,
    graphql_address_data,
    voucher,
):
    # given
    fake_order = Mock()
    fake_order.total = zero_taxed_money(channel_PLN.currency_code)
    response = Mock(return_value=(fake_order, None))
    mock_fetch_order_prices_if_expired.side_effect = response
    query = DRAFT_ORDER_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    discount = "10"
    variant_1 = product_available_in_many_channels.variants.first()
    variant_2 = product_variant_list[2]
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_2_id = graphene.Node.to_global_id("ProductVariant", variant_2.id)
    quantity_1 = 3
    quantity_2 = 4
    lines = [
        {"variantId": variant_1_id, "quantity": quantity_1},
        {"variantId": variant_2_id, "quantity": quantity_2},
    ]
    address = graphql_address_data
    voucher_amount = 13
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_PLN,
        discount=Money(voucher_amount, channel_PLN.currency_code),
    )
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "user": user_id,
        "discount": discount,
        "lines": lines,
        "billingAddress": address,
        "shippingAddress": address,
        "voucher": voucher_id,
        "channel": channel_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    lines = list(order.lines.all())
    mock_fetch_order_prices_if_expired.assert_called_once_with(order, ANY, lines, False)


DRAFT_UPDATE_QUERY = """
        mutation draftUpdate(
        $id: ID!,
        $input: DraftOrderInput!,
        ) {
            draftOrderUpdate(
                id: $id,
                input: $input
            ) {
                errors {
                    field
                    code
                    message
                }
                order {
                    userEmail
                    channel {
                        id
                    }
                }
            }
        }
        """


def test_draft_order_update_existing_channel_id(
    staff_api_client, permission_manage_orders, order_with_lines, channel_PLN
):
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    query = DRAFT_UPDATE_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": order_id,
        "input": {
            "channelId": channel_id,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]

    assert error["code"] == OrderErrorCode.NOT_EDITABLE.name
    assert error["field"] == "channelId"


def test_draft_order_update_voucher_not_available(
    staff_api_client, permission_manage_orders, order_with_lines, voucher
):
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    assert order.voucher is None
    query = DRAFT_UPDATE_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    voucher.channel_listings.all().delete()
    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]

    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "voucher"


DRAFT_ORDER_UPDATE_MUTATION = """
    mutation draftUpdate(
        $id: ID!, $voucher: ID!, $customerNote: String, $shippingAddress: AddressInput
    ) {
        draftOrderUpdate(id: $id,
                            input: {
                                voucher: $voucher,
                                customerNote: $customerNote,
                                shippingAddress: $shippingAddress,
                            }) {
            errors {
                field
                message
                code
            }
            order {
                userEmail
            }
        }
    }
"""


def test_draft_order_update(
    staff_api_client, permission_manage_orders, draft_order, voucher
):
    order = draft_order
    assert not order.voucher
    assert not order.customer_note
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    customer_note = "Test customer note"
    variables = {
        "id": order_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    order.refresh_from_db()
    assert order.voucher
    assert order.customer_note == customer_note
    assert order.search_vector


def test_draft_order_update_with_non_draft_order(
    staff_api_client, permission_manage_orders, order_with_lines, voucher
):
    order = order_with_lines
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    customer_note = "Test customer note"
    variables = {"id": order_id, "voucher": voucher_id, "customerNote": customer_note}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == OrderErrorCode.INVALID.name


def test_draft_order_update_invalid_address(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
):
    order = draft_order
    assert not order.voucher
    assert not order.customer_note
    graphql_address_data["postalCode"] = "TEST TEST invalid postal code 12345"
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    variables = {
        "id": order_id,
        "voucher": voucher_id,
        "shippingAddress": graphql_address_data,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert len(data["errors"]) == 2
    assert not data["order"]
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.INVALID.name,
        OrderErrorCode.REQUIRED.name,
    }
    assert {error["field"] for error in data["errors"]} == {"postalCode"}


def test_draft_order_update_doing_nothing_generates_no_events(
    staff_api_client, permission_manage_orders, order_with_lines
):
    assert not OrderEvent.objects.exists()

    query = """
        mutation draftUpdate($id: ID!) {
            draftOrderUpdate(id: $id, input: {}) {
                errors {
                    field
                    message
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    response = staff_api_client.post_graphql(
        query, {"id": order_id}, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)

    # Ensure not event was created
    assert not OrderEvent.objects.exists()


def test_draft_order_update_free_shipping_voucher(
    staff_api_client, permission_manage_orders, draft_order, voucher_free_shipping
):
    order = draft_order
    assert not order.voucher
    query = """
        mutation draftUpdate(
            $id: ID!
            $voucher: ID!
        ) {
            draftOrderUpdate(
                id: $id
                input: {
                    voucher: $voucher
                }
            ) {
                errors {
                    field
                    message
                    code
                }
                order {
                    id
                }
            }
        }
        """
    voucher = voucher_free_shipping
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "id": order_id,
        "voucher": voucher_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["id"] == variables["id"]
    order.refresh_from_db()
    assert order.voucher


DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION = """
    mutation draftUpdate(
        $id: ID!
        $userEmail: String!
    ) {
        draftOrderUpdate(
            id: $id
            input: {
                userEmail: $userEmail
            }
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
        }
    }
    """


def test_draft_order_update_when_not_existing_customer_email_provided(
    staff_api_client, permission_manage_orders, draft_order
):
    # given
    order = draft_order
    assert order.user

    query = DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    email = "notexisting@example.com"
    variables = {"id": order_id, "userEmail": email}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert not order.user
    assert order.user_email == email


def test_draft_order_update_assign_user_when_existing_customer_email_provided(
    staff_api_client, permission_manage_orders, draft_order
):
    # given
    order = draft_order
    user = order.user
    user_email = user.email
    order.user = None
    order.save(update_fields=["user"])
    assert not order.user

    query = DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "userEmail": user_email}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert order.user == user
    assert order.user_email == user_email


def test_draft_order_delete(staff_api_client, permission_manage_orders, draft_order):
    order = draft_order
    query = """
        mutation draftDelete($id: ID!) {
            draftOrderDelete(id: $id) {
                order {
                    id
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    with pytest.raises(order._meta.model.DoesNotExist):
        order.refresh_from_db()


@pytest.mark.parametrize(
    "order_status",
    [
        OrderStatus.UNFULFILLED,
        OrderStatus.UNCONFIRMED,
        OrderStatus.CANCELED,
        OrderStatus.PARTIALLY_FULFILLED,
        OrderStatus.FULFILLED,
        OrderStatus.PARTIALLY_RETURNED,
        OrderStatus.RETURNED,
    ],
)
def test_draft_order_delete_non_draft_order(
    staff_api_client, permission_manage_orders, order_with_lines, order_status
):
    order = order_with_lines
    order.status = order_status
    order.save(update_fields=["status"])
    query = """
        mutation draftDelete($id: ID!) {
            draftOrderDelete(id: $id) {
                order {
                    id
                }
                errors {
                    code
                    field
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    account_errors = content["data"]["draftOrderDelete"]["errors"]
    assert len(account_errors) == 1
    assert account_errors[0]["field"] == "id"
    assert account_errors[0]["code"] == OrderErrorCode.INVALID.name


ORDER_CAN_FINALIZE_QUERY = """
    query OrderQuery($id: ID!){
        order(id: $id){
            canFinalize
            errors {
                code
                field
                message
                warehouse
                orderLines
                variants
            }
        }
    }
"""


def test_can_finalize_order(staff_api_client, permission_manage_orders, draft_order):
    order_id = graphene.Node.to_global_id("Order", draft_order.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is True
    assert not content["data"]["order"]["errors"]


def test_can_finalize_order_without_sku(
    staff_api_client, permission_manage_orders, draft_order
):
    ProductVariant.objects.update(sku=None)
    draft_order.lines.update(product_sku=None)

    order_id = graphene.Node.to_global_id("Order", draft_order.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is True
    assert not content["data"]["order"]["errors"]


def test_can_finalize_order_invalid_shipping_method_set(
    staff_api_client, permission_manage_orders, draft_order
):
    order_id = graphene.Node.to_global_id("Order", draft_order.id)
    draft_order.channel.shipping_zones.clear()
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is False
    errors = content["data"]["order"]["errors"]
    assert len(errors) == 3
    assert {error["code"] for error in errors} == {
        OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name,
        OrderErrorCode.INSUFFICIENT_STOCK.name,
    }
    assert {error["field"] for error in errors} == {"shipping", "lines"}


def test_can_finalize_order_no_order_lines(
    staff_api_client, permission_manage_orders, order
):
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is False
    errors = content["data"]["order"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.REQUIRED.name
    assert errors[0]["field"] == "lines"


def test_can_finalize_order_product_unavailable_for_purchase(
    staff_api_client, permission_manage_orders, draft_order
):
    # given
    order = draft_order

    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    product = line.variant.product
    product.channel_listings.update(available_for_purchase_at=None)

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is False
    errors = content["data"]["order"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["orderLines"] == [graphene.Node.to_global_id("OrderLine", line.pk)]


def test_can_finalize_order_product_available_for_purchase_from_tomorrow(
    staff_api_client, permission_manage_orders, draft_order
):
    # given
    order = draft_order

    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    product = line.variant.product
    product.channel_listings.update(
        available_for_purchase_at=datetime.now(pytz.UTC) + timedelta(days=1)
    )

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is False
    errors = content["data"]["order"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["orderLines"] == [graphene.Node.to_global_id("OrderLine", line.pk)]


def test_validate_draft_order(draft_order):
    # should not raise any errors
    assert validate_draft_order(draft_order, "US", get_plugins_manager()) is None


def test_validate_draft_order_without_sku(draft_order):
    ProductVariant.objects.update(sku=None)
    draft_order.lines.update(product_sku=None)
    # should not raise any errors
    assert validate_draft_order(draft_order, "US", get_plugins_manager()) is None


def test_validate_draft_order_wrong_shipping(draft_order):
    order = draft_order
    shipping_zone = order.shipping_method.shipping_zone
    shipping_zone.countries = ["DE"]
    shipping_zone.save()
    assert order.shipping_address.country.code not in shipping_zone.countries
    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    msg = "Shipping method is not valid for chosen shipping address"
    assert e.value.error_dict["shipping"][0].message == msg


def test_validate_draft_order_no_order_lines(order, shipping_method):
    order.shipping_method = shipping_method
    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    msg = "Could not create order without any products."
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_non_existing_variant(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    variant.delete()
    line.refresh_from_db()
    assert line.variant is None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    msg = "Could not create orders with non-existing products."
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_with_unpublished_product(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    product_channel_listing = variant.product.channel_listings.get()
    product_channel_listing.is_published = False
    product_channel_listing.save(update_fields=["is_published"])
    line.refresh_from_db()

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    msg = "Can't finalize draft with unpublished product."
    error = e.value.error_dict["lines"][0]

    assert error.message == msg
    assert error.code == OrderErrorCode.PRODUCT_NOT_PUBLISHED.value


def test_validate_draft_order_with_unavailable_for_purchase_product(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    variant.product.channel_listings.update(available_for_purchase_at=None)
    line.refresh_from_db()

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    msg = "Can't finalize draft with product unavailable for purchase."
    error = e.value.error_dict["lines"][0]

    assert error.message == msg
    assert error.code == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value


def test_validate_draft_order_with_product_available_for_purchase_in_future(
    draft_order,
):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    variant.product.channel_listings.update(
        available_for_purchase_at=datetime.now(pytz.UTC) + timedelta(days=2)
    )
    line.refresh_from_db()

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    msg = "Can't finalize draft with product unavailable for purchase."
    error = e.value.error_dict["lines"][0]

    assert error.message == msg
    assert error.code == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value


def test_validate_draft_order_out_of_stock_variant(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant

    stock = variant.stocks.get()
    stock.quantity = 0
    stock.save(update_fields=["quantity"])

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    msg = "Insufficient product stock: SKU_AA"
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_no_shipping_address(draft_order):
    order = draft_order
    order.shipping_address = None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    error = e.value.error_dict["order"][0]
    assert error.message == "Can't finalize draft with no shipping address."
    assert error.code == OrderErrorCode.ORDER_NO_SHIPPING_ADDRESS.value


def test_validate_draft_order_no_billing_address(draft_order):
    order = draft_order
    order.billing_address = None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    error = e.value.error_dict["order"][0]
    assert error.message == "Can't finalize draft with no billing address."
    assert error.code == OrderErrorCode.BILLING_ADDRESS_NOT_SET.value


def test_validate_draft_order_no_shipping_method(draft_order):
    order = draft_order
    order.shipping_method = None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US", get_plugins_manager())
    error = e.value.error_dict["shipping"][0]
    assert error.message == "Shipping method is required."
    assert error.code == OrderErrorCode.SHIPPING_METHOD_REQUIRED.value


def test_validate_draft_order_no_shipping_method_shipping_not_required(draft_order):
    order = draft_order
    order.shipping_method = None
    required_mock = Mock(return_value=False)
    order.is_shipping_required = required_mock

    assert validate_draft_order(order, "US", get_plugins_manager()) is None


def test_validate_draft_order_no_shipping_address_no_method_shipping_not_required(
    draft_order,
):
    order = draft_order
    order.shipping_method = None
    order.shipping_address = None
    required_mock = Mock(return_value=False)
    order.is_shipping_required = required_mock

    assert validate_draft_order(order, "US", get_plugins_manager()) is None


DRAFT_ORDER_COMPLETE_MUTATION = """
    mutation draftComplete($id: ID!) {
        draftOrderComplete(id: $id) {
            errors {
                field
                code
                message
                variants
            }
            order {
                status
                origin
                paymentStatus
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.search_vector

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_0_total(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    """Ensure the payment status is FULLY_CHARGED when the total order price is 0."""
    order = draft_order
    price = zero_taxed_money(order.currency)
    order.shipping_price = price
    order.total = price
    order.save(
        update_fields=[
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "total_net_amount",
            "total_gross_amount",
        ]
    )

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    payment_charge_status = PaymentChargeStatusEnum.FULLY_CHARGED
    assert data["paymentStatus"] == payment_charge_status.name
    assert order.search_vector

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_without_sku(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    ProductVariant.objects.update(sku=None)
    draft_order.lines.update(product_sku=None)

    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    draft_order,
):
    order = draft_order
    first_line = order.lines.first()
    first_line.quantity = 5
    first_line.save()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    total_stock = Stock.objects.aggregate(Sum("quantity"))["quantity__sum"]
    total_allocation = Allocation.objects.filter(order_line__order=order).aggregate(
        Sum("quantity_allocated")
    )["quantity_allocated__sum"]
    assert total_stock == total_allocation
    assert product_variant_out_of_stock_webhook_mock.call_count == 2
    product_variant_out_of_stock_webhook_mock.assert_called_with(Stock.objects.last())


def test_draft_order_from_reissue_complete(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    order.origin = OrderOrigin.REISSUE
    order.save(update_fields=["origin"])

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.REISSUE.upper()

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_with_inactive_channel(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    channel = order.channel
    channel.is_active = False
    channel.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.CHANNEL_INACTIVE.name
    assert data["errors"][0]["field"] == "channel"


def test_draft_order_complete_with_unavailable_variant(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    variant = order.lines.first().variant
    variant.channel_listings.filter(channel=order.channel).delete()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert data["errors"][0]["field"] == "lines"
    assert data["errors"][0]["variants"] == [variant_id]


def test_draft_order_complete_channel_without_shipping_zones(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    order.channel.shipping_zones.clear()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]

    assert len(data["errors"]) == 3
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name,
        OrderErrorCode.INSUFFICIENT_STOCK.name,
    }
    assert {error["field"] for error in data["errors"]} == {"shipping", "lines"}


def test_draft_order_complete_product_without_inventory_tracking(
    staff_api_client,
    shipping_method,
    permission_manage_orders,
    staff_user,
    draft_order_without_inventory_tracking,
):
    order = draft_order_without_inventory_tracking
    order.shipping_method = shipping_method
    order.save()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]

    assert not content["data"]["draftOrderComplete"]["errors"]

    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    assert not Allocation.objects.filter(order_line__order=order).exists()

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_not_available_shipping_method(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    # given
    order = draft_order
    order.channel.shipping_zones.clear()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]

    assert len(data["errors"]) == 3
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name,
        OrderErrorCode.INSUFFICIENT_STOCK.name,
    }
    assert {error["field"] for error in data["errors"]} == {"shipping", "lines"}


@patch("saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_order")
def test_draft_order_complete_with_excluded_shipping_method(
    mocked_webhook,
    draft_order,
    shipping_method,
    staff_api_client,
    permission_manage_orders,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "archives-are-incomplete"
    mocked_webhook.return_value = [
        ExcludedShippingMethod(str(shipping_method.id), webhook_reason)
    ]
    order = draft_order
    order.status = OrderStatus.DRAFT
    order.shipping_method = shipping_method
    order.save()
    query = DRAFT_ORDER_COMPLETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert (
        data["errors"][0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    )
    assert data["errors"][0]["field"] == "shipping"


@patch("saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_order")
def test_draft_order_complete_with_not_excluded_shipping_method(
    mocked_webhook,
    draft_order,
    shipping_method,
    staff_api_client,
    permission_manage_orders,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "archives-are-incomplete"
    other_shipping_method_id = "1337"
    assert other_shipping_method_id != shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(other_shipping_method_id, webhook_reason)
    ]
    order = draft_order
    order.status = OrderStatus.DRAFT
    order.shipping_method = shipping_method
    order.save()
    query = DRAFT_ORDER_COMPLETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert len(data["errors"]) == 0


def test_draft_order_complete_out_of_stock_variant(
    staff_api_client, permission_manage_orders, staff_user, draft_order
):
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    line_1, _ = order.lines.order_by("-quantity").all()
    stock_1 = Stock.objects.get(product_variant=line_1.variant)
    line_1.quantity = get_available_quantity_for_stock(stock_1) + 1
    line_1.save(update_fields=["quantity"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name


def test_draft_order_complete_existing_user_email_updates_user_field(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    order = draft_order
    order.user_email = customer_user.email
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user == customer_user


def test_draft_order_complete_anonymous_user_email_sets_user_field_null(
    staff_api_client, draft_order, permission_manage_orders
):
    order = draft_order
    order.user_email = "anonymous@example.com"
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user is None


def test_draft_order_complete_anonymous_user_no_email(
    staff_api_client, draft_order, permission_manage_orders
):
    order = draft_order
    order.user_email = ""
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    assert data["status"] == OrderStatus.UNFULFILLED.upper()


def test_draft_order_complete_drops_shipping_address(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
    address,
):
    order = draft_order
    order.shipping_address = address.get_copy()
    order.billing_address = address.get_copy()
    order.save()
    order.lines.update(is_shipping_required=False)

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()

    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.shipping_address is None


def test_draft_order_complete_unavailable_for_purchase(
    staff_api_client, permission_manage_orders, staff_user, draft_order
):
    # given
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    product = order.lines.first().variant.product
    product.channel_listings.update(
        available_for_purchase_at=datetime.now(pytz.UTC) + timedelta(days=5)
    )

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name


def test_draft_order_complete_preorders(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order_with_preorder_lines,
):
    order = draft_order_with_preorder_lines

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no preorder allocation were created
    assert not PreorderAllocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    for line in order.lines.all():
        preorder_allocation = line.preorder_allocations.get()
        assert preorder_allocation.quantity == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_insufficient_stock_preorders(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order_with_preorder_lines,
    channel_USD,
):
    order = draft_order_with_preorder_lines

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    line = order.lines.order_by("-quantity").first()
    channel_listing = line.variant.channel_listings.get(channel_id=channel_USD.id)
    line.quantity = channel_listing.preorder_quantity_threshold + 1
    line.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name


def test_draft_order_complete_not_draft_order(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "id"


ORDER_LINES_CREATE_MUTATION = """
    mutation OrderLinesCreate(
            $orderId: ID!, $variantId: ID!, $quantity: Int!, $forceNewLine: Boolean
        ) {
        orderLinesCreate(id: $orderId,
                input: [
                    {
                        variantId: $variantId,
                        quantity: $quantity,
                        forceNewLine: $forceNewLine
                    }
                ]) {

            errors {
                field
                code
                message
                variants
            }
            orderLines {
                id
                quantity
                productSku
                productVariantId
                unitPrice {
                    gross {
                        amount
                        currency
                    }
                    net {
                        amount
                        currency
                    }
                }
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    variant = line.variant
    quantity = 2
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(query, variables)

    quantity_allocated = Allocation.objects.aggregate(Sum("quantity_allocated"))[
        "quantity_allocated__sum"
    ]
    stock_quantity = Allocation.objects.aggregate(Sum("stock__quantity"))[
        "stock__quantity__sum"
    ]
    assert quantity_allocated == stock_quantity
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.first()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create_for_variant_with_many_stocks_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    quantity = 4
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(query, variables)
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.all()[3]
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create(
    product_variant_out_of_stock_webhook_mock,
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()
    assert not OrderEvent.objects.exists()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    assert OrderEvent.objects.count() == 1
    event = OrderEvent.objects.last()
    assert event.type == order_events.OrderEvents.ADDED_PRODUCTS
    assert len(event.parameters["lines"]) == 1
    line = OrderLine.objects.last()
    assert event.parameters["lines"] == [
        {"item": str(line), "line_pk": str(line.pk), "quantity": quantity}
    ]

    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity

    # mutation should fail when quantity is lower than 1
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"
    assert data["errors"][0]["variants"] == [variant_id]
    product_variant_out_of_stock_webhook_mock.assert_not_called()


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create_for_just_published_product(
    product_variant_out_of_stock_webhook_mock,
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    product_listing = variant.product.channel_listings.get(channel=order.channel)
    product_listing.published_at = datetime.now(pytz.utc)
    product_listing.save(update_fields=["published_at"])

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_unavailable_variant(
    order_updated_webhook_mock,
    draft_order_updated_webhoook_mock,
    draft_order,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = draft_order
    channel = order.channel
    line = order.lines.first()
    variant = line.variant
    variant.channel_listings.filter(channel=channel).update(price_amount=None)
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhoook_mock.assert_not_called()


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_existing_variant(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    variant = line.variant
    old_quantity = line.quantity
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    assert not OrderEvent.objects.exists()
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == old_quantity + quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_same_variant_and_force_new_line(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    lines = order.lines.all()
    assert len(lines) == 2
    line = lines[0]
    variant = line.variant

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "forceNewLine": True,
    }

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    assert not OrderEvent.objects.exists()
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    response = staff_api_client.post_graphql(query, variables)
    assert order.lines.count() == 3
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_when_variant_already_in_multiple_lines(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])

    line = order.lines.first()
    variant = line.variant

    # copy line and add to order
    line.id = None
    line.save()

    assert order.lines.count() == 3

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "forceNewLine": True,
    }

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    response = staff_api_client.post_graphql(ORDER_LINES_CREATE_MUTATION, variables)

    assert order.lines.count() == 4
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_variant_on_sale(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
    sale,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION

    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])

    variant = variant_with_many_stocks
    sale.variants.add(variant)

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    line_data = data["orderLines"][0]
    assert line_data["productSku"] == variant.sku
    assert line_data["quantity"] == quantity
    assert line_data["quantity"] == quantity
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    sale_channel_listing = sale.channel_listings.first()
    assert (
        line_data["unitPrice"]["gross"]["amount"]
        == variant_channel_listing.price_amount - sale_channel_listing.discount_value
    )
    assert (
        line_data["unitPrice"]["net"]["amount"]
        == variant_channel_listing.price_amount - sale_channel_listing.discount_value
    )

    line = order.lines.get(product_sku=variant.sku)
    assert line.sale_id == graphene.Node.to_global_id("Sale", sale.id)
    assert line.unit_discount_amount == sale_channel_listing.discount_value
    assert line.unit_discount_value == sale_channel_listing.discount_value
    assert (
        line.unit_discount_reason
        == f"Sale: {graphene.Node.to_global_id('Sale', sale.id)}"
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_product_and_variant_not_assigned_to_channel(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    assert variant != line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    variant.product.channel_listings.all().delete()
    variant.channel_listings.all().delete()

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.PRODUCT_NOT_PUBLISHED.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_variant_not_assigned_to_channel(
    order_update_webhook_mock,
    draft_order_update_webhook_mock,
    status,
    order_with_lines,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    assert variant != line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    variant.channel_listings.all().delete()

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_update_webhook_mock.assert_not_called()
    draft_order_update_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
def test_order_lines_create_without_sku(
    product_variant_out_of_stock_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    ProductVariant.objects.update(sku=None)
    order_with_lines.lines.update(product_sku=None)

    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    assert not OrderEvent.objects.exists()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] is None
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity

    # mutation should fail when quantity is lower than 1
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"
    assert data["errors"][0]["variants"] == [variant_id]
    product_variant_out_of_stock_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_invalid_order_when_creating_lines(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    staff_api_client,
    permission_manage_orders,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()


ORDER_LINE_UPDATE_MUTATION = """
    mutation OrderLineUpdate($lineId: ID!, $quantity: Int!) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity}) {
            errors {
                field
                message
            }
            orderLine {
                id
                quantity
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_line_update_with_out_of_stock_webhook_for_two_lines_success_scenario(
    out_of_stock_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    Stock.objects.update(quantity=5)
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    first_line, second_line = order.lines.all()
    new_quantity = 5

    first_line_id = graphene.Node.to_global_id("OrderLine", first_line.id)
    second_line_id = graphene.Node.to_global_id("OrderLine", second_line.id)

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    variables = {"lineId": first_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    variables = {"lineId": second_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    assert out_of_stock_mock.call_count == 2
    out_of_stock_mock.assert_called_with(Stock.objects.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_line_update_with_out_of_stock_webhook_success_scenario(
    out_of_stock_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 5
    line_id = graphene.Node.to_global_id("OrderLine", line.id)

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    variables = {"lineId": line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    out_of_stock_mock.assert_called_once_with(Stock.objects.first())


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_update_with_back_in_stock_webhook_fail_scenario(
    product_variant_back_in_stock_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    variables = {"lineId": line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    product_variant_back_in_stock_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_update_with_back_in_stock_webhook_called_once_success_scenario(
    back_in_stock_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    first_allocated = Allocation.objects.first()
    first_allocated.quantity_allocated = 5
    first_allocated.save()

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    staff_api_client.post_graphql(query, variables)
    back_in_stock_mock.assert_called_once_with(first_allocated.stock)


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_update_with_back_in_stock_webhook_called_twice_success_scenario(
    product_variant_back_in_stock_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    first_allocation = Allocation.objects.first()
    first_allocation.quantity_allocated = 5
    first_allocation.save()

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    first_line, second_line = order.lines.all()
    new_quantity = 1
    first_line_id = graphene.Node.to_global_id("OrderLine", first_line.id)
    second_line_id = graphene.Node.to_global_id("OrderLine", second_line.id)

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    variables = {"lineId": first_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    variables = {"lineId": second_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    assert product_variant_back_in_stock_webhook_mock.call_count == 2
    product_variant_back_in_stock_webhook_mock.assert_called_with(Stock.objects.last())


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_update(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    staff_user,
):
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    removed_quantity = 2
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # Ensure the line has the expected quantity
    assert line.quantity == 3

    # No event should exist yet
    assert not OrderEvent.objects.exists()

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert removed_items_event.user == staff_user
    assert removed_items_event.parameters == {
        "lines": [
            {"quantity": removed_quantity, "line_pk": str(line.pk), "item": str(line)}
        ]
    }

    # mutation should fail when quantity is lower than 1
    variables = {"lineId": line_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
def test_order_line_update_without_sku(
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    staff_user,
):
    ProductVariant.objects.update(sku=None)

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    removed_quantity = 2
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # Ensure the line has the expected quantity
    assert line.quantity == 3

    # No event should exist yet
    assert not OrderEvent.objects.exists()

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity

    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert removed_items_event.user == staff_user
    assert removed_items_event.parameters == {
        "lines": [
            {"quantity": removed_quantity, "line_pk": str(line.pk), "item": str(line)}
        ]
    }

    line.refresh_from_db()
    assert line.product_sku
    assert line.product_variant_id == line.variant.get_global_id()

    # mutation should fail when quantity is lower than 1
    variables = {"lineId": line_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_invalid_order_when_updating_lines(
    order_update_webhook_mock,
    draft_order_update_webhook_mock,
    order_with_lines,
    staff_api_client,
    permission_manage_orders,
):
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["errors"]
    order_update_webhook_mock.assert_not_called()
    draft_order_update_webhook_mock.assert_not_called()


QUERY_GET_FIRST_EVENT = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        events {
                            lines {
                                quantity
                                orderLine {
                                    id
                                }
                            }
                            fulfilledItems {
                                id
                            }
                        }
                    }
                }
            }
        }
    """


def test_retrieving_event_lines_with_deleted_line(
    staff_api_client, order_with_lines, staff_user, permission_manage_orders
):
    order = order_with_lines
    lines = order_with_lines.lines.all()

    # Create the test event
    order_events.order_added_products_event(
        order=order, user=staff_user, app=None, order_lines=lines
    )

    # Delete a line
    deleted_line = lines.first()
    deleted_line.delete()

    # Prepare the query
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # Send the query and retrieve the data
    content = get_graphql_content(staff_api_client.post_graphql(QUERY_GET_FIRST_EVENT))
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    # Check every line is returned and the one deleted is None
    assert len(data["lines"]) == len(lines)
    for expected_data, received_line in zip(lines, data["lines"]):
        quantity = expected_data.quantity
        line = expected_data

        if line is deleted_line:
            assert received_line["orderLine"] is None
        else:
            assert received_line["orderLine"] is not None
            assert received_line["orderLine"]["id"] == graphene.Node.to_global_id(
                "OrderLine", line.pk
            )

        assert received_line["quantity"] == quantity


def test_retrieving_event_lines_with_missing_line_pk_in_data(
    staff_api_client, order_with_lines, staff_user, permission_manage_orders
):
    order = order_with_lines
    line = order_with_lines.lines.first()

    # Create the test event
    event = order_events.order_added_products_event(
        order=order, user=staff_user, app=None, order_lines=[line]
    )
    del event.parameters["lines"][0]["line_pk"]
    event.save(update_fields=["parameters"])

    # Prepare the query
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # Send the query and retrieve the data
    content = get_graphql_content(staff_api_client.post_graphql(QUERY_GET_FIRST_EVENT))
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    # Check every line is returned and the one deleted is None
    received_line = data["lines"][0]
    assert len(data["lines"]) == 1
    assert received_line["quantity"] == line.quantity
    assert received_line["orderLine"] is None


ORDER_LINE_DELETE_MUTATION = """
    mutation OrderLineDelete($id: ID!) {
        orderLineDelete(id: $id) {
            errors {
                field
                message
            }
            orderLine {
                id
            }
            order {
                id
                total{
                    gross{
                        currency
                        amount
                    }
                    net {
                        currency
                        amount
                    }
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_remove_with_back_in_stock_webhook(
    back_in_stock_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    Stock.objects.update(quantity=3)
    first_stock = Stock.objects.first()
    assert (
        first_stock.quantity
        - (
            first_stock.allocations.aggregate(Sum("quantity_allocated"))[
                "quantity_allocated__sum"
            ]
            or 0
        )
    ) == 0

    query = ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    line = order.lines.first()

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert data["orderLine"]["id"] == line_id
    assert line not in order.lines.all()
    first_stock.refresh_from_db()
    assert (
        first_stock.quantity
        - (
            first_stock.allocations.aggregate(Sum("quantity_allocated"))[
                "quantity_allocated__sum"
            ]
            or 0
        )
    ) == 3
    back_in_stock_webhook_mock.assert_called_once_with(Stock.objects.first())


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_remove(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert data["orderLine"]["id"] == line_id
    assert line not in order.lines.all()
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_invalid_order_when_removing_lines(
    order_update_webhook_mock,
    draft_order_update_webhook_mock,
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
):
    query = ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert data["errors"]
    order_update_webhook_mock.assert_not_called()
    draft_order_update_webhook_mock.assert_not_called()


ORDER_UPDATE_MUTATION = """
    mutation orderUpdate($id: ID!, $email: String, $address: AddressInput) {
        orderUpdate(
            id: $id, input: {
                userEmail: $email,
                shippingAddress: $address,
                billingAddress: $address}) {
            errors {
                field
                code
            }
            order {
                userEmail
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    order_updated_webhook_mock.assert_called_once_with(order)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_with_draft_order(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    draft_order,
    graphql_address_data,
):
    order = draft_order
    order.user = None
    order.save()
    email = "not_default@example.com"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderUpdate"]["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == OrderErrorCode.INVALID.name
    order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_without_sku(
    plugin_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    ProductVariant.objects.update(sku=None)
    order_with_lines.lines.update(product_sku=None)

    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    assert plugin_mock.called is True


def test_order_update_anonymous_user_no_user_email(
    staff_api_client, order_with_lines, permission_manage_orders, graphql_address_data
):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
            mutation orderUpdate(
            $id: ID!, $address: AddressInput) {
                orderUpdate(
                    id: $id, input: {
                        shippingAddress: $address,
                        billingAddress: $address}) {
                    errors {
                        field
                        message
                    }
                    order {
                        id
                    }
                }
            }
            """
    first_name = "Test fname"
    last_name = "Test lname"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)
    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name != first_name
    assert order.billing_address.last_name != last_name
    assert order.status == OrderStatus.UNFULFILLED


def test_order_update_user_email_existing_user(
    staff_api_client,
    order_with_lines,
    customer_user,
    permission_manage_orders,
    graphql_address_data,
):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email, shippingAddress: $address,
                    billingAddress: $address}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    email = customer_user.email
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data, "email": email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user == customer_user


ORDER_ADD_NOTE_MUTATION = """
    mutation addNote($id: ID!, $message: String!) {
        orderAddNote(order: $id, input: {message: $message}) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
            event {
                user {
                    email
                }
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_add_note_as_staff_user(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    staff_user,
):
    """We are testing that adding a note to an order as a staff user is doing the
    expected behaviors."""
    order = order_with_lines
    assert not order.events.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}
    response = staff_api_client.post_graphql(
        ORDER_ADD_NOTE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderAddNote"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["message"] == message
    order_updated_webhook_mock.assert_called_once_with(order)

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED

    # Ensure the correct order event was created
    event = order.events.get()
    assert event.type == order_events.OrderEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}

    # Ensure not customer events were created as it was a staff action
    assert not CustomerEvent.objects.exists()


@pytest.mark.parametrize(
    "message",
    (
        "",
        "   ",
    ),
)
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_add_note_fail_on_empty_message(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    message,
):
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id, "message": message}
    response = staff_api_client.post_graphql(
        ORDER_ADD_NOTE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderAddNote"]
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == OrderErrorCode.REQUIRED.name
    order_updated_webhook_mock.assert_not_called()


MUTATION_ORDER_CANCEL = """
mutation cancelOrder($id: ID!) {
    orderCancel(id: $id) {
        order {
            status
        }
        errors{
            field
            code
        }
    }
}
"""


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel(
    mock_clean_order_cancel,
    mock_cancel_order,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=staff_api_client.user, app=None, manager=ANY
    )


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel_as_app(
    mock_clean_order_cancel,
    mock_cancel_order,
    app_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=AnonymousUser(), app=app_api_client.app, manager=ANY
    )


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel_with_bought_gift_cards(
    mock_clean_order_cancel,
    mock_cancel_order,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    gift_card,
):
    order = order_with_lines
    gift_cards_bought_event([gift_card], order, staff_api_client.user, None)
    assert gift_card.is_active is True
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=staff_api_client.user, app=None, manager=ANY
    )

    gift_card.refresh_from_db()
    assert gift_card.is_active is False
    assert gift_card.events.filter(type=GiftCardEvents.DEACTIVATED)


ORDER_CAPTURE_MUTATION = """
        mutation captureOrder($id: ID!, $amount: PositiveDecimal!) {
            orderCapture(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    paymentStatusDisplay
                    isPaid
                    totalCaptured {
                        amount
                    }
                }
                errors{
                    field
                    message
                    code
                }
            }
        }
"""


@patch("saleor.giftcard.utils.fulfill_non_shippable_gift_cards")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_order_capture(
    mocked_notify,
    fulfill_non_shippable_gift_cards_mock,
    staff_api_client,
    permission_manage_orders,
    payment_txn_preauth,
    staff_user,
    site_settings,
):
    # given
    order = payment_txn_preauth.order

    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_preauth.total)
    variables = {"id": order_id, "amount": amount}

    # when
    response = staff_api_client.post_graphql(
        ORDER_CAPTURE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCapture"]["order"]
    order.refresh_from_db()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"]
    assert data["totalCaptured"]["amount"] == float(amount)

    event_captured, event_order_fully_paid = order.events.all()

    assert event_captured.type == order_events.OrderEvents.PAYMENT_CAPTURED
    assert event_captured.user == staff_user
    assert event_captured.parameters == {
        "amount": str(amount),
        "payment_gateway": "mirumee.payments.dummy",
        "payment_id": "",
    }

    assert event_order_fully_paid.type == order_events.OrderEvents.ORDER_FULLY_PAID
    assert event_order_fully_paid.user == staff_user

    payment = Payment.objects.get()
    expected_payment_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "payment": {
            "created": payment.created_at,
            "modified": payment.modified_at,
            "charge_status": payment.charge_status,
            "total": payment.total,
            "captured_amount": payment.captured_amount,
            "currency": payment.currency,
        },
        "site_name": "mirumee.com",
        "domain": "mirumee.com",
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
        expected_payment_payload,
        channel_slug=order.channel.slug,
    )
    fulfill_non_shippable_gift_cards_mock.assert_called_once_with(
        order, list(order.lines.all()), site_settings, staff_api_client.user, None, ANY
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_action_request")
def test_order_charge_with_transaction_action_request(
    mocked_transaction_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    transaction = TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["charge", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )
    charge_value = Decimal(5.0)
    mocked_is_active.return_value = True
    order_id = to_global_id_or_none(order)

    variables = {"id": order_id, "amount": charge_value}

    # when
    response = staff_api_client.post_graphql(
        ORDER_CAPTURE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCapture"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_transaction_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=charge_value,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_CAPTURE_REQUESTED
    assert Decimal(event.parameters["amount"]) == charge_value
    assert event.parameters["reference"] == transaction.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_order_capture_with_transaction_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    authorization_value = Decimal("10")
    TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorization_value,
    )
    mocked_is_active.return_value = False

    order_id = to_global_id_or_none(order)

    variables = {"id": order_id, "amount": authorization_value}

    # when
    response = staff_api_client.post_graphql(
        ORDER_CAPTURE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderCapture"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    assert data["errors"][0]["code"] == (
        OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called


MUTATION_MARK_ORDER_AS_PAID = """
    mutation markPaid($id: ID!, $transaction: String) {
        orderMarkAsPaid(id: $id, transactionReference: $transaction) {
            errors {
                field
                message
            }
            errors {
                field
                message
                code
            }
            order {
                isPaid
                events{
                    transactionReference
                }
            }
        }
    }
"""


def test_paid_order_mark_as_paid(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    order = payment_txn_preauth.order
    query = MUTATION_MARK_ORDER_AS_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderMarkAsPaid"]["errors"]
    msg = "Orders with payments can not be manually marked as paid."
    assert errors[0]["message"] == msg
    assert errors[0]["field"] == "payment"

    order_errors = content["data"]["orderMarkAsPaid"]["errors"]
    assert order_errors[0]["code"] == OrderErrorCode.PAYMENT_ERROR.name


def test_order_mark_as_paid_with_external_reference(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    transaction_reference = "searchable-id"
    order = order_with_lines
    query = MUTATION_MARK_ORDER_AS_PAID
    assert not order.is_fully_paid()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "transaction": transaction_reference}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert data["isPaid"] is True
    assert len(data["events"]) == 1
    assert data["events"][0]["transactionReference"] == transaction_reference
    assert order.is_fully_paid()
    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user == staff_user
    event_reference = event_order_paid.parameters.get("transaction_reference")
    assert event_reference == transaction_reference
    order_payments = order.payments.filter(psp_reference=transaction_reference)
    assert order_payments.count() == 1


def test_order_mark_as_paid(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    order = order_with_lines
    query = MUTATION_MARK_ORDER_AS_PAID
    assert not order.is_fully_paid()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert data["isPaid"] is True is order.is_fully_paid()

    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user == staff_user


def test_order_mark_as_paid_no_billing_address(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    order = order_with_lines
    order_with_lines.billing_address = None
    order_with_lines.save()

    query = MUTATION_MARK_ORDER_AS_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderMarkAsPaid"]["errors"]
    assert data[0]["code"] == OrderErrorCode.BILLING_ADDRESS_NOT_SET.name


def test_draft_order_mark_as_paid_check_price_recalculation(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    # given
    order = order_with_lines
    # we need to change order total and set it as invalidated prices.
    # we couldn't use `order.total.gross` because this test don't use any tax app
    # or plugin.
    expected_total_net = order.total.net
    expected_total = TaxedMoney(net=expected_total_net, gross=expected_total_net)
    order.total = TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
    order.should_refresh_prices = True
    order.status = OrderStatus.DRAFT
    order.save()
    query = MUTATION_MARK_ORDER_AS_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert order.total == expected_total
    payment = order.payments.get()
    assert payment.total == expected_total_net.amount
    assert data["isPaid"] is True is order.is_fully_paid()
    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user == staff_user


ORDER_VOID = """
    mutation voidOrder($id: ID!) {
        orderVoid(id: $id) {
            order {
                paymentStatus
                paymentStatusDisplay
            }
            errors {
                field
                message
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_order_void(
    staff_api_client, permission_manage_orders, payment_txn_preauth, staff_user
):
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]["order"]
    assert data["paymentStatus"] == PaymentChargeStatusEnum.NOT_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    event_payment_voided = order.events.last()
    assert event_payment_voided.type == order_events.OrderEvents.PAYMENT_VOIDED
    assert event_payment_voided.user == staff_user
    order.refresh_from_db()


@patch.object(PluginsManager, "void_payment")
def test_order_void_payment_error(
    mock_void_payment, staff_api_client, permission_manage_orders, payment_txn_preauth
):
    msg = "Oops! Something went wrong."
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    mock_void_payment.side_effect = ValueError(msg)
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderVoid"]["errors"]
    assert errors[0]["field"] == "payment"
    assert errors[0]["message"] == msg

    order_errors = content["data"]["orderVoid"]["errors"]
    assert order_errors[0]["code"] == OrderErrorCode.PAYMENT_ERROR.name

    mock_void_payment.assert_called_once()


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_action_request")
def test_order_void_with_transaction_action_request(
    mocked_transaction_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    transaction = TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )

    mocked_is_active.return_value = True

    order_id = to_global_id_or_none(order)

    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_transaction_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.VOID,
            action_value=None,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_VOID_REQUESTED
    assert event.parameters["reference"] == transaction.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_order_void_with_transaction_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10.0"),
    )
    mocked_is_active.return_value = False

    order_id = to_global_id_or_none(order)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    assert data["errors"][0]["code"] == (
        OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called


ORDER_REFUND_MUTATION = """
    mutation refundOrder($id: ID!, $amount: PositiveDecimal!) {
        orderRefund(id: $id, amount: $amount) {
            order {
                paymentStatus
                paymentStatusDisplay
                isPaid
                status
            }
            errors {
                code
                field
            }
        }
    }
"""


def test_order_refund(staff_api_client, permission_manage_orders, payment_txn_captured):
    order = payment_txn_captured.order
    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_captured.total)
    variables = {"id": order_id, "amount": amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_REFUNDED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_REFUNDED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"] is False

    refund_order_event = order.events.filter(
        type=order_events.OrderEvents.PAYMENT_REFUNDED
    ).first()
    assert refund_order_event.parameters["amount"] == str(amount)

    refunded_fulfillment = order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED
    ).first()
    assert refunded_fulfillment
    assert refunded_fulfillment.total_refund_amount == payment_txn_captured.total
    assert refunded_fulfillment.shipping_refund_amount is None


def test_order_refund_with_gift_card_lines(
    staff_api_client, permission_manage_orders, gift_card_shippable_order_line
):
    order = gift_card_shippable_order_line.order
    query = ORDER_REFUND_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id, "amount": 10.0}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]
    assert not data["order"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert data["errors"][0]["field"] == "id"


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_action_request")
def test_order_refund_with_transaction_action_request(
    mocked_transaction_action_request,
    mocked_is_active,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    transaction = TransactionItem.objects.create(
        status="Captured",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )
    refund_value = Decimal(5.0)
    mocked_is_active.return_value = True

    order_id = to_global_id_or_none(order)
    variables = {"id": order_id, "amount": refund_value}

    # when
    response = staff_api_client.post_graphql(
        ORDER_REFUND_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]
    assert not data["errors"]

    assert mocked_is_active.called
    mocked_transaction_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=refund_value,
        ),
        channel_slug=order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == refund_value
    assert event.parameters["reference"] == transaction.reference


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_order_refund_with_transaction_action_request_missing_event(
    mocked_is_active, staff_api_client, permission_manage_orders, order
):
    # given
    authorized_value = Decimal("10")
    TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorized_value,
    )
    mocked_is_active.return_value = False

    order_id = to_global_id_or_none(order)
    variables = {"id": order_id, "amount": authorized_value}

    # when
    response = staff_api_client.post_graphql(
        ORDER_REFUND_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == (
        OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called


@pytest.mark.parametrize(
    "requires_amount, mutation_name",
    ((True, "orderRefund"), (False, "orderVoid"), (True, "orderCapture")),
)
def test_clean_payment_without_payment_associated_to_order(
    staff_api_client, permission_manage_orders, order, requires_amount, mutation_name
):

    assert not OrderEvent.objects.exists()

    additional_arguments = ", amount: 2" if requires_amount else ""
    query = """
        mutation %(mutationName)s($id: ID!) {
          %(mutationName)s(id: $id %(args)s) {
            errors {
              field
              message
            }
          }
        }
    """ % {
        "mutationName": mutation_name,
        "args": additional_arguments,
    }

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    errors = get_graphql_content(response)["data"][mutation_name].get("errors")

    message = "There's no payment associated with the order."

    assert errors, "expected an error"
    assert errors == [{"field": "payment", "message": message}]
    assert not OrderEvent.objects.exists()


def test_try_payment_action_generates_event(order, staff_user, payment_dummy):
    message = "The payment did a oopsie!"
    assert not OrderEvent.objects.exists()

    def _test_operation():
        raise PaymentError(message)

    with pytest.raises(ValidationError) as exc:
        try_payment_action(
            order=order,
            user=staff_user,
            app=None,
            payment=payment_dummy,
            func=_test_operation,
        )

    assert exc.value.args[0]["payment"].message == message

    error_event = OrderEvent.objects.get()  # type: OrderEvent
    assert error_event.type == order_events.OrderEvents.PAYMENT_FAILED
    assert error_event.user == staff_user
    assert not error_event.app
    assert error_event.parameters == {
        "message": message,
        "gateway": payment_dummy.gateway,
        "payment_id": payment_dummy.token,
    }


def test_try_payment_action_generates_app_event(order, app, payment_dummy):
    message = "The payment did a oopsie!"
    assert not OrderEvent.objects.exists()

    def _test_operation():
        raise PaymentError(message)

    with pytest.raises(ValidationError) as exc:
        try_payment_action(
            order=order, user=None, app=app, payment=payment_dummy, func=_test_operation
        )

    assert exc.value.args[0]["payment"].message == message

    error_event = OrderEvent.objects.get()  # type: OrderEvent
    assert error_event.type == order_events.OrderEvents.PAYMENT_FAILED
    assert not error_event.user
    assert error_event.app == app
    assert error_event.parameters == {
        "message": message,
        "gateway": payment_dummy.gateway,
        "payment_id": payment_dummy.token,
    }


def test_clean_order_refund_payment():
    payment = MagicMock(spec=Payment)
    payment.can_refund.return_value = False
    with pytest.raises(ValidationError) as e:
        clean_refund_payment(payment)
    assert e.value.error_dict["payment"][0].code == OrderErrorCode.CANNOT_REFUND


def test_clean_order_capture():
    with pytest.raises(ValidationError) as e:
        clean_order_capture(None)
    msg = "There's no payment associated with the order."
    assert e.value.error_dict["payment"][0].message == msg


@pytest.mark.parametrize(
    "status",
    [
        FulfillmentStatus.RETURNED,
        FulfillmentStatus.REFUNDED_AND_RETURNED,
        FulfillmentStatus.REFUNDED,
        FulfillmentStatus.CANCELED,
        FulfillmentStatus.REPLACED,
    ],
)
def test_clean_order_cancel(status, fulfillment):
    order = fulfillment.order
    fulfillment.status = status
    fulfillment.save()
    # Shouldn't raise any errors
    assert clean_order_cancel(order) is None


def test_clean_order_cancel_draft_order(
    fulfilled_order_with_all_cancelled_fulfillments,
):
    order = fulfilled_order_with_all_cancelled_fulfillments

    order.status = OrderStatus.DRAFT
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER


def test_clean_order_cancel_canceled_order(
    fulfilled_order_with_all_cancelled_fulfillments,
):
    order = fulfilled_order_with_all_cancelled_fulfillments

    order.status = OrderStatus.CANCELED
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER


def test_clean_order_cancel_order_with_fulfillment(
    fulfilled_order_with_cancelled_fulfillment,
):
    order = fulfilled_order_with_cancelled_fulfillment

    order.status = OrderStatus.CANCELED
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER


ORDER_UPDATE_SHIPPING_QUERY = """
    mutation orderUpdateShipping($order: ID!, $shippingMethod: ID) {
        orderUpdateShipping(
                order: $order, input: {shippingMethod: $shippingMethod}) {
            errors {
                field
                code
                message
            }
            order {
                id
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


@pytest.mark.parametrize("status", [OrderStatus.UNCONFIRMED, OrderStatus.DRAFT])
def test_order_update_shipping(
    status,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = status
    order.save()
    assert order.shipping_method != shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id

    order.refresh_from_db()
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    shipping_price = TaxedMoney(shipping_total, shipping_total)
    assert order.status == status
    assert order.shipping_method == shipping_method
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross
    assert order.shipping_tax_rate == Decimal("0.0")
    assert order.shipping_method_name == shipping_method.name


@pytest.mark.parametrize("status", [OrderStatus.UNCONFIRMED, OrderStatus.DRAFT])
def test_order_update_shipping_no_shipping_method_channel_listings(
    status,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = status
    order.save()
    assert order.shipping_method != shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    shipping_method.channel_listings.all().delete()
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert errors[0]["field"] == "shippingMethod"


def test_order_update_shipping_tax_included(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
    vatlayer,
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    address = order_with_lines.shipping_address
    address.country = "DE"
    address.save()

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id

    order.refresh_from_db()
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    shipping_price = TaxedMoney(
        shipping_total / Decimal("1.19"), shipping_total
    ).quantize()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.shipping_method == shipping_method
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross
    assert order.shipping_tax_rate == Decimal("0.19")
    assert order.shipping_method_name == shipping_method.name


def test_order_update_shipping_clear_shipping_method(
    staff_api_client, permission_manage_orders, order, staff_user, shipping_method
):
    order.shipping_method = shipping_method
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id,
    ).get_total()

    shipping_price = TaxedMoney(shipping_total, shipping_total)
    order.shipping_price = shipping_price
    order.shipping_method_name = "Example shipping"
    order.save()

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"order": order_id, "shippingMethod": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id

    order.refresh_from_db()
    assert order.shipping_method is None
    assert order.shipping_price == zero_taxed_money(order.currency)
    assert order.shipping_method_name is None


def test_order_update_shipping_shipping_required(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"order": order_id, "shippingMethod": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "shippingMethod"
    assert data["errors"][0]["message"] == (
        "Shipping method is required for this order."
    )


@pytest.mark.parametrize(
    "status",
    [
        OrderStatus.UNFULFILLED,
        OrderStatus.FULFILLED,
        OrderStatus.PARTIALLY_RETURNED,
        OrderStatus.RETURNED,
        OrderStatus.CANCELED,
    ],
)
def test_order_update_shipping_not_editable_order(
    status,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = status
    order.save()
    assert order.shipping_method != shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == OrderErrorCode.NOT_EDITABLE.name


def test_order_update_shipping_no_shipping_address(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    order.shipping_address = None
    order.save()
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "order"
    assert data["errors"][0]["message"] == (
        "Cannot choose a shipping method for an order without" " the shipping address."
    )


def test_order_update_shipping_incorrect_shipping_method(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    zone = shipping_method.shipping_zone
    zone.countries = ["DE"]
    zone.save()
    assert order.shipping_address.country.code not in zone.countries
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "shippingMethod"
    assert data["errors"][0]["message"] == (
        "Shipping method cannot be used with this order."
    )


def test_order_update_shipping_shipping_zone_without_channels(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    order.channel.shipping_zones.clear()
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name


def test_order_update_shipping_excluded_shipping_method_postal_code(
    staff_api_client,
    permission_manage_orders,
    order_unconfirmed,
    staff_user,
    shipping_method_excluded_by_postal_code,
):
    order = order_unconfirmed
    order.shipping_method = shipping_method_excluded_by_postal_code
    shipping_total = shipping_method_excluded_by_postal_code.channel_listings.get(
        channel_id=order.channel_id,
    ).get_total()

    shipping_price = TaxedMoney(shipping_total, shipping_total)
    order.shipping_price = shipping_price
    order.shipping_method_name = "Example shipping"
    order.save()

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method_excluded_by_postal_code.id
    )
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "shippingMethod"
    assert data["errors"][0]["message"] == (
        "Shipping method cannot be used with this order."
    )


def test_draft_order_clear_shipping_method(
    staff_api_client, draft_order, permission_manage_orders
):
    assert draft_order.shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", draft_order.id)
    variables = {"order": order_id, "shippingMethod": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id
    draft_order.refresh_from_db()
    assert draft_order.shipping_method is None
    assert draft_order.shipping_price == zero_taxed_money(draft_order.currency)
    assert draft_order.shipping_method_name is None


ORDER_BY_TOKEN_QUERY = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            id
            shippingAddress {
                firstName
                lastName
                streetAddress1
                streetAddress2
                phone
            }
            billingAddress {
                firstName
                lastName
                streetAddress1
                streetAddress2
                phone
            }
            userEmail
        }
    }
    """


def test_order_by_token_query_by_anonymous_user(api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.billing_address.street_address_2 = "test"
    order.billing_address.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_order_owner(user_api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY
    order.user = user_api_client.user
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = user_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_old_id_query_by_anonymous_user(api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    order.billing_address.street_address_2 = "test"
    order.billing_address.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id
    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name[
        0
    ] + "." * (len(order.shipping_address.first_name) - 1)
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name[
        0
    ] + "." * (len(order.shipping_address.last_name) - 1)
    assert data["shippingAddress"][
        "streetAddress1"
    ] == order.shipping_address.street_address_1[0] + "." * (
        len(order.shipping_address.street_address_1) - 1
    )
    assert data["shippingAddress"][
        "streetAddress2"
    ] == order.shipping_address.street_address_2[0] + "." * (
        len(order.shipping_address.street_address_2) - 1
    )
    assert data["shippingAddress"]["phone"] == str(order.shipping_address.phone)[
        :3
    ] + "." * (len(str(order.shipping_address.phone)) - 3)

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name[
        0
    ] + "." * (len(order.billing_address.first_name) - 1)
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name[
        0
    ] + "." * (len(order.billing_address.last_name) - 1)
    assert data["billingAddress"][
        "streetAddress1"
    ] == order.billing_address.street_address_1[0] + "." * (
        len(order.billing_address.street_address_1) - 1
    )
    assert data["billingAddress"][
        "streetAddress2"
    ] == order.billing_address.street_address_2[0] + "." * (
        len(order.billing_address.street_address_2) - 1
    )
    assert data["billingAddress"]["phone"] == str(order.billing_address.phone)[
        :3
    ] + "." * (len(str(order.billing_address.phone)) - 3)
    assert data["userEmail"] == obfuscate_email(order.user_email)


def test_order_by_token_query_by_superuser(superuser_api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = superuser_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_staff_with_permission(
    staff_api_client, permission_manage_orders, order, customer_user
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_orders)

    order.user = customer_user
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_staff_no_permission(
    staff_api_client, order, customer_user
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.shipping_address.street_address_2 = "test"
    order.shipping_address.save()

    order.user = customer_user
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.user = customer_user
    order.save()

    app_api_client.app.permissions.add(permission_manage_orders)

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = app_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_app_no_perm(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.user = customer_user
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = app_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_old_id_query_by_app_no_perm(app_api_client, order, customer_user):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    query = ORDER_BY_TOKEN_QUERY

    order.user = customer_user
    order.save()

    # when
    response = app_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == graphene.Node.to_global_id("Order", order.id)

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name[
        0
    ] + "." * (len(order.shipping_address.first_name) - 1)
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name[
        0
    ] + "." * (len(order.shipping_address.last_name) - 1)
    assert data["shippingAddress"][
        "streetAddress1"
    ] == order.shipping_address.street_address_1[0] + "." * (
        len(order.shipping_address.street_address_1) - 1
    )
    assert data["shippingAddress"]["streetAddress2"] == ""
    assert data["shippingAddress"]["phone"] == str(order.shipping_address.phone)[
        :3
    ] + "." * (len(str(order.shipping_address.phone)) - 3)

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name[
        0
    ] + "." * (len(order.billing_address.first_name) - 1)
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name[
        0
    ] + "." * (len(order.billing_address.last_name) - 1)
    assert data["billingAddress"][
        "streetAddress1"
    ] == order.billing_address.street_address_1[0] + "." * (
        len(order.billing_address.street_address_1) - 1
    )
    assert data["billingAddress"]["streetAddress2"] == ""
    assert data["billingAddress"]["phone"] == str(order.billing_address.phone)[
        :3
    ] + "." * (len(str(order.billing_address.phone)) - 3)


def test_order_by_token_user_restriction(api_client, order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            user {
                id
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"token": order.id})
    assert_no_permission(response)


def test_order_by_token_events_restriction(api_client, order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            events {
                id
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"token": order.id})
    assert_no_permission(response)


def test_authorized_access_to_order_by_token(
    user_api_client, staff_api_client, customer_user, order, permission_manage_users
):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            user {
                id
            }
        }
    }
    """
    variables = {"token": order.id}
    customer_user_id = graphene.Node.to_global_id("User", customer_user.id)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["orderByToken"]["user"]["id"] == customer_user_id

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    assert content["data"]["orderByToken"]["user"]["id"] == customer_user_id


def test_query_draft_order_by_token_with_requester_as_customer(
    user_api_client, draft_order
):
    draft_order.user = user_api_client.user
    draft_order.save(update_fields=["user"])
    query = ORDER_BY_TOKEN_QUERY
    response = user_api_client.post_graphql(query, {"token": draft_order.id})
    content = get_graphql_content(response)
    assert not content["data"]["orderByToken"]


def test_query_draft_order_by_token_as_anonymous_customer(api_client, draft_order):
    query = ORDER_BY_TOKEN_QUERY
    response = api_client.post_graphql(query, {"token": draft_order.id})
    content = get_graphql_content(response)
    assert not content["data"]["orderByToken"]


def test_query_order_without_addresses(order, user_api_client, channel_USD):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order = Order.objects.create(
        channel=channel_USD,
        user=user_api_client.user,
    )

    # when
    response = user_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["userEmail"] == user_api_client.user.email
    assert data["billingAddress"] is None
    assert data["shippingAddress"] is None


def test_order_query_address_without_order_user(
    staff_api_client, permission_manage_orders, channel_USD, address
):
    query = ORDER_BY_TOKEN_QUERY
    shipping_address = address.get_copy()
    billing_address = address.get_copy()
    order = Order.objects.create(
        channel=channel_USD,
        shipping_address=shipping_address,
        billing_address=billing_address,
    )
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, {"token": order.id})
    content = get_graphql_content(response)
    order = content["data"]["orderByToken"]
    assert order["shippingAddress"] is not None
    assert order["billingAddress"] is not None


QUERY_ORDER_LINE_STOCKS = """
query OrderQuery($id: ID!) {
    order(id: $id) {
        number
        lines {
            id
            quantity
            quantityFulfilled
            variant {
                id
                name
                sku
                stocks {
                    warehouse {
                        id
                        name
                    }
                }
            }
        }
    }
}
"""


def test_query_order_line_stocks(
    staff_api_client,
    permission_manage_orders,
    order_with_lines_for_cc,
    warehouse,
    warehouse_for_cc,
):
    """Ensure that stocks for normal and click and collect warehouses are returned."""
    # given
    order = order_with_lines_for_cc
    variant = order.lines.first().variant
    variables = {"id": graphene.Node.to_global_id("Order", order.id)}

    # create the variant stock for not click and collect warehouse
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_LINE_STOCKS, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data
    assert len(order_data["lines"]) == 1
    assert {
        stock["warehouse"]["name"]
        for stock in order_data["lines"][0]["variant"]["stocks"]
    } == {warehouse.name, warehouse_for_cc.name}


MUTATION_ORDER_BULK_CANCEL = """
mutation CancelManyOrders($ids: [ID!]!) {
    orderBulkCancel(ids: $ids) {
        count
        errors{
            field
            code
        }
    }
}
"""


@patch("saleor.graphql.order.bulk_mutations.orders.cancel_order")
def test_order_bulk_cancel(
    mock_cancel_order,
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
):
    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(order=order, user=staff_api_client.user, app=None, manager=ANY)
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    mock_cancel_order.call_count == expected_count


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_bulk_cancel_with_back_in_stock_webhook(
    product_variant_back_in_stock_webhook_mock,
    staff_api_client,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
):
    variables = {
        "ids": [
            graphene.Node.to_global_id(
                "Order", fulfilled_order_with_all_cancelled_fulfillments.id
            )
        ]
    }
    staff_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )

    product_variant_back_in_stock_webhook_mock.assert_called_once()


@patch("saleor.graphql.order.bulk_mutations.orders.cancel_order")
def test_order_bulk_cancel_as_app(
    mock_cancel_order,
    app_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
):
    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = app_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(order=order, user=AnonymousUser(), app=app_api_client.app, manager=ANY)
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    assert mock_cancel_order.call_count == expected_count


@patch("saleor.graphql.order.bulk_mutations.orders.cancel_order")
def test_order_bulk_cancel_without_sku(
    mock_cancel_order,
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
):
    ProductVariant.objects.update(sku=None)
    OrderLine.objects.update(product_sku=None)

    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_BULK_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["errors"]

    calls = [
        call(order=order, user=staff_api_client.user, app=None, manager=ANY)
        for order in orders
    ]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    mock_cancel_order.call_count == expected_count


def test_order_query_with_filter_channels_with_one_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    orders,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variables = {"filter": {"channels": [channel_id]}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 3


def test_order_query_with_filter_channels_without_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    orders,
):
    # given
    variables = {"filter": {"channels": []}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 5


def test_order_query_with_filter_channels_with_many_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    orders,
    channel_USD,
    channel_PLN,
    other_channel_USD,
):
    # given
    Order.objects.create(channel=other_channel_USD)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    variables = {"filter": {"channels": [channel_pln_id, channel_usd_id]}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 5
    assert Order.objects.non_draft().count() == 6


def test_order_query_with_filter_channels_with_empty_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    orders,
    other_channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", other_channel_USD.pk)
    variables = {"filter": {"channels": [channel_id]}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_query_with_filter_gift_card_used_true(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    gift_card,
    orders,
):
    # given
    gift_card_order = orders[0]
    gift_cards_used_in_order_event(
        [(gift_card, 20.0)], gift_card_order, staff_api_client.user, None
    )
    variables = {"filter": {"giftCardUsed": True}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert orders[0]["node"]["id"] == graphene.Node.to_global_id(
        "Order", gift_card_order.id
    )


def test_order_query_with_filter_gift_card_used_false(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    gift_card,
    orders,
):
    # given
    gift_card_order = orders[0]
    gift_card_order_id = graphene.Node.to_global_id("Order", gift_card_order.id)
    gift_cards_used_in_order_event(
        [(gift_card, 20.0)], gift_card_order, staff_api_client.user, None
    )
    variables = {"filter": {"giftCardUsed": False}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders_data = content["data"]["orders"]["edges"]
    assert gift_card_order_id not in {
        order_data["node"]["id"] for order_data in orders_data
    }


def test_order_query_with_filter_gift_card_bough_true(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    gift_card,
    orders,
):
    # given
    gift_card_order = orders[-1]
    gift_cards_bought_event([gift_card], gift_card_order, staff_api_client.user, None)
    variables = {"filter": {"giftCardBought": True}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert orders[0]["node"]["id"] == graphene.Node.to_global_id(
        "Order", gift_card_order.id
    )


def test_order_query_with_filter_gift_card_bought_false(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    gift_card,
    orders,
):
    # given
    gift_card_order = orders[-1]
    gift_card_order_id = graphene.Node.to_global_id("Order", gift_card_order.id)
    gift_cards_bought_event([gift_card], gift_card_order, staff_api_client.user, None)
    variables = {"filter": {"giftCardBought": False}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    orders_data = content["data"]["orders"]["edges"]
    assert gift_card_order_id not in {
        order_data["node"]["id"] for order_data in orders_data
    }


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            1,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"lte": str(date.today())}}, 2),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0),
    ],
)
def test_order_query_with_filter_created(
    orders_filter,
    count,
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    channel_USD,
):
    Order.objects.create(channel=channel_USD)
    with freeze_time("2012-01-14"):
        Order.objects.create(channel=channel_USD)
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        ({"updatedAt": {"gte": "2012-01-14T10:59:00+00:00"}}, 2),
        ({"updatedAt": {"lte": "2012-01-14T12:00:05+00:00"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T11:59:00+00:00"}}, 1),
        ({"updatedAt": {"lte": "2012-01-14T11:05:00+00:00"}}, 1),
        ({"updatedAt": {"gte": "2012-01-14T12:01:00+00:00"}}, 0),
        ({"updatedAt": {"lte": "2012-01-14T10:59:00+00:00"}}, 0),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:01:00+00:00",
                    "gte": "2012-01-14T11:59:00+00:00",
                },
            },
            1,
        ),
    ],
)
def test_order_query_with_filter_updated_at(
    orders_filter,
    count,
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    channel_USD,
):
    with freeze_time("2012-01-14 11:00:00"):
        Order.objects.create(channel=channel_USD)

    with freeze_time("2012-01-14 12:00:00"):
        Order.objects.create(channel=channel_USD)

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count, payment_status",
    [
        ({"paymentStatus": "FULLY_CHARGED"}, 1, ChargeStatus.FULLY_CHARGED),
        ({"paymentStatus": "NOT_CHARGED"}, 2, ChargeStatus.NOT_CHARGED),
        ({"paymentStatus": "PARTIALLY_CHARGED"}, 1, ChargeStatus.PARTIALLY_CHARGED),
        ({"paymentStatus": "PARTIALLY_REFUNDED"}, 1, ChargeStatus.PARTIALLY_REFUNDED),
        ({"paymentStatus": "FULLY_REFUNDED"}, 1, ChargeStatus.FULLY_REFUNDED),
        ({"paymentStatus": "FULLY_CHARGED"}, 0, ChargeStatus.FULLY_REFUNDED),
        ({"paymentStatus": "NOT_CHARGED"}, 1, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_order_query_with_filter_payment_status(
    orders_filter,
    count,
    payment_status,
    orders_query_with_filter,
    staff_api_client,
    payment_dummy,
    permission_manage_orders,
    channel_PLN,
):
    payment_dummy.charge_status = payment_status
    payment_dummy.save()

    payment_dummy.id = None
    payment_dummy.order = Order.objects.create(channel=channel_PLN)
    payment_dummy.charge_status = ChargeStatus.NOT_CHARGED
    payment_dummy.save()

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count, status",
    [
        ({"status": "UNFULFILLED"}, 2, OrderStatus.UNFULFILLED),
        ({"status": "UNCONFIRMED"}, 1, OrderStatus.UNCONFIRMED),
        ({"status": "PARTIALLY_FULFILLED"}, 1, OrderStatus.PARTIALLY_FULFILLED),
        ({"status": "FULFILLED"}, 1, OrderStatus.FULFILLED),
        ({"status": "CANCELED"}, 1, OrderStatus.CANCELED),
    ],
)
def test_order_query_with_filter_status(
    orders_filter,
    count,
    status,
    orders_query_with_filter,
    staff_api_client,
    payment_dummy,
    permission_manage_orders,
    order,
    channel_USD,
):
    order.status = status
    order.save()

    Order.objects.create(channel=channel_USD)

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    orders_ids_from_response = [o["node"]["id"] for o in orders]
    assert len(orders) == count
    assert order_id in orders_ids_from_response


@pytest.mark.parametrize(
    "orders_filter, user_field, user_value",
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_order_query_with_filter_customer_fields(
    orders_filter,
    user_field,
    user_value,
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(user=customer_user, channel=channel_USD)
    Order.objects.bulk_create([order, Order(channel=channel_USD)])

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


@pytest.mark.parametrize(
    "orders_filter, user_field, user_value",
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_draft_order_query_with_filter_customer_fields(
    orders_filter,
    user_field,
    user_value,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(
        status=OrderStatus.DRAFT,
        user=customer_user,
        channel=channel_USD,
    )
    Order.objects.bulk_create(
        [
            order,
            Order(status=OrderStatus.DRAFT, channel=channel_USD),
        ]
    )

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            1,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"lte": str(date.today())}}, 2),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0),
    ],
)
def test_draft_order_query_with_filter_created_(
    orders_filter,
    count,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    channel_USD,
):
    Order.objects.create(status=OrderStatus.DRAFT, channel=channel_USD)
    with freeze_time("2012-01-14"):
        Order.objects.create(status=OrderStatus.DRAFT, channel=channel_USD)
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]

    assert len(orders) == count


@pytest.fixture
def order_list_with_cc_orders(orders, warehouse_for_cc):
    order_1 = orders[0]
    order_1.collection_point = warehouse_for_cc
    order_1.collection_point_name = warehouse_for_cc.name

    order_2 = orders[1]
    order_2.collection_point_name = warehouse_for_cc.name

    order_3 = orders[2]
    order_3.collection_point = warehouse_for_cc

    cc_orders = [order_1, order_2, order_3]

    Order.objects.bulk_update(cc_orders, ["collection_point", "collection_point_name"])
    return orders


def test_order_query_with_filter_is_click_and_collect_true(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    order_list_with_cc_orders,
):
    # given
    orders = order_list_with_cc_orders
    variables = {"filter": {"isClickAndCollect": True}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    expected_orders = {
        order
        for order in orders
        if order.collection_point or order.collection_point_name
    }
    assert len(returned_orders) == len(expected_orders)
    assert {order["node"]["id"] for order in returned_orders} == {
        graphene.Node.to_global_id("Order", order.pk) for order in expected_orders
    }


def test_order_query_with_filter_is_click_and_collect_false(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    order_list_with_cc_orders,
):
    # given
    orders = order_list_with_cc_orders
    variables = {"filter": {"isClickAndCollect": False}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    expected_orders = {
        order
        for order in orders
        if not order.collection_point
        and not order.collection_point_name
        and order.status != OrderStatus.DRAFT
    }
    assert len(returned_orders) == len(expected_orders)
    assert {order["node"]["id"] for order in returned_orders} == {
        graphene.Node.to_global_id("Order", order.pk) for order in expected_orders
    }


@pytest.fixture
@freeze_time("2021-11-01 12:00:01")
def preorders(orders, product):
    variants = [
        ProductVariant(
            product=product,
            is_preorder=True,
            sku=f"Preorder product variant #{i}",
        )
        for i in (1, 2, 3, 4)
    ]
    variants[1].preorder_end_date = timezone.now() + timedelta(days=1)
    variants[2].preorder_end_date = timezone.now()
    variants[3].preorder_end_date = timezone.now() - timedelta(days=1)
    ProductVariant.objects.bulk_create(variants)

    lines = [
        OrderLine(
            order=order,
            product_name=str(product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            quantity=1,
            variant=variant,
            unit_price_net_amount=Decimal("10.0"),
            unit_price_gross_amount=Decimal("10.0"),
            currency="USD",
            total_price_net_amount=Decimal("10.0"),
            total_price_gross_amount=Decimal("10.0"),
            undiscounted_unit_price_net_amount=Decimal("10.0"),
            undiscounted_unit_price_gross_amount=Decimal("10.0"),
            undiscounted_total_price_net_amount=Decimal("10.0"),
            undiscounted_total_price_gross_amount=Decimal("10.0"),
        )
        for variant, order in zip(variants, orders)
    ]
    OrderLine.objects.bulk_create(lines)
    preorders = orders[: len(variants) - 1]
    return preorders


@freeze_time("2021-11-01 12:00:01")
def test_order_query_with_filter_is_preorder_true(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    preorders,
):
    # given
    variables = {"filter": {"isPreorder": True}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    assert len(returned_orders) == len(preorders)
    assert {order["node"]["id"] for order in returned_orders} == {
        graphene.Node.to_global_id("Order", order.pk) for order in preorders
    }


@freeze_time("2021-11-01 12:00:01")
def test_order_query_with_filter_is_preorder_false(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    preorders,
):
    # given
    variables = {"filter": {"isPreorder": False}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    preorders_ids = {
        graphene.Node.to_global_id("Order", order.pk) for order in preorders
    }
    preorder_ids = {order["node"]["id"] for order in returned_orders}
    for order_id in preorders_ids:
        assert order_id not in preorder_ids


QUERY_ORDER_WITH_SORT = """
    query ($sort_by: OrderSortingInput!) {
        orders(first:5, sortBy: $sort_by) {
            edges{
                node{
                    number
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "order_sort, result_order",
    [
        ({"field": "NUMBER", "direction": "ASC"}, [0, 1, 2, 3]),
        ({"field": "NUMBER", "direction": "DESC"}, [3, 2, 1, 0]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0, 2, 3]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [3, 2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0, 1, 3]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [3, 1, 0, 2]),
        ({"field": "FULFILLMENT_STATUS", "direction": "ASC"}, [2, 1, 0, 3]),
        ({"field": "FULFILLMENT_STATUS", "direction": "DESC"}, [3, 0, 1, 2]),
    ],
)
def test_query_orders_with_sort(
    order_sort,
    result_order,
    staff_api_client,
    permission_manage_orders,
    address,
    channel_USD,
):
    created_orders = []
    with freeze_time("2017-01-14"):
        created_orders.append(
            Order.objects.create(
                billing_address=address,
                status=OrderStatus.PARTIALLY_FULFILLED,
                total=TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD")),
                channel=channel_USD,
            )
        )
    with freeze_time("2012-01-14"):
        address2 = address.get_copy()
        address2.first_name = "Walter"
        address2.save()
        created_orders.append(
            Order.objects.create(
                billing_address=address2,
                status=OrderStatus.FULFILLED,
                total=TaxedMoney(net=Money(100, "USD"), gross=Money(130, "USD")),
                channel=channel_USD,
            )
        )
    address3 = address.get_copy()
    address3.last_name = "Alice"
    address3.save()
    created_orders.append(
        Order.objects.create(
            billing_address=address3,
            status=OrderStatus.CANCELED,
            total=TaxedMoney(net=Money(20, "USD"), gross=Money(26, "USD")),
            channel=channel_USD,
        )
    )
    created_orders.append(
        Order.objects.create(
            billing_address=None,
            status=OrderStatus.UNCONFIRMED,
            total=TaxedMoney(net=Money(60, "USD"), gross=Money(80, "USD")),
            channel=channel_USD,
        )
    )
    variables = {"sort_by": order_sort}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDER_WITH_SORT, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    for order, order_number in enumerate(result_order):
        assert orders[order]["node"]["number"] == str(
            created_orders[order_number].number
        )


QUERY_DRAFT_ORDER_WITH_SORT = """
    query ($sort_by: OrderSortingInput!) {
        draftOrders(first:5, sortBy: $sort_by) {
            edges{
                node{
                    number
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "draft_order_sort, result_order",
    [
        ({"field": "NUMBER", "direction": "ASC"}, [0, 1, 2]),
        ({"field": "NUMBER", "direction": "DESC"}, [2, 1, 0]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0, 2]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [1, 0, 2]),
    ],
)
def test_query_draft_orders_with_sort(
    draft_order_sort,
    result_order,
    staff_api_client,
    permission_manage_orders,
    address,
    channel_USD,
):
    created_orders = []
    with freeze_time("2017-01-14"):
        created_orders.append(
            Order.objects.create(
                billing_address=address,
                status=OrderStatus.DRAFT,
                total=TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD")),
                channel=channel_USD,
            )
        )
    with freeze_time("2012-01-14"):
        address2 = address.get_copy()
        address2.first_name = "Walter"
        address2.save()
        created_orders.append(
            Order.objects.create(
                billing_address=address2,
                status=OrderStatus.DRAFT,
                total=TaxedMoney(net=Money(100, "USD"), gross=Money(130, "USD")),
                channel=channel_USD,
            )
        )
    address3 = address.get_copy()
    address3.last_name = "Alice"
    address3.save()
    created_orders.append(
        Order.objects.create(
            billing_address=address3,
            status=OrderStatus.DRAFT,
            total=TaxedMoney(net=Money(20, "USD"), gross=Money(26, "USD")),
            channel=channel_USD,
        )
    )
    variables = {"sort_by": draft_order_sort}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_DRAFT_ORDER_WITH_SORT, variables)
    content = get_graphql_content(response)
    draft_orders = content["data"]["draftOrders"]["edges"]

    for order, order_number in enumerate(result_order):
        assert draft_orders[order]["node"]["number"] == str(
            created_orders[order_number].number
        )


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        ({"search": "discount name"}, 2),
        ({"search": "Some other"}, 1),
        ({"search": "translated"}, 1),
        ({"search": "test@mirumee.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 3),
        ({"search": "ExternalID"}, 1),
        ({"search": "SKU_A"}, 1),
    ],
)
def test_orders_query_with_filter_search(
    orders_filter,
    count,
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
    product,
    variant,
):
    orders = Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                user_email="test@mirumee.com",
                channel=channel_USD,
            ),
            Order(
                user_email="user_email1@example.com",
                channel=channel_USD,
            ),
            Order(
                user_email="user_email2@example.com",
                channel=channel_USD,
            ),
        ]
    )

    OrderDiscount.objects.bulk_create(
        [
            OrderDiscount(
                order=orders[0],
                name="Some discount name",
                value=Decimal("1"),
                amount_value=Decimal("1"),
                translated_name="translated",
            ),
            OrderDiscount(
                order=orders[2],
                name="Some other discount name",
                value=Decimal("10"),
                amount_value=Decimal("10"),
                translated_name="PL_name",
            ),
        ]
    )
    order_with_payment = orders[1]
    payment = Payment.objects.create(
        order=order_with_payment, psp_reference="ExternalID"
    )
    payment.transactions.create(gateway_response={}, is_success=True)

    order_with_orderline = orders[2]
    channel = order_with_orderline.channel
    channel_listening = variant.channel_listings.get(channel=channel)
    net = variant.get_price(product, [], channel, channel_listening)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    order_with_orderline.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=3,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * 3,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * 3,
        tax_rate=Decimal("0.23"),
    )
    for order in orders:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(orders, ["search_vector"])

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == count


def test_orders_query_with_filter_search_by_global_payment_id(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    orders = Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                channel=channel_USD,
                user_email="test@example.com",
            ),
            Order(
                channel=channel_USD,
                user_email="user1@example.com",
            ),
        ]
    )
    OrderDiscount.objects.create(
        order=orders[0],
        name="test_discount1",
        value=Decimal("1"),
        amount_value=Decimal("1"),
        translated_name="translated_discount1_name",
    ),

    order_with_payment = orders[0]
    payment = Payment.objects.create(order=order_with_payment)
    global_id = graphene.Node.to_global_id("Payment", payment.pk)
    for order in orders:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(orders, ["search_vector"])

    variables = {"filter": {"search": global_id}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_query_with_filter_search_by_number(
    orders_query_with_filter,
    order_with_search_vector_value,
    staff_api_client,
    permission_manage_orders,
):
    order = order_with_search_vector_value
    variables = {"filter": {"search": order.number}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_query_with_filter_search_by_number_with_hash(
    orders_query_with_filter,
    order_with_search_vector_value,
    staff_api_client,
    permission_manage_orders,
):
    order = order_with_search_vector_value
    variables = {"filter": {"search": f"#{order.number}"}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_query_with_filter_search_by_product_sku_with_multiple_identic_sku(
    orders_query_with_filter, staff_api_client, permission_manage_orders, allocations
):
    variables = {"filter": {"search": allocations[0].order_line.product_sku}}
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 3


def test_order_query_with_filter_search_by_product_sku_order_line(
    orders_query_with_filter, staff_api_client, permission_manage_orders, order_line
):
    query = """
      query ($filter: OrderFilterInput!, ) {
        orders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
              lines{
                   productSku
              }
            }
          }
        }
      }
    """
    order = order_line.order
    order.refresh_from_db()
    update_order_search_vector(order)

    variables = {"filter": {"search": order_line.product_sku}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"][0]
    lines = orders["node"]["lines"][0]["productSku"]
    assert content["data"]["orders"]["totalCount"] == 1
    assert order_line.product_sku in lines


def test_orders_query_with_filter_by_orders_id(
    orders_query_with_filter,
    staff_api_client,
    order,
    permission_manage_orders,
    channel_USD,
):

    # given
    orders = Order.objects.bulk_create(
        [
            Order(
                user_email="test@mirumee.com",
                status=OrderStatus.UNFULFILLED,
                channel=channel_USD,
            ),
            Order(
                user_email="user_email1@example.com",
                status=OrderStatus.FULFILLED,
                channel=channel_USD,
            ),
        ]
    )
    orders_ids = [graphene.Node.to_global_id("Order", order.pk) for order in orders]
    variables = {"filter": {"ids": orders_ids}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)
    edges = content["data"]["orders"]["edges"]
    response_ids = [edge["node"]["id"] for edge in edges]

    # then
    assert content["data"]["orders"]["totalCount"] == 2
    assert all(ids in response_ids for ids in orders_ids)


def test_orders_query_with_filter_by_old_orders_id(
    orders_query_with_filter,
    staff_api_client,
    order,
    permission_manage_orders,
    channel_USD,
):

    # given
    orders = Order.objects.bulk_create(
        [
            Order(
                user_email="test@mirumee.com",
                status=OrderStatus.UNFULFILLED,
                channel=channel_USD,
                use_old_id=True,
            ),
            Order(
                user_email="user_email1@example.com",
                status=OrderStatus.FULFILLED,
                channel=channel_USD,
                use_old_id=False,
            ),
        ]
    )
    orders_ids = [graphene.Node.to_global_id("Order", order.number) for order in orders]
    variables = {"filter": {"ids": orders_ids}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)
    edges = content["data"]["orders"]["edges"]
    response_ids = [edge["node"]["id"] for edge in edges]

    # then
    assert content["data"]["orders"]["totalCount"] == 1
    assert response_ids == [graphene.Node.to_global_id("Order", orders[0].pk)]


def test_orders_query_with_filter_by_old_and_new_orders_id(
    orders_query_with_filter,
    staff_api_client,
    order,
    permission_manage_orders,
    channel_USD,
):

    # given
    orders = Order.objects.bulk_create(
        [
            Order(
                user_email="test@mirumee.com",
                status=OrderStatus.UNFULFILLED,
                channel=channel_USD,
                use_old_id=True,
            ),
            Order(
                user_email="user_email1@example.com",
                status=OrderStatus.FULFILLED,
                channel=channel_USD,
            ),
        ]
    )
    orders_ids = [
        graphene.Node.to_global_id("Order", orders[0].number),
        graphene.Node.to_global_id("Order", orders[1].pk),
    ]
    variables = {"filter": {"ids": orders_ids}}

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)
    edges = content["data"]["orders"]["edges"]
    response_ids = [edge["node"]["id"] for edge in edges]

    # then
    assert content["data"]["orders"]["totalCount"] == 2
    assert set(response_ids) == {
        graphene.Node.to_global_id("Order", order.pk) for order in orders
    }


def test_order_query_with_filter_search_by_product_sku_multi_order_lines(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    product,
    channel_USD,
    order,
):
    variants = ProductVariant.objects.bulk_create(
        [
            ProductVariant(product=product, sku="Var1"),
            ProductVariant(product=product, sku="Var2"),
        ]
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_USD,
                price_amount=Decimal(10),
                cost_price_amount=Decimal(1),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_USD,
                price_amount=Decimal(10),
                cost_price_amount=Decimal(1),
                currency=channel_USD.currency_code,
            ),
        ]
    )
    product = product
    channel = order.channel
    channel_listening = variants[0].channel_listings.get(channel=channel)
    net = variants[0].get_price(product, [], channel, channel_listening)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)

    lines = order.lines.bulk_create(
        [
            OrderLine(
                order_id=order.id,
                product_name=str(product),
                variant_name=str(variants[0]),
                product_sku=variants[0].sku,
                product_variant_id=variants[0].get_global_id(),
                is_shipping_required=variants[0].is_shipping_required(),
                is_gift_card=variants[0].is_gift_card(),
                quantity=quantity,
                variant=variants[0],
                unit_price=unit_price,
                total_price=unit_price * quantity,
                undiscounted_unit_price=unit_price,
                undiscounted_total_price=unit_price * quantity,
                tax_rate=Decimal("0.23"),
            ),
            OrderLine(
                order_id=order.id,
                product_name=str(product),
                variant_name=str(variants[1]),
                product_sku=variants[1].sku,
                product_variant_id=variants[1].get_global_id(),
                is_shipping_required=variants[1].is_shipping_required(),
                is_gift_card=variants[1].is_gift_card(),
                quantity=quantity,
                variant=variants[1],
                unit_price=unit_price,
                total_price=unit_price * quantity,
                undiscounted_unit_price=unit_price,
                undiscounted_total_price=unit_price * quantity,
                tax_rate=Decimal("0.23"),
            ),
        ]
    )
    order.refresh_from_db()
    update_order_search_vector(order)

    variables = {"filter": {"search": lines[0].product_sku}}
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


@pytest.mark.parametrize(
    "draft_orders_filter, count",
    [
        ({"search": "discount name"}, 2),
        ({"search": "Some other"}, 1),
        ({"search": "translated"}, 1),
        ({"search": "test@mirumee.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "leslie wade"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 3),
    ],
)
def test_draft_orders_query_with_filter_search(
    draft_orders_filter,
    count,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    orders = Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                user_email="test@mirumee.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                user_email="user_email1@example.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                user_email="user_email2@example.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
        ]
    )
    OrderDiscount.objects.bulk_create(
        [
            OrderDiscount(
                order=orders[0],
                name="Some discount name",
                value=Decimal("1"),
                amount_value=Decimal("1"),
                translated_name="translated",
            ),
            OrderDiscount(
                order=orders[2],
                name="Some other discount name",
                value=Decimal("10"),
                amount_value=Decimal("10"),
                translated_name="PL_name",
            ),
        ]
    )
    for order in orders:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(orders, ["search_vector"])

    variables = {"filter": draft_orders_filter}

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == count


def test_draft_orders_query_with_filter_search_by_number(
    draft_orders_query_with_filter,
    draft_order,
    staff_api_client,
    permission_manage_orders,
):
    update_order_search_vector(draft_order)
    variables = {"filter": {"search": draft_order.number}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == 1


def test_draft_orders_query_with_filter_search_by_number_with_hash(
    draft_orders_query_with_filter,
    draft_order,
    staff_api_client,
    permission_manage_orders,
):
    update_order_search_vector(draft_order)
    variables = {"filter": {"search": f"#{draft_order.number}"}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == 1


@pytest.mark.parametrize(
    "transaction_data, statuses, expected_count",
    [
        (
            {"authorized_value": Decimal("10")},
            [OrderAuthorizeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"authorized_value": Decimal("00")},
            [OrderAuthorizeStatusEnum.PARTIAL.name],
            0,
        ),
        (
            {"authorized_value": Decimal("100")},
            [OrderAuthorizeStatusEnum.FULL.name],
            2,
        ),
        (
            {"authorized_value": Decimal("10")},
            [OrderAuthorizeStatusEnum.FULL.name, OrderAuthorizeStatusEnum.PARTIAL.name],
            2,
        ),
        (
            {"authorized_value": Decimal("0")},
            [OrderAuthorizeStatusEnum.FULL.name, OrderAuthorizeStatusEnum.NONE.name],
            2,
        ),
        (
            {"authorized_value": Decimal("10"), "charged_value": Decimal("90")},
            [OrderAuthorizeStatusEnum.FULL.name],
            2,
        ),
    ],
)
def test_orders_query_with_filter_authorize_status(
    transaction_data,
    statuses,
    expected_count,
    orders_query_with_filter,
    order_with_lines,
    order,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    # given
    address = customer_user.default_billing_address.get_copy()
    order = Order.objects.create(
        billing_address=address,
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
        origin=OrderOrigin.CHECKOUT,
    )
    order.payment_transactions.create(
        currency=order.currency, authorized_value=Decimal("10")
    )
    update_order_charge_data(order)
    update_order_authorize_data(order)

    order_with_lines.payment_transactions.create(
        currency=order.currency, **transaction_data
    )
    update_order_charge_data(order_with_lines)
    update_order_authorize_data(order_with_lines)

    variables = {"filter": {"authorizeStatus": statuses}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == expected_count


@pytest.mark.parametrize(
    "transaction_data, statuses, expected_count",
    [
        (
            {"charged_value": Decimal("10")},
            [OrderChargeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"charged_value": Decimal("00")},
            [OrderChargeStatusEnum.PARTIAL.name],
            0,
        ),
        (
            {"charged_value": Decimal("98.40")},
            [OrderChargeStatusEnum.FULL.name],
            1,
        ),
        (
            {"charged_value": Decimal("10")},
            [OrderChargeStatusEnum.FULL.name, OrderChargeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"charged_value": Decimal("0")},
            [OrderChargeStatusEnum.FULL.name, OrderChargeStatusEnum.NONE.name],
            1,
        ),
        (
            {"charged_value": Decimal("98.40")},
            [OrderChargeStatusEnum.FULL.name, OrderChargeStatusEnum.OVERCHARGED.name],
            2,
        ),
    ],
)
def test_orders_query_with_filter_charge_status(
    transaction_data,
    statuses,
    expected_count,
    orders_query_with_filter,
    order_with_lines,
    order,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    # given
    address = customer_user.default_billing_address.get_copy()
    order = Order.objects.create(
        billing_address=address,
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
        origin=OrderOrigin.CHECKOUT,
    )
    order.payment_transactions.create(
        currency=order.currency, charged_value=Decimal("10")
    )
    update_order_charge_data(order)

    order_with_lines.payment_transactions.create(
        currency=order.currency, **transaction_data
    )
    update_order_charge_data(order_with_lines)

    variables = {"filter": {"chargeStatus": statuses}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == expected_count


def test_order_query_with_filter_numbers(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    orders,
    channel_USD,
):
    # given
    variables = {
        "filter": {
            "numbers": [str(orders[0].number), str(orders[2].number)],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"]
    assert len(order_data) == 2
    for order in [
        {"node": {"id": graphene.Node.to_global_id("Order", orders[0].id)}},
        {"node": {"id": graphene.Node.to_global_id("Order", orders[2].id)}},
    ]:
        assert order in order_data


def test_order_query_with_filter_not_allow_numbers_and_ids_together(
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    orders,
    channel_USD,
):
    # given
    variables = {
        "filter": {
            "numbers": [str(orders[0].number), str(orders[2].number)],
            "ids": [graphene.Node.to_global_id("Order", orders[1].id)],
        },
    }
    error_message = "'ids' and 'numbers` are not allowed to use together in filter."

    # when
    response = staff_api_client.post_graphql(
        orders_query_with_filter, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content_from_response(response)

    # then
    assert content["errors"][0]["message"] == error_message
    assert not content["data"]["orders"]


QUERY_GET_VARIANTS_FROM_ORDER = """
{
  me{
    orders(first:10){
      edges{
        node{
          lines{
            variant{
              id
            }
          }
        }
      }
    }
  }
}
"""


def test_get_variant_from_order_line_variant_published_as_customer(
    user_api_client, order_line
):
    # given

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_published_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_published_as_customer(
    user_api_client, order_line
):
    # given
    product = order_line.variant.product
    product.channel_listings.update(is_published=False)

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None


def test_get_variant_from_order_line_variant_not_published_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    product = order_line.variant.product
    product.channel_listings.update(is_published=False)

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_assigned_to_channel_as_customer(
    user_api_client, order_line
):
    # given
    product = order_line.variant.product
    product.channel_listings.all().delete()

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None


def test_get_variant_from_order_line_variant_not_assigned_to_channel_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    product = order_line.variant.product
    product.channel_listings.all().delete()

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_visible_in_listings_as_customer(
    user_api_client, order_line
):
    # given
    product = order_line.variant.product
    product.channel_listings.update(visible_in_listings=False)

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_visible_in_listings_as_admin(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    product = order_line.variant.product
    product.channel_listings.update(visible_in_listings=False)

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"]["id"]


def test_get_variant_from_order_line_variant_not_exists_as_customer(
    user_api_client, order_line
):
    # given
    order_line.variant = None
    order_line.save()

    # when
    response = user_api_client.post_graphql(QUERY_GET_VARIANTS_FROM_ORDER, {})

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None


def test_get_variant_from_order_line_variant_not_exists_as_staff(
    staff_api_client, order_line, permission_manage_products
):
    # given
    order = order_line.order
    order.user = staff_api_client.user
    order.save()
    order_line.variant = None
    order_line.save()

    # when
    response = staff_api_client.post_graphql(
        QUERY_GET_VARIANTS_FROM_ORDER,
        {},
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    orders = content["data"]["me"]["orders"]["edges"]
    assert orders[0]["node"]["lines"][0]["variant"] is None


def test_draft_order_properly_recalculate_total_after_shipping_product_removed(
    staff_api_client,
    draft_order,
    permission_manage_orders,
):
    order = draft_order
    line = order.lines.get(product_sku="SKU_AA")
    line.is_shipping_required = True
    line.save()

    query = ORDER_LINE_DELETE_MUTATION
    line_2 = order.lines.get(product_sku="SKU_B")
    line_2_id = graphene.Node.to_global_id("OrderLine", line_2.id)
    variables = {"id": line_2_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]

    order.refresh_from_db()
    assert data["order"]["total"]["net"]["amount"] == float(
        line.total_price_net_amount
    ) + float(order.shipping_price_net_amount)


ORDER_UPDATE_SHIPPING_QUERY_WITH_TOTAL = """
mutation OrderUpdateShipping(
    $orderId: ID!
    $shippingMethod: OrderUpdateShippingInput!
) {
    orderUpdateShipping(order: $orderId, input: $shippingMethod) {
        order {
            shippingMethod {
                id
            }
        }
        errors {
            field
            message
        }
    }
}
"""


@pytest.mark.parametrize(
    "input, response_msg",
    [
        ({"shippingMethod": ""}, "Shipping method cannot be empty."),
        ({}, "Shipping method must be provided to perform mutation."),
    ],
)
def test_order_shipping_update_mutation_return_error_for_empty_value(
    draft_order, permission_manage_orders, staff_api_client, input, response_msg
):
    query = ORDER_UPDATE_SHIPPING_QUERY_WITH_TOTAL

    order = draft_order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"orderId": order_id, "shippingMethod": input}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=(permission_manage_orders,),
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]

    assert data["errors"][0]["message"] == response_msg


def test_order_shipping_update_mutation_properly_recalculate_total(
    draft_order,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_UPDATE_SHIPPING_QUERY_WITH_TOTAL

    order = draft_order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"orderId": order_id, "shippingMethod": {"shippingMethod": None}}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=(permission_manage_orders,),
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["shippingMethod"] is None


QUERY_ORDER_BY_TOKEN_WITH_PAYMENT = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token){
            id
            payments{
              id
              gateway
              isActive
              created
              modified
              paymentMethodType
              transactions{
                gatewayResponse

              }
              actions
              capturedAmount{
                amount
              }
              availableCaptureAmount{
                amount
              }
              availableRefundAmount{
                amount
              }

              creditCard{
                brand
                firstDigits
                lastDigits
                expMonth
                expYear
              }
            }
        }
  }
"""

QUERY_ORDER_WITH_PAYMENT_AVAILABLE_FIELDS = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token){
            id
            payments{
              id
              gateway
              isActive
              created
              modified
              paymentMethodType
              capturedAmount{
                amount
              }
              chargeStatus
              creditCard{
                brand
                firstDigits
                lastDigits
                expMonth
                expYear
              }
            }
        }
  }
"""


def test_order_by_token_query_for_payment_details_without_permissions(
    api_client, payment_txn_captured
):
    response = api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_WITH_PAYMENT, {"token": payment_txn_captured.order.id}
    )
    assert_no_permission(response)


def test_order_by_token_query_for_payment_details_with_permissions(
    staff_api_client, payment_txn_captured, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_WITH_PAYMENT,
        {"token": payment_txn_captured.order.id},
    )

    content = get_graphql_content(response)

    assert_order_and_payment_ids(content, payment_txn_captured)


def test_order_by_token_query_payment_details_available_fields_without_permissions(
    api_client, payment_txn_captured
):
    response = api_client.post_graphql(
        QUERY_ORDER_WITH_PAYMENT_AVAILABLE_FIELDS,
        {"token": payment_txn_captured.order.id},
    )

    content = get_graphql_content(response)

    assert_order_and_payment_ids(content, payment_txn_captured)


def test_order_by_token_query_payment_details_available_fields_with_permissions(
    staff_api_client, payment_txn_captured, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_ORDER_WITH_PAYMENT_AVAILABLE_FIELDS,
        {"token": payment_txn_captured.order.id},
    )

    content = get_graphql_content(response)

    assert_order_and_payment_ids(content, payment_txn_captured)


SEARCH_ORDERS_QUERY = """
    query Orders(
        $filters: OrderFilterInput,
        $sortBy: OrderSortingInput,
        $after: String,
    ) {
        orders(
            first: 5,
            filter: $filters,
            sortBy: $sortBy,
            after: $after,
        ) {
            edges {
                node {
                    id
                }
                cursor
            }
        }
    }
"""


def test_sort_order_by_rank_without_search(staff_api_client, permission_manage_orders):
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    variables = {
        "sortBy": {"field": "RANK", "direction": "DESC"},
    }
    response = staff_api_client.post_graphql(SEARCH_ORDERS_QUERY, variables)
    content = get_graphql_content(response, ignore_errors=True)

    assert "errors" in content
    assert (
        content["errors"][0]["message"]
        == "Sorting by RANK is available only when using a search filter."
    )


@pytest.mark.parametrize(
    "fun_to_patch, price_name",
    [
        ("order_total", "total"),
        ("order_undiscounted_total", "undiscountedTotal"),
        ("order_shipping", "shippingPrice"),
    ],
)
def test_order_resolver_tax_recalculation(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    fun_to_patch,
    price_name,
):
    # given
    price = TaxedMoney(
        net=Money(amount="1234.56", currency="USD"),
        gross=Money(amount="1267.89", currency="USD"),
    )
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    query = (
        """
    query OrderPrices($id: ID!) {
        order(id: $id) {
            %s { net { amount } gross { amount } }
        }
    }
    """
        % price_name
    )
    variables = {"id": order_id}

    # when
    with patch(
        f"saleor.order.calculations.{fun_to_patch}", new=Mock(return_value=price)
    ):
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        data = content["data"]["order"]

    # then
    assert str(data[price_name]["net"]["amount"]) == str(price.net.amount)
    assert str(data[price_name]["gross"]["amount"]) == str(price.gross.amount)


ORDER_LINE_PRICE_DATA = OrderTaxedPricesData(
    price_with_discounts=TaxedMoney(
        net=Money(amount="1234.56", currency="USD"),
        gross=Money(amount="1267.89", currency="USD"),
    ),
    undiscounted_price=TaxedMoney(
        net=Money(amount="7234.56", currency="USD"),
        gross=Money(amount="7267.89", currency="USD"),
    ),
)


@pytest.mark.parametrize(
    "fun_to_patch, price_name, expected_price",
    [
        ("order_line_unit", "unitPrice", ORDER_LINE_PRICE_DATA.price_with_discounts),
        (
            "order_line_unit",
            "undiscountedUnitPrice",
            ORDER_LINE_PRICE_DATA.undiscounted_price,
        ),
        ("order_line_total", "totalPrice", ORDER_LINE_PRICE_DATA.price_with_discounts),
    ],
)
def test_order_line_resolver_tax_recalculation(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    fun_to_patch,
    price_name,
    expected_price,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save()

    order.lines.last().delete()

    order_id = graphene.Node.to_global_id("Order", order.id)

    query = (
        """
    query OrderLinePrices($id: ID!) {
        order(id: $id) {
            lines {
                %s { net { amount } gross { amount } }
            }
        }
    }
    """
        % price_name
    )
    variables = {"id": order_id}

    # when
    with patch(
        f"saleor.order.calculations.{fun_to_patch}",
        new=Mock(return_value=ORDER_LINE_PRICE_DATA),
    ):
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        data = content["data"]["order"]["lines"][0]

    # then
    assert str(data[price_name]["net"]["amount"]) == str(expected_price.net.amount)
    assert str(data[price_name]["gross"]["amount"]) == str(expected_price.gross.amount)


ORDER_SHIPPING_TAX_RATE_QUERY = """
query OrderShippingTaxRate($id: ID!) {
    order(id: $id) {
        shippingTaxRate
    }
}
"""


ORDER_LINE_TAX_RATE_QUERY = """
query OrderLineTaxRate($id: ID!) {
    order(id: $id) {
        lines {
            taxRate
        }
    }
}
"""


@pytest.mark.parametrize(
    "query, fun_to_patch, path",
    [
        (ORDER_SHIPPING_TAX_RATE_QUERY, "order_shipping_tax_rate", ["shippingTaxRate"]),
        (ORDER_LINE_TAX_RATE_QUERY, "order_line_tax_rate", ["lines", 0, "taxRate"]),
    ],
)
def test_order_tax_rate_resolver_tax_recalculation(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    query,
    fun_to_patch,
    path,
):
    # given
    tax_rate = Decimal("0.01")
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save()

    order.lines.last().delete()

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id}

    # when
    with patch(
        f"saleor.order.calculations.{fun_to_patch}", new=Mock(return_value=tax_rate)
    ):
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        data = content["data"]["order"]

    # then
    assert str(reduce(getitem, path, data)) == str(tax_rate)
