from datetime import date, timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time
from prices import Money, TaxedMoney

from .....core.postgres import FlatConcatSearchVector
from .....discount.models import OrderDiscount
from .....giftcard.events import gift_cards_bought_event, gift_cards_used_in_order_event
from .....order import OrderOrigin, OrderStatus
from .....order.models import Order, OrderLine
from .....order.search import (
    prepare_order_search_vector_value,
    update_order_search_vector,
)
from .....order.utils import update_order_authorize_data, update_order_charge_data
from .....payment import ChargeStatus
from .....payment.models import Payment
from .....product.models import ProductVariant, ProductVariantChannelListing
from ....order.enums import OrderAuthorizeStatusEnum, OrderChargeStatusEnum
from ....tests.utils import get_graphql_content, get_graphql_content_from_response


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


def test_order_query_with_filter_channels_with_one_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    orders,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variables = {"filter": {"channels": [channel_id]}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 3


def test_order_query_with_filter_channels_without_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    orders,
):
    # given
    variables = {"filter": {"channels": []}}

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 5


def test_order_query_with_filter_channels_with_many_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
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

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 5
    assert Order.objects.non_draft().count() == 6


def test_order_query_with_filter_channels_with_empty_channel(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    orders,
    other_channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", other_channel_USD.pk)
    variables = {"filter": {"channels": [channel_id]}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_query_with_filter_gift_card_used_true(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[0]
    gift_cards_used_in_order_event(
        [(gift_card, 20.0)], gift_card_order, staff_api_client.user, None
    )
    variables = {"filter": {"giftCardUsed": True}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

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
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[0]
    gift_card_order_id = graphene.Node.to_global_id("Order", gift_card_order.id)
    gift_cards_used_in_order_event(
        [(gift_card, 20.0)], gift_card_order, staff_api_client.user, None
    )
    variables = {"filter": {"giftCardUsed": False}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    orders_data = content["data"]["orders"]["edges"]
    assert gift_card_order_id not in {
        order_data["node"]["id"] for order_data in orders_data
    }


def test_order_query_with_filter_gift_card_bough_true(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[-1]
    gift_cards_bought_event([gift_card], gift_card_order, staff_api_client.user, None)
    variables = {"filter": {"giftCardBought": True}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

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
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[-1]
    gift_card_order_id = graphene.Node.to_global_id("Order", gift_card_order.id)
    gift_cards_bought_event([gift_card], gift_card_order, staff_api_client.user, None)
    variables = {"filter": {"giftCardBought": False}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    orders_data = content["data"]["orders"]["edges"]
    assert gift_card_order_id not in {
        order_data["node"]["id"] for order_data in orders_data
    }


@pytest.mark.parametrize(
    ("orders_filter", "count"),
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
    permission_group_manage_orders,
    channel_USD,
):
    Order.objects.create(channel=channel_USD)
    with freeze_time("2012-01-14"):
        Order.objects.create(channel=channel_USD)
    variables = {"filter": orders_filter}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    ("orders_filter", "count"),
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
    permission_group_manage_orders,
    channel_USD,
):
    with freeze_time("2012-01-14 11:00:00"):
        Order.objects.create(channel=channel_USD)

    with freeze_time("2012-01-14 12:00:00"):
        Order.objects.create(channel=channel_USD)

    variables = {"filter": orders_filter}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    ("orders_filter", "count", "payment_status"),
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
    permission_group_manage_orders,
    channel_PLN,
):
    payment_dummy.charge_status = payment_status
    payment_dummy.save()

    payment_dummy.id = None
    payment_dummy.order = Order.objects.create(channel=channel_PLN)
    payment_dummy.charge_status = ChargeStatus.NOT_CHARGED
    payment_dummy.save()

    variables = {"filter": orders_filter}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


def test_order_query_with_filter_payment_fully_refunded_not_active(
    orders_query_with_filter,
    staff_api_client,
    payment_dummy,
    permission_group_manage_orders,
    channel_PLN,
):
    # given
    payment_dummy.charge_status = ChargeStatus.FULLY_REFUNDED
    payment_dummy.is_active = False
    payment_dummy.order = Order.objects.create(channel=channel_PLN)
    payment_dummy.save()
    variables = {"filter": {"paymentStatus": "FULLY_REFUNDED"}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1


@pytest.mark.parametrize(
    ("orders_filter", "count", "status"),
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
    permission_group_manage_orders,
    order_generator,
    channel_USD,
):
    order1 = order_generator(status=status)

    variables = {"filter": orders_filter}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order1.pk)

    orders_ids_from_response = [o["node"]["id"] for o in orders]
    assert len(orders) == count
    assert order_id in orders_ids_from_response


@pytest.mark.parametrize(
    ("orders_filter", "user_field", "user_value"),
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
    permission_group_manage_orders,
    customer_user,
    channel_USD,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(user=customer_user, channel=channel_USD)
    Order.objects.bulk_create([order, Order(channel=channel_USD)])

    variables = {"filter": orders_filter}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


def test_order_query_with_filter_is_click_and_collect_true(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    order_list_with_cc_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    orders = order_list_with_cc_orders
    variables = {"filter": {"isClickAndCollect": True}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

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
    permission_group_manage_orders,
    order_list_with_cc_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    orders = order_list_with_cc_orders
    variables = {"filter": {"isClickAndCollect": False}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

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
    permission_group_manage_orders,
    preorders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"filter": {"isPreorder": True}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

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
    permission_group_manage_orders,
    preorders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"filter": {"isPreorder": False}}

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    preorders_ids = {
        graphene.Node.to_global_id("Order", order.pk) for order in preorders
    }
    preorder_ids = {order["node"]["id"] for order in returned_orders}
    for order_id in preorders_ids:
        assert order_id not in preorder_ids


@pytest.mark.parametrize(
    ("orders_filter", "count"),
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
    permission_group_manage_orders,
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
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == count


def test_orders_query_with_filter_search_by_global_payment_id(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
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
    (
        OrderDiscount.objects.create(
            order=orders[0],
            name="test_discount1",
            value=Decimal("1"),
            amount_value=Decimal("1"),
            translated_name="translated_discount1_name",
        ),
    )

    order_with_payment = orders[0]
    payment = Payment.objects.create(order=order_with_payment)
    global_id = graphene.Node.to_global_id("Payment", payment.pk)
    for order in orders:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(orders, ["search_vector"])

    variables = {"filter": {"search": global_id}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_query_with_filter_search_by_number(
    orders_query_with_filter,
    order_generator,
    staff_api_client,
    permission_group_manage_orders,
):
    order = order_generator(search_vector_class=FlatConcatSearchVector)
    variables = {"filter": {"search": order.number}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_query_with_filter_search_by_number_with_hash(
    orders_query_with_filter,
    order_generator,
    staff_api_client,
    permission_group_manage_orders,
):
    order = order_generator(search_vector_class=FlatConcatSearchVector)
    variables = {"filter": {"search": f"#{order.number}"}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_query_with_filter_search_by_product_sku_with_multiple_identic_sku(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    allocations,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"filter": {"search": allocations[0].order_line.product_sku}}
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 3


def test_order_query_with_filter_search_by_product_sku_order_line(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    order_line,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_line.order
    order.refresh_from_db()
    update_order_search_vector(order)

    variables = {"filter": {"search": order_line.product_sku}}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"][0]
    lines = orders["node"]["lines"][0]["productSku"]
    assert content["data"]["orders"]["totalCount"] == 1
    assert order_line.product_sku in lines


def test_orders_query_with_filter_by_orders_id(
    orders_query_with_filter,
    staff_api_client,
    order,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
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
    permission_group_manage_orders,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
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
    permission_group_manage_orders,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
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
    permission_group_manage_orders,
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
    net = variants[0].get_price(channel_listening)
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {"filter": {"search": lines[0].product_sku}}
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


@pytest.mark.parametrize(
    ("transaction_data", "statuses", "expected_count"),
    [
        (
            {"authorized_value": Decimal("10")},
            [OrderAuthorizeStatusEnum.PARTIAL.name],
            1,
        ),
        (
            {"authorized_value": Decimal("0")},
            [OrderAuthorizeStatusEnum.NONE.name],
            1,
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
            {"authorized_value": Decimal("10"), "charged_value": Decimal("80")},
            [OrderAuthorizeStatusEnum.PARTIAL.name],
            1,
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
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == expected_count


@pytest.mark.parametrize(
    ("transaction_data", "statuses", "expected_count"),
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
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == expected_count


def test_order_query_with_filter_numbers(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    orders,
    channel_USD,
):
    # given
    variables = {
        "filter": {
            "numbers": [str(orders[0].number), str(orders[2].number)],
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

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
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content_from_response(response)

    # then
    assert content["errors"][0]["message"] == error_message
    assert not content["data"]["orders"]


def test_order_query_with_filter_by_checkout_token(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    orders_from_checkout,
    orders,
    checkout,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "filter": {
            "checkoutIds": [
                graphene.Node.to_global_id("Checkout", checkout.token),
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"]

    returned_orders_ids = {edge["node"]["id"] for edge in order_data}
    orders_from_checkout_ids = {
        graphene.Node.to_global_id("Order", order.id) for order in orders_from_checkout
    }

    assert len(returned_orders_ids) == len(orders_from_checkout_ids) == 4
    assert len(returned_orders_ids.intersection(orders_from_checkout_ids)) == 4
    assert content["data"]["orders"]["totalCount"] == 4


def test_order_query_with_filter_by_multiple_checkout_tokens(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    order_generator,
    orders_from_checkout,
    orders,
    checkout,
    checkout_JPY,
):
    # given
    order_from_checkout_JPY = order_generator(
        status=OrderStatus.CANCELED,
        channel=checkout_JPY.channel,
        checkout_token=checkout_JPY.token,
    )
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "filter": {
            "checkoutIds": [
                graphene.Node.to_global_id("Checkout", checkout.token),
                graphene.Node.to_global_id("Checkout", checkout_JPY.token),
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"]

    returned_orders_ids = {edge["node"]["id"] for edge in order_data}
    orders_from_checkout_ids = {
        graphene.Node.to_global_id("Order", order.id) for order in orders_from_checkout
    } | {graphene.Node.to_global_id("Order", order_from_checkout_JPY.id)}

    assert len(returned_orders_ids) == len(orders_from_checkout_ids) == 5
    assert len(returned_orders_ids.intersection(orders_from_checkout_ids)) == 5
    assert content["data"]["orders"]["totalCount"] == 5


def test_order_query_with_filter_by_empty_list(
    orders_query_with_filter,
    staff_api_client,
    permission_group_manage_orders,
    orders_from_checkout,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "filter": {
            "checkoutIds": [],
        }
    }

    # when
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == len(orders_from_checkout)
