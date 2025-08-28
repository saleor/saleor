from .....graphql.tests.fixtures import BaseApiClient
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


def gift_card_query(
    staff_api_client: BaseApiClient,
    gift_card_id: str,
):
    variables = {
        "id": gift_card_id,
    }

    response = staff_api_client.post_graphql(
        GIFT_CARD_QUERY,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    return data
