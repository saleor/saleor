from ....tests.utils import get_graphql_content

APP_TOKEN_VERIFY_MUTATION = """
mutation AppTokenVerify($token: String!){
    appTokenVerify(token:$token){
        valid
    }
}
"""


def test_app_token_verify_valid_token(app, api_client):
    token = app.tokens.first().auth_token
    query = APP_TOKEN_VERIFY_MUTATION

    variables = {"token": token}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    assert content["data"]["appTokenVerify"]["valid"]


def test_app_token_verify_invalid_token(app, api_client):
    token = app.tokens.first().auth_token
    token += "incorrect"
    query = APP_TOKEN_VERIFY_MUTATION

    variables = {"token": token}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    assert not content["data"]["appTokenVerify"]["valid"]
