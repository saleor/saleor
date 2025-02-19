import datetime
from unittest import mock

import pytest
from django.utils import timezone

from ....checkout.calculations import _fetch_checkout_prices_if_expired
from ....checkout.fetch import fetch_checkout_lines
from ....product.models import ProductChannelListing, ProductVariantChannelListing
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
    lines{
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
}
"""


def test_line_without_any_problem(api_client, checkout_with_items_and_shipping):
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
    for line_data in content["data"]["checkout"]["lines"]:
        assert line_data["problems"] == []


def test_line_variant_without_stock(api_client, checkout_with_items_and_shipping):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)

    checkout_line = checkout.lines.first()
    checkout_line.variant.stocks.all().delete()
    checkout_line_id = to_global_id_or_none(checkout_line)

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

    line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(line_without_stock["problems"]) == 1
    assert (
        line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemInsufficientStock"
    )
    assert line_without_stock["problems"][0]["availableQuantity"] == 0
    assert line_without_stock["problems"][0]["line"]["id"] == checkout_line_id
    assert line_without_stock["problems"][0]["variant"]["id"] == to_global_id_or_none(
        checkout_line.variant
    )


def test_line_variant_with_insufficient_stock(
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
    checkout_line_id = to_global_id_or_none(checkout_line)

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

    line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(line_without_stock["problems"]) == 1
    assert (
        line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemInsufficientStock"
    )
    assert line_without_stock["problems"][0]["availableQuantity"] == 0
    assert line_without_stock["problems"][0]["line"]["id"] == checkout_line_id
    assert line_without_stock["problems"][0]["variant"]["id"] == to_global_id_or_none(
        checkout_line.variant
    )


def test_line_variant_without_tracking_inventory(
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
    checkout_line.variant.track_inventory = False
    checkout_line.variant.save(update_fields=["track_inventory"])

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)

    assert content["data"]["checkout"]["id"] == checkout_id
    assert content["data"]["checkout"]["problems"] == []
    for line_data in content["data"]["checkout"]["lines"]:
        assert line_data["problems"] == []


def test_lines_with_same_variant(api_client, checkout_with_items_and_shipping):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_id = to_global_id_or_none(checkout)

    checkout_line = checkout.lines.first()

    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = checkout_line.quantity - 1
    stock.save(update_fields=["quantity"])
    available_quantity = stock.quantity

    second_checkout_line = checkout_line
    second_checkout_line.pk = None
    second_checkout_line.save()
    second_checkout_line_id = to_global_id_or_none(second_checkout_line)
    checkout_line_id = to_global_id_or_none(checkout_line)

    variables = {"id": checkout_id, "channel": checkout.channel.slug}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_WITH_PROBLEMS, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == checkout_id
    assert len(content["data"]["checkout"]["problems"]) == 2
    problems = content["data"]["checkout"]["problems"]
    assert all(
        problem["availableQuantity"] == available_quantity for problem in problems
    )
    problem_line_ids = [problem["line"]["id"] for problem in problems]
    problem_variant_ids = [problem["variant"]["id"] for problem in problems]
    assert to_global_id_or_none(checkout_line) in problem_line_ids
    assert to_global_id_or_none(second_checkout_line) in problem_line_ids
    assert to_global_id_or_none(checkout_line.variant) in problem_variant_ids

    first_line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(first_line_without_stock["problems"]) == 1
    assert (
        first_line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemInsufficientStock"
    )
    assert (
        first_line_without_stock["problems"][0]["availableQuantity"]
        == available_quantity
    )

    second_line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == second_checkout_line_id
    ][0]
    assert len(second_line_without_stock["problems"]) == 1
    assert (
        second_line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemInsufficientStock"
    )
    assert (
        second_line_without_stock["problems"][0]["availableQuantity"]
        == available_quantity
    )


def test_product_is_not_published(checkout_with_items_and_shipping, api_client):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    product = checkout_line.variant.product
    product.channel_listings.update(is_published=False)

    checkout_line_id = to_global_id_or_none(checkout_line)

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

    line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(line_without_stock["problems"]) == 1
    assert (
        line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert line_without_stock["problems"][0]["line"]["id"] == checkout_line_id


def test_product_doesnt_have_channel_listing(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    available_at = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=5)
    product = checkout_line.variant.product
    product.channel_listings.update(available_for_purchase_at=available_at)

    checkout_line_id = to_global_id_or_none(checkout_line)

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

    line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(line_without_stock["problems"]) == 1
    assert (
        line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert line_without_stock["problems"][0]["line"]["id"] == checkout_line_id


def test_product_is_not_available_to_purchase(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    product = checkout_line.variant.product
    ProductChannelListing.objects.filter(product=product).delete()

    checkout_line_id = to_global_id_or_none(checkout_line)

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

    line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(line_without_stock["problems"]) == 1
    assert (
        line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert line_without_stock["problems"][0]["line"]["id"] == checkout_line_id


def test_product_variant_doesnt_have_channel_listing(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    variant = checkout_line.variant
    ProductVariantChannelListing.objects.filter(variant=variant).delete()

    checkout_line_id = to_global_id_or_none(checkout_line)

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

    line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(line_without_stock["problems"]) == 1
    assert (
        line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert line_without_stock["problems"][0]["line"]["id"] == checkout_line_id


def test_product_variant_channel_listing_doesnt_have_price_amount(
    checkout_with_items_and_shipping, api_client
):
    # given
    checkout = checkout_with_items_and_shipping
    checkout_line = checkout.lines.first()

    variant = checkout_line.variant
    ProductVariantChannelListing.objects.filter(variant=variant).update(
        price_amount=None
    )

    checkout_line_id = to_global_id_or_none(checkout_line)

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

    line_without_stock = [
        line
        for line in content["data"]["checkout"]["lines"]
        if line["id"] == checkout_line_id
    ][0]
    assert len(line_without_stock["problems"]) == 1
    assert (
        line_without_stock["problems"][0]["__typename"]
        == "CheckoutLineProblemVariantNotAvailable"
    )
    assert line_without_stock["problems"][0]["line"]["id"] == checkout_line_id


CHECKOUTS_WITH_LINE_TOTAL_IN_PROBLEMS_QUERY = """
{
  checkouts(first: 10) {
    edges {
      node {
        lines {
          problems {
            __typename
            ... on CheckoutLineProblemVariantNotAvailable {
              line {
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
            ... on CheckoutLineProblemInsufficientStock {
              line {
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


CHECKOUTS_WITH_TOTAL_INSIDE_PROBLEMS_QUERY = """
{
  checkouts(first:10){
    edges{
      node{
        problems{
          __typename
          ...on CheckoutLineProblemVariantNotAvailable{
            line{
              totalPrice{
                gross{
                  amount
                }
              }
            }
          }
          ...on CheckoutLineProblemInsufficientStock{
            line{
              totalPrice{
                gross{
                  amount
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    "query",
    [
        CHECKOUTS_WITH_LINE_TOTAL_IN_PROBLEMS_QUERY,
        CHECKOUTS_WITH_TOTAL_INSIDE_PROBLEMS_QUERY,
    ],
)
@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations._calculate_and_add_tax")
def test_query_checkouts_do_not_trigger_sync_tax_webhooks_when_variant_not_available(
    mocked_calculate_and_add_tax,
    mocked_fetch_checkout_prices_if_expired,
    query,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_tax_app,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    checkout_line = checkout.lines.first()

    variant = checkout_line.variant
    ProductVariantChannelListing.objects.filter(variant=variant).delete()

    # when
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["checkouts"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_calculate_and_add_tax.assert_not_called()
    mocked_fetch_checkout_prices_if_expired.assert_called_once_with(
        checkout_info=mock.ANY,
        allow_sync_webhooks=False,
        address=None,
        database_connection_name=mock.ANY,
        force_update=False,
        lines=lines,
        manager=mock.ANY,
        pregenerated_subscription_payloads=mock.ANY,
    )


@pytest.mark.parametrize(
    "query",
    [
        CHECKOUTS_WITH_LINE_TOTAL_IN_PROBLEMS_QUERY,
        CHECKOUTS_WITH_TOTAL_INSIDE_PROBLEMS_QUERY,
    ],
)
@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations.update_checkout_prices_with_flat_rates")
def test_query_checkouts_calculate_flat_taxes_when_variant_not_available(
    mocked_update_order_prices_with_flat_rates,
    mocked_fetch_checkout_prices_if_expired,
    query,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_flat_rates,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    ProductVariantChannelListing.objects.all().delete()

    # when
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_update_order_prices_with_flat_rates.assert_called_once_with(
        checkout_with_item,
        mock.ANY,
        lines,
        tax_configuration_flat_rates.prices_entered_with_tax,
        None,
        database_connection_name=mock.ANY,
    )
    mocked_fetch_checkout_prices_if_expired.assert_called_once()


@pytest.mark.parametrize(
    "query",
    [
        CHECKOUTS_WITH_LINE_TOTAL_IN_PROBLEMS_QUERY,
        CHECKOUTS_WITH_TOTAL_INSIDE_PROBLEMS_QUERY,
    ],
)
@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations._calculate_and_add_tax")
def test_query_checkouts_do_not_trigger_sync_tax_webhooks_when_out_of_stock(
    mocked_calculate_and_add_tax,
    mocked_fetch_checkout_prices_if_expired,
    query,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_tax_app,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    checkout_line = checkout.lines.first()

    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = checkout_line.quantity - 1
    stock.save(update_fields=["quantity"])

    # when
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["checkouts"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_calculate_and_add_tax.assert_not_called()
    mocked_fetch_checkout_prices_if_expired.assert_called_once_with(
        checkout_info=mock.ANY,
        allow_sync_webhooks=False,
        address=None,
        database_connection_name=mock.ANY,
        force_update=False,
        lines=lines,
        manager=mock.ANY,
        pregenerated_subscription_payloads=mock.ANY,
    )


@pytest.mark.parametrize(
    "query",
    [
        CHECKOUTS_WITH_LINE_TOTAL_IN_PROBLEMS_QUERY,
        CHECKOUTS_WITH_TOTAL_INSIDE_PROBLEMS_QUERY,
    ],
)
@mock.patch(
    "saleor.checkout.calculations._fetch_checkout_prices_if_expired",
    wraps=_fetch_checkout_prices_if_expired,
)
@mock.patch("saleor.checkout.calculations.update_checkout_prices_with_flat_rates")
def test_query_checkouts_calculate_flat_taxes_when_variant_out_of_stock(
    mocked_update_order_prices_with_flat_rates,
    mocked_fetch_checkout_prices_if_expired,
    query,
    checkout_with_item,
    staff_api_client,
    permission_manage_checkouts,
    tax_configuration_flat_rates,
):
    # given
    checkout = checkout_with_item
    checkout.price_expiration = timezone.now()
    checkout.save()

    checkout_line = checkout.lines.first()

    stocks = checkout_line.variant.stocks.all()
    stocks.update(quantity=0)
    stock = stocks.first()
    stock.quantity = checkout_line.quantity - 1
    stock.save(update_fields=["quantity"])

    # when
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"])

    lines, _ = fetch_checkout_lines(checkout_with_item)

    mocked_update_order_prices_with_flat_rates.assert_called_once_with(
        checkout_with_item,
        mock.ANY,
        lines,
        tax_configuration_flat_rates.prices_entered_with_tax,
        None,
        database_connection_name=mock.ANY,
    )
    mocked_fetch_checkout_prices_if_expired.assert_called_once()
