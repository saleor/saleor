import re

import graphene
from django.conf import settings
from graphql.utils import schema_printer

from ..account.types import AddressInput
from ..utils import get_user_country_context
from .utils import get_graphql_content


def test_get_user_country_context_from_address_instance(address, address_other_country):
    destination_address = address
    company_address = address_other_country

    country = get_user_country_context(destination_address=destination_address)
    assert country == destination_address.country.code

    country = get_user_country_context(company_address=company_address)
    assert country == company_address.country.code

    country = get_user_country_context(
        destination_address=destination_address, company_address=company_address
    )
    assert country == destination_address.country.code

    country = get_user_country_context()
    assert country == settings.DEFAULT_COUNTRY


def test_get_user_country_from_address_input():
    class Query(graphene.ObjectType):
        field = graphene.Field(graphene.String, address=graphene.Argument(AddressInput))

        @staticmethod
        def resolve_field(_root, _info, address):
            return get_user_country_context(destination_address=address)

    schema = graphene.Schema(query=Query)
    result = schema.execute(
        """
        query {
            field(address: {country: US})
        }
        """
    )

    assert not result.errors
    assert result.data == {"field": "US"}


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
