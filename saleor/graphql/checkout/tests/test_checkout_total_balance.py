import pytest

from ....checkout import calculations
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....plugins.manager import get_plugins_manager
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content

MUTATION_CHECKOUT_ADD_PROMO_CODE = """
    mutation($id: ID, $promoCode: String!) {
        checkoutAddPromoCode(
            id: $id, promoCode: $promoCode) {
            errors {
                field
                message
                code
            }
            checkout {
                id
                token
                totalBalance {
                    amount
                }
            }
        }
    }
"""


def mutate_checkout_add_promo_code(client, variables):
    response = client.post_graphql(MUTATION_CHECKOUT_ADD_PROMO_CODE, variables)
    content = get_graphql_content(response)
    return content["data"]["checkoutAddPromoCode"]


@pytest.mark.parametrize(
    ("gift_card_balance", "expected_total_balance"),
    [
        (0, -30),  # gift card does not cover checkout total price at all
        (10, -20),  # gift card partially does cover checkout total price
        (30, 0),  # gift card fully cover checkout total price
        (50, 0),  # gift card cover more than checkout total price
    ],
)
def test_checkout_total_balance(
    api_client, checkout_with_item, gift_card, gift_card_balance, expected_total_balance
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_total = calculations.calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )

    assert checkout_total.gross.amount == 30

    gift_card.initial_balance_amount = gift_card_balance
    gift_card.current_balance_amount = gift_card_balance
    gift_card.save(update_fields=["initial_balance_amount", "current_balance_amount"])

    # when
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }
    data = mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert data["checkout"]["totalBalance"]["amount"] == expected_total_balance


@pytest.mark.parametrize(
    ("transaction_charged_value", "gift_card_balance", "expected_total_balance"),
    [
        (5, 0, -25),  # transaction partially cover checkout total price
        (5, 10, -15),  # transaction and gift card partially cover checkout total price
        (5, 25, 0),  # transaction and gift card fully cover checkout total price
        (
            5,
            50,
            5,
        ),  # transaction and gift card cover more than checkout total price, all funds are taken from gift card
        (30, 0, 0),  # transaction fully cover checkout total price
        (
            30,
            5,
            5,
        ),  # transaction and gift card cover more than checkout total price, funds are first taken from gift card and then from transaction
        (
            30,
            30,
            30,
        ),  # transaction and gift card cover more than checkout total price, funds are first taken from gift card and then from transaction
        (
            30,
            50,
            30,
        ),  # transaction and gift card cover more than checkout total price, funds are first taken from gift card and then from transaction
    ],
)
def test_checkout_total_balance_with_charge_transaction(
    api_client,
    checkout_with_item,
    gift_card,
    transaction_item_generator,
    transaction_charged_value,
    gift_card_balance,
    expected_total_balance,
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_total = calculations.calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )

    assert checkout_total.gross.amount == 30

    gift_card.initial_balance_amount = gift_card_balance
    gift_card.current_balance_amount = gift_card_balance
    gift_card.save(update_fields=["initial_balance_amount", "current_balance_amount"])

    transaction_item_generator(
        checkout_id=checkout_with_item.pk, charged_value=transaction_charged_value
    )

    # when
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }
    data = mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert data["checkout"]["totalBalance"]["amount"] == expected_total_balance
