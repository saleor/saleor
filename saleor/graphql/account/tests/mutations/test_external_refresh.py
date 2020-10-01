import json
from unittest.mock import Mock

from ....tests.utils import get_graphql_content

MUTATION_EXTERNAL_REFRESH = """
    mutation externalRefresh($input: JSONString!){
        externalRefresh(input: $input){
            refreshedData
            accountErrors{
                field
                message
            }
        }
}
"""


def test_external_refresh_plugin_not_active(api_client, customer_user):
    variables = {"input": json.dumps({"refreshToken": "ABCD"})}
    response = api_client.post_graphql(MUTATION_EXTERNAL_REFRESH, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalRefresh"]
    assert json.loads(data["refreshedData"]) == {}


def test_external_refresh(api_client, customer_user, monkeypatch, rf):
    mocked_plugin_fun = Mock()
    expected_return = {"refreshToken": "XYZ123"}
    mocked_plugin_fun.return_value = expected_return
    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.external_refresh", mocked_plugin_fun
    )
    variables = {"input": json.dumps({"refreshToken": "ABCD"})}
    response = api_client.post_graphql(MUTATION_EXTERNAL_REFRESH, variables)
    content = get_graphql_content(response)
    data = content["data"]["externalRefresh"]
    assert json.loads(data["refreshedData"]) == expected_return
    assert mocked_plugin_fun.called
