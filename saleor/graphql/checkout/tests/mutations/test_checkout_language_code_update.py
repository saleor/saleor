from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE = """
mutation checkoutLanguageCodeUpdate($id: ID, $languageCode: LanguageCodeEnum!){
  checkoutLanguageCodeUpdate(id: $id, languageCode: $languageCode){
    checkout{
      id
      languageCode
    }
    errors{
      field
      message
      code
    }
  }
}
"""


def test_checkout_update_language_code(
    user_api_client,
    checkout_with_gift_card,
):
    language_code = "PL"
    checkout = checkout_with_gift_card
    previous_last_change = checkout.last_change
    variables = {"id": to_global_id_or_none(checkout), "languageCode": language_code}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE, variables
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutLanguageCodeUpdate"]
    assert not data["errors"]

    assert data["checkout"]["languageCode"] == language_code
    checkout.refresh_from_db()
    assert checkout.language_code == language_code.lower()
    assert checkout.last_change != previous_last_change


def test_with_active_problems_flow(api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "languageCode": "PL",
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutLanguageCodeUpdate"]["errors"]
