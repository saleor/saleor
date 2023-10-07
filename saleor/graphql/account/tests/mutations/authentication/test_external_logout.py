import json
from unittest.mock import Mock

from .....tests.utils import get_graphql_content

MUTATION_EXTERNAL_LOGOUT = """
    mutation externalLogout($pluginId: String!, $input: JSONString!){
        externalLogout(pluginId: $pluginId, input: $input){
            logoutData
            errors{
                field
                message
            }
        }
}
"""


def test_external_logout_plugin_not_active(api_client, customer_user):
    variables = {
        "pluginId": "pluginID1",
        "input": json.dumps({"logoutRedirect": "ABCD"}),
    }
    response = api_client.post_graphql(MUTATION_EXTERNAL_LOGOUT, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalLogout"]
    assert json.loads(data["logoutData"]) == {}


def test_external_logout(api_client, customer_user, monkeypatch, rf):
    mocked_plugin_fun = Mock()
    expected_return = {"logoutRedirectParam": "AVC"}
    mocked_plugin_fun.return_value = expected_return
    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.external_logout", mocked_plugin_fun
    )
    variables = {"pluginId": "pluginID1", "input": json.dumps({"logoutParam": "ABCD"})}
    response = api_client.post_graphql(MUTATION_EXTERNAL_LOGOUT, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalLogout"]
    assert json.loads(data["logoutData"]) == expected_return
    assert mocked_plugin_fun.called
