from unittest import mock

import graphene

from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import CheckoutLine
from .....checkout.utils import invalidate_checkout
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
    "saleor.graphql.checkout.mutations.checkout_lines_delete.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_lines_delete(
    mocked_invalidate_checkout,
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
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


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


def test_checkout_lines_delete_non_removable_gift(user_api_client, checkout_with_items):
    # given
    checkout = checkout_with_items
    gift_line = checkout.lines.first()
    gift_line.is_gift = True
    gift_line.save(update_fields=["is_gift"])
    non_gift_line = checkout.lines.last()
    gift_line_id = to_global_id_or_none(gift_line)
    non_gift_line_id = to_global_id_or_none(non_gift_line)
    lines_list = [gift_line_id, non_gift_line_id]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutLinesDelete"]
    assert not data["checkout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lineIds"
    assert errors[0]["code"] == CheckoutErrorCode.NON_REMOVABLE_GIFT_LINE.name
    assert errors[0]["lines"] == [gift_line_id]


def test_checkout_lines_delete_not_associated_with_checkout(
    user_api_client, checkout_with_items, checkouts_list, variant
):
    # given
    checkout = checkout_with_items
    wrong_checkout = checkouts_list[0]
    line = CheckoutLine.objects.create(
        checkout=wrong_checkout,
        variant=variant,
        quantity=1,
    )
    line_id = to_global_id_or_none(line)
    variables = {"id": to_global_id_or_none(checkout), "linesIds": [line_id]}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutLinesDelete"]
    assert not data["checkout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lineId"
    assert errors[0]["code"] == CheckoutErrorCode.INVALID.name
    assert errors[0]["lines"] == [line_id]
