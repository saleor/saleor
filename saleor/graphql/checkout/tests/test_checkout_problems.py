from datetime import timedelta

from django.utils import timezone

from ....checkout.problem_codes import CheckoutProblemCode
from ....warehouse.models import Allocation, Reservation
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content

QUERY_CHECKOUT_WITH_PROBLEMS = """
query checkout($id: ID) {
  checkout(id: $id){
    id
    problems{
      code
      message
      field
    }
  }
}
"""


def test_checkout_without_problems(api_client, checkout_with_items_and_shipping):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert content["data"]["checkout"]["problems"] == []


def test_checkout_without_shipping(api_client, checkout_with_items):
    # given
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert content["data"]["checkout"]["problems"] == []


def test_checkout_with_out_of_stock_when_stocks_dont_exist(
    api_client, checkout_with_items_and_shipping
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)

    checkout_line = checkout.lines.first()
    checkout_line.variant.stocks.all().delete()

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["code"]
        == CheckoutProblemCode.INSUFFICIENT_STOCK.name
    )
    assert content["data"]["checkout"]["problems"][0]["field"] == "lines"


def test_checkout_problem_out_of_stock_without_available_quantity(
    api_client, checkout_with_items_and_shipping
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)

    checkout_line = checkout.lines.first()
    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = checkout_line.quantity - 1
    stock.save(update_fields=["quantity"])

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["code"]
        == CheckoutProblemCode.INSUFFICIENT_STOCK.name
    )
    assert content["data"]["checkout"]["problems"][0]["field"] == "lines"


def test_checkout_problems_with_reservation(api_client, checkout_with_items):
    # given
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)

    checkout_line = checkout.lines.first()
    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = checkout_line.quantity
    stock.save(update_fields=["quantity"])

    reserved_until = timezone.now() + timedelta(minutes=5)
    Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=checkout_line.quantity,
        reserved_until=reserved_until,
    )

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert content["data"]["checkout"]["problems"] == []


def test_checkout_with_out_of_stock_with_allocations_and_not_enough_items(
    api_client, checkout_with_items_and_shipping, order_line
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)

    line_quantity = 5
    checkout_line = checkout.lines.first()
    checkout_line.quantity = line_quantity
    checkout_line.save(update_fields=["quantity"])

    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = line_quantity + 2
    stock.save(update_fields=["quantity"])

    order_line.variant = checkout_line.variant
    order_line.save(update_fields=["variant"])
    Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=line_quantity
    )

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["code"]
        == CheckoutProblemCode.INSUFFICIENT_STOCK.name
    )
    assert content["data"]["checkout"]["problems"][0]["field"] == "lines"


def test_checkout_out_of_stock_without_tracking_inventory(
    api_client, checkout_with_items_and_shipping
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)

    checkout_line = checkout.lines.first()
    checkout_line.variant.stocks.all().delete()
    checkout_line.variant.track_inventory = False
    checkout_line.variant.save(update_fields=["track_inventory"])

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 0


def test_checkout_with_multiple_same_variant_and_out_of_stock(
    api_client, checkout_with_items_and_shipping
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)

    checkout_line = checkout.lines.first()
    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = checkout_line.quantity
    stock.save(update_fields=["quantity"])

    second_checkout_line = checkout_line
    second_checkout_line.pk = None
    second_checkout_line.save()

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["code"]
        == CheckoutProblemCode.INSUFFICIENT_STOCK.name
    )
    assert content["data"]["checkout"]["problems"][0]["field"] == "lines"
