import re

from graphql.utils import schema_printer

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
