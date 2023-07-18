from unittest import mock

import graphene

from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import invalidate_checkout_prices
from .....plugins.manager import get_plugins_manager
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...mutations.utils import update_checkout_shipping_method_if_invalid

MUTATION_CHECKOUT_LINES_DELETE = """
    mutation checkoutLinesDelete($id: ID, $linesIds: [ID!]!) {
        checkoutLinesDelete(id: $id, linesIds: $linesIds) {
            checkout {
                token
                lines {
                    id
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                  message
                  code
                  field
                  lines
            }
        }
    }
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete."
    "invalidate_checkout_prices",
    wraps=invalidate_checkout_prices,
)
def test_checkout_lines_delete(
    mocked_invalidate_checkout_prices,
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_items,
):
    checkout = checkout_with_items
    checkout_lines_count = checkout.lines.count()
    previous_last_change = checkout.last_change
    line = checkout.lines.first()
    second_line = checkout.lines.last()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    second_line_id = graphene.Node.to_global_id("CheckoutLine", second_line.pk)
    lines_list = [first_line_id, second_line_id]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() + len(lines_list) == checkout_lines_count
    remaining_lines = data["checkout"]["lines"]
    lines_ids = [line["id"] for line in remaining_lines]
    assert lines_list not in lines_ids
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout_prices.call_count == 1


def test_checkout_lines_delete_invalid_checkout_id(
    user_api_client, checkout_with_items
):
    checkout = checkout_with_items
    line = checkout.lines.first()
    second_line = checkout.lines.last()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    second_line_id = graphene.Node.to_global_id("CheckoutLine", second_line.pk)
    lines_list = [first_line_id, second_line_id]

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "linesIds": lines_list,
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesDelete"]["errors"][0]
    assert errors["code"] == CheckoutErrorCode.NOT_FOUND.name


def tests_checkout_lines_delete_invalid_lines_ids(user_api_client, checkout_with_items):
    checkout = checkout_with_items
    previous_last_change = checkout.last_change
    line = checkout.lines.first()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    lines_list = [first_line_id, "Q2hlY2tvdXRMaW5lOjE8"]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["errors"][0]
    assert errors["extensions"]["exception"]["code"] == "GraphQLError"
    assert checkout.last_change == previous_last_change


def test_with_active_problems_flow(api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    line = checkout_with_problems.lines.first()
    first_line_id = to_global_id_or_none(line)

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "linesIds": [first_line_id],
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_DELETE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutLinesDelete"]["errors"]
