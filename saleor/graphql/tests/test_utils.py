import re

from django.test import override_settings
from graphql.utils import schema_printer

from ..utils import ALLOWED_ERRORS, INTERNAL_ERROR_MESSAGE, format_error
from .utils import get_graphql_content


def test_multiple_interface_separator_in_schema(api_client):
    query = """
    query __ApolloGetServiceDefinition__ {
        _service {
            sdl
        }
    }
    """
    response = api_client.post_graphql(query)

    content = get_graphql_content(response)
    sdl = content["data"]["_service"]["sdl"]
    comma_separated_interfaces = re.findall("implements (\\w+,) (\\w+)", sdl)
    ampersand_separated_interfaces = re.findall("implements (\\w+) & (\\w+)", sdl)
    assert not comma_separated_interfaces
    assert ampersand_separated_interfaces


def test_graphql_core_contains_patched_function():
    assert hasattr(schema_printer, "_print_object")


@override_settings(DEBUG=False)
def test_format_error_hides_internal_error_msg_in_production_mode():
    error = ValueError("Example error")
    result = format_error(error, ())
    assert result["message"] == INTERNAL_ERROR_MESSAGE


@override_settings(DEBUG=False)
def test_format_error_prints_allowed_errors():
    error_cls = ALLOWED_ERRORS[0]
    error = error_cls("Example error")
    result = format_error(error, ())
    assert result["message"] == str(error)


@override_settings(DEBUG=True)
def test_format_error_prints_internal_error_msg_in_debug_mode():
    error = ValueError("Example error")
    result = format_error(error, ())
    assert result["message"] == str(error)
