from ...utils import get_graphql_content

GIFT_CARD_CREATE_MUTATION = """
mutation GiftCardCreate($input: GiftCardCreateInput!) {
  giftCardCreate(input: $input) {
    giftCard {
      id
      code
    }
    errors {
      code
      field
      message
    }
  }
}
"""


def create_gift_card(
    staff_api_client,
    amount,
    currency="USD",
    active=True,
    email=None,
    channel=None,
):
    variables = {
        "input": {
            "note": "note",
            "addTags": ["tag_test"],
            "userEmail": email,
            "channel": channel,
            "balance": {"amount": amount, "currency": currency},
            "isActive": active,
        }
    }

    response = staff_api_client.post_graphql(
        GIFT_CARD_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["giftCardCreate"]["errors"] == []

    data = content["data"]["giftCardCreate"]["giftCard"]
    assert data["id"] is not None
    assert data["code"] is not None

    return data
