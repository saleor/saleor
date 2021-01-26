from django.conf import settings

from ..utils import get_user_country_context


def test_get_user_country_context(address, address_other_country):
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
