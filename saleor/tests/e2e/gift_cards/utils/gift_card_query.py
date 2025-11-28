from ...utils import get_graphql_content

GIFT_CARD_QUERY = """
query GiftCard($id: ID!) {
  giftCard(id: $id) {
    id
    code
    initialBalance {
      amount
      currency
    }
    currentBalance {
      amount
      currency
    }
  }
}
"""


def get_gift_card(
    staff_api_client,
    gift_card_id,
):
    variables = {
        "id": gift_card_id,
    }

    response = staff_api_client.post_graphql(
        GIFT_CARD_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    return content["data"]["giftCard"]
