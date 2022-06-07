import graphene

from .....checkout.error_codes import CheckoutErrorCode
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE = """
mutation checkoutLanguageCodeUpdate(
    $checkoutId: ID, $token: UUID, $languageCode: LanguageCodeEnum!
){
  checkoutLanguageCodeUpdate(
      checkoutId: $checkoutId, token: $token, languageCode: $languageCode
  ){
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


def test_checkout_update_language_code_by_id(
    user_api_client,
    checkout_with_gift_card,
):
    language_code = "PL"
    checkout = checkout_with_gift_card
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "languageCode": language_code}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE, variables
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutLanguageCodeUpdate"]
    assert not data["errors"]

    assert data["checkout"]["languageCode"] == language_code
    checkout.refresh_from_db()
    assert checkout.language_code == language_code.lower()


def test_checkout_update_language_code_by_token(
    user_api_client,
    checkout_with_gift_card,
):
    language_code = "PL"
    checkout = checkout_with_gift_card

    variables = {"token": checkout.token, "languageCode": language_code}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE, variables
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutLanguageCodeUpdate"]
    assert not data["errors"]

    assert data["checkout"]["languageCode"] == language_code
    checkout.refresh_from_db()
    assert checkout.language_code == language_code.lower()


def test_checkout_update_language_code_neither_token_and_id_given(
    user_api_client,
    checkout_with_gift_card,
):
    language_code = "PL"
    variables = {"languageCode": language_code}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE, variables
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutLanguageCodeUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_update_language_code_both_token_and_id_given(
    user_api_client,
    checkout_with_gift_card,
):
    language_code = "PL"
    checkout = checkout_with_gift_card
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {
        "checkoutId": checkout_id,
        "token": checkout.token,
        "languageCode": language_code,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE, variables
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutLanguageCodeUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
