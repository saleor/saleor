from django_countries import countries

from ..utils import get_countries_codes_list


def test_get_countries_codes_list(shipping_zones):
    # given
    all_countries = {country[0] for country in countries}

    # when
    countries_list_all = get_countries_codes_list()

    # then
    assert countries_list_all == all_countries


def test_get_countries_codes_list_true(shipping_zones):
    # given
    fixture_countries_code_set = {zone.countries[0].code for zone in shipping_zones}

    # when
    countries_list_true = get_countries_codes_list(attached_to_shipping_zones=True)

    # then
    assert countries_list_true == fixture_countries_code_set


def test_get_countries_codes_list_false(shipping_zones):
    # given
    fixture_countries_code_set = {zone.countries[0].code for zone in shipping_zones}

    # when
    countries_list_false = get_countries_codes_list(False)

    # then
    assert not any(
        country in countries_list_false for country in fixture_countries_code_set
    )
