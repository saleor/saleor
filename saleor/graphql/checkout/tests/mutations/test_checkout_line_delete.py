from unittest import mock

import graphene

from .....checkout import base_calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import (
    add_variant_to_checkout,
    add_voucher_to_checkout,
    calculate_checkout_quantity,
    invalidate_checkout_prices,
)
from .....plugins.manager import get_plugins_manager
from .....warehouse.models import Reservation
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...mutations.utils import update_checkout_shipping_method_if_invalid

MUTATION_CHECKOUT_LINE_DELETE = """
    mutation checkoutLineDelete($id: ID, $lineId: ID!) {
        checkoutLineDelete(id: $id, lineId: $lineId) {
            checkout {
                token
                lines {
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                field
                message
            }
        }
    }
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete."
    "invalidate_checkout_prices",
    wraps=invalidate_checkout_prices,
)
def test_checkout_line_delete(
    mocked_invalidate_checkout_prices,
    mocked_update_shipping_method,
    user_api_client,
    checkout_line_with_reservation_in_many_stocks,
):
    assert Reservation.objects.count() == 2
    checkout = checkout_line_with_reservation_in_many_stocks.checkout
    previous_last_change = checkout.last_change
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.quantity == 3

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"id": to_global_id_or_none(checkout), "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 0
    assert calculate_checkout_quantity(lines) == 0
    assert Reservation.objects.count() == 0
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout_prices.call_count == 1


def test_checkout_lines_delete_with_not_applicable_voucher(
    user_api_client, checkout_with_item, voucher, channel_USD
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
    )
    voucher.channel_listings.filter(channel=channel_USD).update(
        min_spent_amount=subtotal.amount
    )
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    assert checkout_with_item.voucher_code == voucher.code

    line = checkout_with_item.lines.first()

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variables = {"id": to_global_id_or_none(checkout_with_item), "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.lines.count() == 0
    assert checkout_with_item.voucher_code is None


def test_checkout_line_delete_remove_shipping_if_removed_product_with_shipping(
    user_api_client, checkout_with_item, digital_content, address, shipping_method
):
    checkout = checkout_with_item
    digital_variant = digital_content.product_variant
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, digital_variant, 1)
    line = checkout.lines.first()

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"id": to_global_id_or_none(checkout), "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    assert not checkout.shipping_method


def test_with_active_problems_flow(
    api_client, checkout_with_problems, product_with_single_variant
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variant = product_with_single_variant.variants.first()

    checkout_info = fetch_checkout_info(
        checkout_with_problems, [], get_plugins_manager()
    )
    add_variant_to_checkout(checkout_info, variant, 1)

    line = checkout_info.checkout.lines.last()

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "lineId": to_global_id_or_none(line),
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_LINE_DELETE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutLineDelete"]["errors"]
