from unittest.mock import Mock

from ..dataloaders import WarehouseCountryCodeByChannelLoader


def test_warehouse_country_code_loader(channel_USD, shipping_zone):
    warehouse = channel_USD.shipping_zones.first().warehouses.first()
    request = Mock(dataloaders={})

    def with_country_code(country_code):
        assert country_code == warehouse.address.country.code

    WarehouseCountryCodeByChannelLoader(request).load(channel_USD.slug).then(
        with_country_code
    )


def test_warehouse_country_code_loader_fallback_to_settings_country_no_warehouse(
    channel_USD, settings
):
    # Change the DEFAULT_COUNTRY for test purpose to a country that is different than
    # fixtures' addresses.
    settings.DEFAULT_COUNTRY = "TH"
    request = Mock(dataloaders={})

    def with_country_code(country_code):
        assert country_code == "TH"

    WarehouseCountryCodeByChannelLoader(request).load(channel_USD.slug).then(
        with_country_code
    )
