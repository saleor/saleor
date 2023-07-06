import datetime
from datetime import timedelta

import pytz
from django.utils import timezone

from ....product.models import ProductChannelListing, ProductVariantChannelListing
from ....warehouse.models import Allocation, Reservation
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content

QUERY_CHECKOUT_WITH_PROBLEMS = """
query checkout($id: ID) {
  checkout(id: $id){
    id
    problems{
      __typename
      ... on CheckoutLineProblemInsufficientStock{
        availableQuantity
        variant{
          id
        }
        line{
          id
        }
      }
      ... on CheckoutLineProblemVariantNotAvailable{
        line{
          id
        }
      }
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
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemInsufficientStock"
    )
    assert content["data"]["checkout"]["problems"][0]["availableQuantity"] == 0
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)
    assert content["data"]["checkout"]["problems"][0]["variant"][
        "id"
    ] == to_global_id_or_none(checkout_line.variant)


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
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemInsufficientStock"
    )
    assert content["data"]["checkout"]["problems"][0]["availableQuantity"] == 0
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)
    assert content["data"]["checkout"]["problems"][0]["variant"][
        "id"
    ] == to_global_id_or_none(checkout_line.variant)


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

    free_quantity = 2
    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = line_quantity + free_quantity
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
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemInsufficientStock"
    )
    assert (
        content["data"]["checkout"]["problems"][0]["availableQuantity"] == free_quantity
    )
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)
    assert content["data"]["checkout"]["problems"][0]["variant"][
        "id"
    ] == to_global_id_or_none(checkout_line.variant)


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
    available_quantity = stock.quantity

    second_checkout_line = checkout_line
    second_checkout_line.quantity = 1
    second_checkout_line.pk = None
    second_checkout_line.save()

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 2
    problems = content["data"]["checkout"]["problems"]
    assert all(
        [problem["availableQuantity"] == available_quantity for problem in problems]
    )
    problem_line_ids = [problem["line"]["id"] for problem in problems]
    problem_variant_ids = [problem["variant"]["id"] for problem in problems]
    assert to_global_id_or_none(checkout_line) in problem_line_ids
    assert to_global_id_or_none(second_checkout_line) in problem_line_ids
    assert to_global_id_or_none(checkout_line.variant) in problem_variant_ids


def test_checkout_problems_when_product_is_not_published(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    product = checkout_line.variant.product
    product.channel_listings.update(is_published=False)

    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)


def test_checkout_problems_when_product_doesnt_have_channel_listing(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    available_at = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=5)
    product = checkout_line.variant.product
    product.channel_listings.update(available_for_purchase_at=available_at)

    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)


def test_checkout_problems_when_product_is_not_available_to_purchase(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    product = checkout_line.variant.product
    ProductChannelListing.objects.filter(product=product).delete()

    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)


def test_checkout_problems_when_product_variant_doesnt_have_channel_listing(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    variant = checkout_line.variant
    ProductVariantChannelListing.objects.filter(variant=variant).delete()

    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)


def test_checkout_problems_when_variant_channel_listing_doesnt_have_price_amount(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    variant = checkout_line.variant
    ProductVariantChannelListing.objects.filter(variant=variant).update(
        price_amount=None
    )

    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 1
    assert (
        content["data"]["checkout"]["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert content["data"]["checkout"]["problems"][0]["line"][
        "id"
    ] == to_global_id_or_none(checkout_line)
