from ....tests.utils import get_graphql_content

APP_TOKEN_VERIFY_MUTATION = """
mutation AppTokenVerify($token: String!){
    appTokenVerify(token:$token){
        valid
        errors {
          field
          message
          code
        }
    }
}
"""


def test_app_token_verify_valid_token(app, api_client):
    # given
    _, token = app.tokens.create()
    query = APP_TOKEN_VERIFY_MUTATION
    variables = {"token": token}

    # when
    response = api_client.post_graphql(query, variables=variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["appTokenVerify"]["valid"]


def test_app_token_verify_invalid_token(app, api_client):
    # given
    _, token = app.tokens.create()
    token += "incorrect"
    query = APP_TOKEN_VERIFY_MUTATION
    variables = {"token": token}

    # when
    response = api_client.post_graphql(query, variables=variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["appTokenVerify"]["valid"]


def test_app_token_verify_app_turned_off(app, api_client):
    # given
    app.is_active = False
    app.save()
    _, token = app.tokens.create()
    query = APP_TOKEN_VERIFY_MUTATION
    variables = {"token": token}

    # when
    response = api_client.post_graphql(query, variables=variables)

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["appTokenVerify"]
    assert app_data["valid"] is False
    assert not app_data["errors"]


def test_app_token_verify_removed_app(removed_app, api_client):
    # given
    _, token = removed_app.tokens.create()
    query = APP_TOKEN_VERIFY_MUTATION
    variables = {"token": token}

    # when
    response = api_client.post_graphql(query, variables=variables)

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["appTokenVerify"]
    assert app_data["valid"] is False
    assert not app_data["errors"]
