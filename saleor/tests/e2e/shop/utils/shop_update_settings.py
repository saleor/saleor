from ...utils import get_graphql_content

SHOP_SETTING_UPDATE_MUTATION = """
mutation ShopSettingsUpdate($input: ShopSettingsInput!) {
  shopSettingsUpdate(input: $input) {
    errors {
      field
      message
      code
    }
    shop {
      enableAccountConfirmationByEmail
      fulfillmentAutoApprove
      fulfillmentAllowUnpaid
    }
  }
}
"""


def update_shop_settings(staff_api_client, input):
    variables = {"input": input}

    response = staff_api_client.post_graphql(SHOP_SETTING_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["shopSettingsUpdate"]["errors"] == []

    data = content["data"]["shopSettingsUpdate"]["shop"]

    return data
