import json

from django.middleware.csrf import _get_new_csrf_token
from freezegun import freeze_time

from .....account.error_codes import AccountErrorCode
from .....core.jwt import create_access_token, create_refresh_token, jwt_decode
from ....tests.utils import get_graphql_content
from .test_token_refresh import MUTATION_TOKEN_REFRESH

MUTATION_DEACTIVATE_ALL_USER_TOKENS = """
mutation{
  tokensDeactivateAll{
    accountErrors{
      field
      message
      code
    }
  }
}

"""


@freeze_time("2020-03-18 12:00:00")
def test_deactivate_all_user_tokens(customer_user, user_api_client):
    token = create_access_token(customer_user)
    jwt_key = customer_user.jwt_token_key

    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})

    user_api_client.token = token
    user_api_client.post_graphql(MUTATION_DEACTIVATE_ALL_USER_TOKENS)
    customer_user.refresh_from_db()

    new_token = create_access_token(customer_user)
    new_refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})
    # the mutation changes the parameter of jwt token, which confirms if jwt token is
    # valid or not
    assert jwt_decode(token)["token"] != jwt_decode(new_token)["token"]
    assert jwt_decode(refresh_token)["token"] != jwt_decode(new_refresh_token)["token"]
    assert jwt_key != customer_user.jwt_token_key


def test_deactivate_all_user_tokens_access_token(user_api_client, customer_user):
    token = create_access_token(customer_user)
    user_api_client.token = token
    response = user_api_client.post_graphql(MUTATION_DEACTIVATE_ALL_USER_TOKENS)
    content = get_graphql_content(response)
    errors = content["data"]["tokensDeactivateAll"]["accountErrors"]
    assert not errors

    query = "{me { id }}"
    response = user_api_client.post_graphql(query)
    content = json.loads(response.content.decode("utf8"))
    assert len(content["errors"]) == 1
    assert content["errors"][0]["extensions"]["exception"]["code"] == (
        "InvalidTokenError"
    )

    assert content["data"]["me"] is None


def test_deactivate_all_user_token_refresh_token(
    api_client, user_api_client, customer_user
):
    user_api_client.token = create_access_token(customer_user)
    create_refresh_token(customer_user)
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(customer_user, {"csrfToken": csrf_token})

    response = user_api_client.post_graphql(MUTATION_DEACTIVATE_ALL_USER_TOKENS)
    content = get_graphql_content(response)
    errors = content["data"]["tokensDeactivateAll"]["accountErrors"]
    assert not errors

    variables = {"token": refresh_token, "csrf_token": csrf_token}
    response = api_client.post_graphql(MUTATION_TOKEN_REFRESH, variables)
    content = get_graphql_content(response)

    data = content["data"]["tokenRefresh"]
    errors = data["accountErrors"]

    assert data["token"] is None
    assert len(errors) == 1

    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name
