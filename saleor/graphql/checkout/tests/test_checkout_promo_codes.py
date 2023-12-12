from ....checkout import calculations
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....plugins.manager import get_plugins_manager
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content


def test_checkout_totals_use_discounts(api_client, checkout_with_item, channel_USD):
    # given
    checkout = checkout_with_item
    query = """
    query getCheckout($id: ID) {
        checkout(id: $id) {
            lines {
                totalPrice {
                    gross {
                        amount
                    }
                }
            }
            totalPrice {
                gross {
                    amount
                }
            }
            subtotalPrice {
                gross {
                    amount
                }
            }
        }
    }
    """

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == taxed_total.gross.amount
    assert data["subtotalPrice"]["gross"]["amount"] == taxed_total.gross.amount

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]
    line_total = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
    )
    assert data["lines"][0]["totalPrice"]["gross"]["amount"] == line_total.gross.amount


QUERY_GET_CHECKOUT_GIFT_CARD_CODES = """
query getCheckout($id: ID) {
  checkout(id: $id) {
    token
    giftCards {
      last4CodeChars
      currentBalance {
        amount
      }
    }
    subtotalPrice {
      gross {
        amount
      }
    }
  }
}
"""


def test_checkout_get_gift_card_code(user_api_client, checkout_with_gift_card):
    gift_card = checkout_with_gift_card.gift_cards.first()
    variables = {"id": to_global_id_or_none(checkout_with_gift_card)}
    response = user_api_client.post_graphql(
        QUERY_GET_CHECKOUT_GIFT_CARD_CODES, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["giftCards"][0]
    assert data["last4CodeChars"] == gift_card.display_code
    assert data["currentBalance"]["amount"] == gift_card.current_balance.amount


def test_checkout_get_gift_card_codes(
    user_api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    # given
    checkout_with_gift_card.gift_cards.add(gift_card_created_by_staff)
    checkout_with_gift_card.save()
    gift_card_fist = checkout_with_gift_card.gift_cards.first()
    gift_card_second = checkout_with_gift_card.gift_cards.last()
    variables = {"id": to_global_id_or_none(checkout_with_gift_card)}

    # when
    response = user_api_client.post_graphql(
        QUERY_GET_CHECKOUT_GIFT_CARD_CODES, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["giftCards"]
    gift_cards_dict = {
        data[0]["last4CodeChars"]: data[0],
        data[1]["last4CodeChars"]: data[1],
    }
    assert (
        gift_cards_dict[gift_card_fist.display_code]["currentBalance"]["amount"]
        == gift_card_fist.current_balance.amount
    )
    assert (
        gift_cards_dict[gift_card_second.display_code]["currentBalance"]["amount"]
        == gift_card_second.current_balance.amount
    )


def test_checkout_get_gift_card_code_without_gift_card(user_api_client, checkout):
    variables = {"id": to_global_id_or_none(checkout)}
    response = user_api_client.post_graphql(
        QUERY_GET_CHECKOUT_GIFT_CARD_CODES, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["giftCards"]
    assert not data
