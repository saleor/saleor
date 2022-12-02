import json
from unittest.mock import Mock

from ....tests.utils import get_graphql_content

MUTATION_EXTERNAL_VERIFY = """
    mutation externalVerify($pluginId: String!, $input: JSONString!){
        externalVerify(pluginId:$pluginId, input: $input){
            verifyData
            user{
               email
            }
            isValid
            errors{
                field
                message
            }
        }
}
"""


def test_external_verify_plugin_not_active(api_client, customer_user):
    variables = {"pluginId": "pluginId3", "input": json.dumps({"token": "ABCD"})}
    response = api_client.post_graphql(MUTATION_EXTERNAL_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalVerify"]
    assert json.loads(data["verifyData"]) == {}


def test_external_verify(api_client, customer_user, monkeypatch, rf):
    mocked_plugin_fun = Mock()
    expected_return = customer_user, {"data": "XYZ123"}
    mocked_plugin_fun.return_value = expected_return
    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.external_verify", mocked_plugin_fun
    )
    variables = {"pluginId": "pluginId3", "input": json.dumps({"token": "ABCD"})}
    response = api_client.post_graphql(MUTATION_EXTERNAL_VERIFY, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalVerify"]
    user_email = content["data"]["externalVerify"]["user"]["email"]
    assert json.loads(data["verifyData"]) == {"data": "XYZ123"}
    assert user_email == customer_user.email
    assert mocked_plugin_fun.called
