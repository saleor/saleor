import graphene
from django.conf import settings

from ..account.types import AddressInput
from ..utils import get_user_country_context


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
