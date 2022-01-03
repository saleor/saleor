from ..utils import get_countries_codes_list


def test_get_countries_codes_list(shipping_zones):
    # given
    fixture_countries_code_set = {zone.countries[0].code for zone in shipping_zones}

    # when
    countries_list_all = get_countries_codes_list()
    countries_list_false = get_countries_codes_list(False)
    countries_list_true = get_countries_codes_list(in_shipping_zones=True)

    # then
    assert (countries_list_true | countries_list_false) == countries_list_all
    assert countries_list_true == fixture_countries_code_set
    assert not any(country in countries_list_true for country in countries_list_false)
