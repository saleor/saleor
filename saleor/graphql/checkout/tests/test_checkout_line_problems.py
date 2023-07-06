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
        [problem["availableQuantity"] == available_quantity for problem in problems]
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
