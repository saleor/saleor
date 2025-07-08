from decimal import Decimal

import graphene
import pytest
from prices import Money, TaxedMoney

from .....core.postgres import FlatConcatSearchVector
from .....discount.models import OrderDiscount
from .....invoice.models import Invoice
from .....order import OrderEvents
from .....order.models import Order, Payment
from .....order.search import prepare_order_search_vector_value
from ....tests.utils import get_graphql_content

ORDERS_QUERY_WITH_SEARCH = """
  query ($search: String) {
    orders(first: 10, search:$search) {
      totalCount
      edges {
        node {
          id
          number
        }
      }
    }
  }
"""


def update_orders_search_vector(orders):
    for order in orders:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(orders, ["search_vector"])


@pytest.mark.parametrize(
    ("search_value", "count"),
    [
        ("discount name", 2),
        ("Some other", 1),
        ("translated", 1),
        ("test@mirumee.com", 1),
        ("Leslie", 1),
        ("Wade", 1),
        ("Leslie Wade", 1),
        ("", 3),
        ("ExternalID", 1),
        ("SKU_A", 1),
    ],
)
def test_orders_query_with_search(
    search_value,
    count,
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    channel_USD,
    product,
    variant,
):
    # given
    orders = Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                user_email="test@mirumee.com",
                channel=channel_USD,
                lines_count=0,
            ),
            Order(
                user_email="user_email1@example.com",
                channel=channel_USD,
                lines_count=0,
            ),
            Order(
                user_email="user_email2@example.com",
                channel=channel_USD,
                lines_count=0,
            ),
        ]
    )

    OrderDiscount.objects.bulk_create(
        [
            OrderDiscount(
                order=orders[0],
                name="Some discount name",
                value=Decimal(1),
                amount_value=Decimal(1),
                translated_name="translated",
            ),
            OrderDiscount(
                order=orders[2],
                name="Some other discount name",
                value=Decimal(10),
                amount_value=Decimal(10),
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

    update_orders_search_vector(orders)

    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == count


def test_orders_query_with_search_by_order_id(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
):
    # given
    update_orders_search_vector(order_list)

    search_value = graphene.Node.to_global_id("Order", order_list[1].pk)
    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1
    assert content["data"]["orders"]["edges"][0]["node"]["id"] == search_value


def test_orders_query_with_search_by_invoice_id(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
):
    # given
    invoices = Invoice.objects.bulk_create(
        [Invoice(order=order, number=f"INV-{order.pk}") for order in order_list]
    )
    update_orders_search_vector(order_list)

    search_value = graphene.Node.to_global_id("Invoice", invoices[2].pk)
    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1
    assert content["data"]["orders"]["edges"][0]["node"][
        "id"
    ] == graphene.Node.to_global_id("Order", order_list[2].pk)


def test_orders_query_with_search_by_order_event_message(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
):
    # given
    event_message = "Special event message for search"
    order = order_list[0]
    order.events.create(
        type=OrderEvents.NOTE_ADDED,
        user=None,
        parameters={"message": event_message},
    )

    update_orders_search_vector(order_list)

    variables = {"search": "Special event message"}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1
    assert content["data"]["orders"]["edges"][0]["node"][
        "id"
    ] == graphene.Node.to_global_id("Order", order_list[0].pk)


@pytest.mark.parametrize(
    ("search_value", "expected_count"),
    [
        ("match in", 1),
        ("note", 2),
        ("partial", 1),
        ("unrelated", 0),
    ],
)
def test_orders_query_with_search_by_partial_customer_note(
    search_value,
    expected_count,
    staff_api_client,
    permission_group_manage_orders,
    order_list,
):
    # given
    notes = [
        "This is a match in the customer note",
        "This note has a partial match",
        "",
    ]
    for order, note in zip(order_list, notes, strict=True):
        order.customer_note = note

    Order.objects.bulk_update(order_list, ["customer_note"])
    update_orders_search_vector(order_list)

    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == expected_count


def test_orders_query_with_search_by_product_name(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    product,
    variant,
):
    # given
    order = order_list[0]
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    product_name = str(product)
    order.lines.create(
        product_name=product_name,
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=2,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * 2,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * 2,
        tax_rate=Decimal("0.23"),
    )

    update_orders_search_vector(order_list)

    variables = {"search": product_name}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1
    assert content["data"]["orders"]["edges"][0]["node"][
        "id"
    ] == graphene.Node.to_global_id("Order", order.pk)


def test_orders_query_with_search_by_variant_name(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    product,
    variant,
):
    # given
    order = order_list[1]
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    variant_name = str(variant)
    order.lines.create(
        product_name=str(product),
        variant_name=variant_name,
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=1,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price,
        tax_rate=Decimal("0.23"),
    )

    update_orders_search_vector(order_list)

    variables = {"search": variant_name}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1
    assert content["data"]["orders"]["edges"][0]["node"][
        "id"
    ] == graphene.Node.to_global_id("Order", order.pk)


def test_orders_query_with_search_by_product_sku(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    product,
    variant,
):
    # given
    order = order_list[2]
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    sku = variant.sku
    order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=4,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * 4,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * 4,
        tax_rate=Decimal("0.23"),
    )

    update_orders_search_vector(order_list)

    variables = {"search": sku}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1
    assert content["data"]["orders"]["edges"][0]["node"][
        "id"
    ] == graphene.Node.to_global_id("Order", order.pk)


@pytest.mark.parametrize(
    ("search_value", "expected_count"),
    [
        ("First", 1),
        ("Last", 1),
        ("First Last", 1),
        ("Billing Street", 1),
        ("PL", 1),
        ("US", 2),
        ("Nonexistent", 0),
    ],
)
def test_orders_query_with_search_by_billing_address_fields(
    search_value,
    expected_count,
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    address,
    address_usa,
):
    # given
    order = order_list[0]
    address.first_name = "First"
    address.last_name = "Last"
    address.street_address_1 = "Billing Street"
    address.country = "PL"
    address.save()

    order.billing_address = address
    for order in order_list[1:]:
        order.billing_address = address_usa
    Order.objects.bulk_update(order_list, ["billing_address"])

    update_orders_search_vector(order_list)

    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == expected_count


@pytest.mark.parametrize(
    ("search_value", "expected_count"),
    [
        ("First", 1),
        ("Last", 1),
        ("First Last", 1),
        ("Shipping Street", 1),
        ("JP", 1),
        ("US", 2),
        ("Nonexistent", 0),
    ],
)
def test_orders_query_with_search_by_shipping_address_fields(
    search_value,
    expected_count,
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    address,
    address_usa,
):
    # given
    order = order_list[0]
    address.first_name = "First"
    address.last_name = "Last"
    address.street_address_1 = "Shipping Street"
    address.country = "JP"
    address.save()

    order.shipping_address = address
    for order in order_list[1:]:
        order.shipping_address = address_usa
    Order.objects.bulk_update(order_list, ["shipping_address"])

    update_orders_search_vector(order_list)

    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == expected_count


@pytest.mark.parametrize(
    ("search_value", "expected_order_idxes"),
    [
        ("EXT-REF-12345", [0]),
        ("REF", [0, 1]),
        ("ANOTHER-REF-67890", [1]),
        ("nonexistent-ref", []),
    ],
)
def test_orders_query_with_search_by_external_reference(
    search_value,
    expected_order_idxes,
    staff_api_client,
    permission_group_manage_orders,
    order_list,
):
    # given
    external_references = ["EXT-REF-12345", "ANOTHER-REF-67890", ""]
    for order, ext_ref in zip(order_list, external_references, strict=True):
        order.external_reference = ext_ref
    Order.objects.bulk_update(order_list, ["external_reference"])

    update_orders_search_vector(order_list)

    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == len(expected_order_idxes)
    returned_numbers = [
        edge["node"]["number"] for edge in content["data"]["orders"]["edges"]
    ]
    expected_numbers = [str(order_list[idx].number) for idx in expected_order_idxes]
    assert set(returned_numbers) == set(expected_numbers)
