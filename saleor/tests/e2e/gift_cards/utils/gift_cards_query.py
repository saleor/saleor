from ...utils import get_graphql_content

GIFT_CARDS_QUERY = """
query GiftCards($first: Int) {
  giftCards(first: $first) {
    edges {
      node {
        id
        code
        initialBalance {
          amount
        }
      }
    }
  }
}
"""


def get_gift_cards(
    staff_api_client,
    first=10,
):
    variables = {
        "first": first,
    }

    response = staff_api_client.post_graphql(
        GIFT_CARDS_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    return data
