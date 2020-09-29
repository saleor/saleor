import json
from unittest.mock import Mock

from ....tests.utils import get_graphql_content

MUTATION_EXTERNAL_AUTHENTICATION = """
    mutation externalAuthentication($input: JSONString!){
        externalAuthentication(input: $input){
            authenticationData
            accountErrors{
                field
                message
            }
        }
}
"""


def test_external_authentication_plugin_not_active(api_client, customer_user):
    variables = {"input": json.dumps({"redirectUrl": "http://locahost:3000/"})}
    response = api_client.post_graphql(MUTATION_EXTERNAL_AUTHENTICATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalAuthentication"]
    assert json.loads(data["authenticationData"]) == {}


def test_external_authentication(api_client, customer_user, monkeypatch, rf):
    mocked_plugin_fun = Mock()
    expected_return = {"authorizationUrl": "https://ouath-provider/url"}
    mocked_plugin_fun.return_value = expected_return
    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.external_authentication",
        mocked_plugin_fun,
    )
    variables = {"input": json.dumps({"redirectUrl": "http://locahost:3000/"})}
    response = api_client.post_graphql(MUTATION_EXTERNAL_AUTHENTICATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalAuthentication"]
    assert json.loads(data["authenticationData"]) == expected_return
    assert mocked_plugin_fun.called
