import json

from django.core.serializers.json import DjangoJSONEncoder

from saleor.graphql.core.utils import snake_to_camel_case
from saleor.menu.utils import get_menu_item_as_dict


def _get_graphql_content_from_response(response):
    return json.loads(response.content.decode("utf8"))


def get_graphql_content(response, *, ignore_errors: bool = False):
    """Gets GraphQL content from the response, and optionally checks if it
    contains any operating-related errors, eg. schema errors or lack of
    permissions.
    """
    content = _get_graphql_content_from_response(response)
    if not ignore_errors:
        assert "errors" not in content, content["errors"]
    return content


def assert_no_permission(response):
    content = _get_graphql_content_from_response(response)
    assert "errors" in content, content
    assert content["errors"][0]["message"] == (
        "You do not have permission to perform this action"
    ), content["errors"]


def get_multipart_request_body(query, variables, file, file_name):
    """Create request body for multipart GraphQL requests.

    Multipart requests are different than standard GraphQL requests, because
    of additional 'operations' and 'map' keys.
    """
    return {
        "operations": json.dumps(
            {"query": query, "variables": variables}, cls=DjangoJSONEncoder
        ),
        "map": json.dumps({file_name: ["variables.file"]}, cls=DjangoJSONEncoder),
        file_name: file,
    }


def convert_dict_keys_to_camel_case(d):
    """Changes dict fields from d[field_name] to d[fieldName].

    Useful when dealing with dict data such as address that need to be parsed
    into graphql input.
    """
    data = {}
    for k, v in d.items():
        new_key = snake_to_camel_case(k)
        data[new_key] = d[k]
    return data


def menu_item_to_json(menu_item):
    """Transforms a menu item to a JSON representation as used in the storefront."""
    item_json = get_menu_item_as_dict(menu_item)
    item_json["child_items"] = []
    return item_json
