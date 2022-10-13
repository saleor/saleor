import json

from django.core.serializers.json import DjangoJSONEncoder


def get_graphql_content_from_response(response):
    return json.loads(response.content.decode("utf8"))


def get_graphql_content(response, *, ignore_errors: bool = False):
    """Gets GraphQL content from the response, and optionally checks if it
    contains any operating-related errors, eg. schema errors or lack of
    permissions.
    """
    content = get_graphql_content_from_response(response)
    if not ignore_errors:
        assert "errors" not in content, content["errors"]
    return content


def assert_no_permission(response):
    content = get_graphql_content_from_response(response)
    assert "errors" in content, content
    assert content["errors"][0]["extensions"]["exception"]["code"] == (
        "PermissionDenied"
    ), content["errors"]


def assert_negative_positive_decimal_value(response):
    content = get_graphql_content_from_response(response)
    assert "errors" in content, content
    assert "Value cannot be lower than 0." in content["errors"][0]["message"], content[
        "errors"
    ]


def assert_graphql_error_with_message(response, message):
    content = get_graphql_content_from_response(response)
    assert "errors" in content, content
    assert message in content["errors"][0]["message"], content["errors"]


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
