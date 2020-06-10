from .....account.error_codes import AccountErrorCode
from .....core.jwt import create_access_token
from ....tests.utils import get_graphql_content

MUTATION_TOKEN_VERIFY = """
    mutation tokenVerify($token: String!){
        tokenVerify(token: $token){
            isValid
            user{
              email
            }
            accountErrors{
              code
            }
        }
    }
"""


def test_verify_token(api_client, customer_user):
    variables = {"token": create_access_token(customer_user)}
    response = api_client.post_graphql(MUTATION_TOKEN_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["tokenVerify"]
    assert data["isValid"] is True
    user_email = content["data"]["tokenVerify"]["user"]["email"]
    assert customer_user.email == user_email


def test_verify_token_incorrect_token(api_client):
    variables = {"token": "incorrect_token"}
    response = api_client.post_graphql(MUTATION_TOKEN_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["tokenVerify"]
    errors = data["accountErrors"]
    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_DECODE_ERROR.name
    assert data["isValid"] is False
    assert not data["user"]


def test_verify_token_invalidated_by_user(api_client, customer_user):
    variables = {"token": create_access_token(customer_user)}
    customer_user.jwt_token_key = "new token"
    customer_user.save()
    response = api_client.post_graphql(MUTATION_TOKEN_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["tokenVerify"]
    errors = data["accountErrors"]

    assert data["isValid"] is False
    assert len(errors) == 1
    assert errors[0]["code"] == AccountErrorCode.JWT_INVALID_TOKEN.name
