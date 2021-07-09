from .....app.models import AppToken
from ....tests.utils import get_graphql_content

APP_TOKEN_VERIFY_MUTATION = """
mutation AppTokenVerify($token: String!){
    appTokenVerify(token:$token){
        valid
    }
}
"""


def test_app_token_verify_valid_token(app, api_client):
    _token_obj, token = AppToken.objects.create_app_token(app=app)
    query = APP_TOKEN_VERIFY_MUTATION

    variables = {"token": token}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    assert content["data"]["appTokenVerify"]["valid"]


def test_app_token_verify_valid_token_and_inactive_app(app, api_client):
    app.is_active = False
    app.save(update_fields=["is_active"])

    _token_obj, token = AppToken.objects.create_app_token(app=app)
    query = APP_TOKEN_VERIFY_MUTATION

    variables = {"token": token}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    assert not content["data"]["appTokenVerify"]["valid"]


def test_app_token_verify_invalid_token(app, api_client):
    _token_obj, token = AppToken.objects.create_app_token(app=app)
    token += "incorrect"
    query = APP_TOKEN_VERIFY_MUTATION

    variables = {"token": token}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    assert not content["data"]["appTokenVerify"]["valid"]
