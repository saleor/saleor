import pytest
from prices import Money, TaxedMoney

from ..plugin import AvataxExcisePlugin
from ....manager import get_plugins_manager
from ....models import PluginConfiguration
from .....core.prices import quantize_price
from .....account.models import Address
from .....warehouse.models import Warehouse


@pytest.fixture
def plugin_configuration(db):
    def set_configuration(
        username="api_user",
        password="test",
        sandbox=True,
        company_id="1337",
    ):
        data = {
            "active": True,
            "name": AvataxExcisePlugin.PLUGIN_NAME,
            "configuration": [
                {"name": "Username", "value": username},
                {"name": "Password", "value": password},
                {"name": "Use sandbox", "value": sandbox},
                {"name": "Company ID", "value": company_id},
            ],
        }
        configuration = PluginConfiguration.objects.create(
            identifier=AvataxExcisePlugin.PLUGIN_ID, **data
        )
        return configuration

    return set_configuration


@pytest.fixture
def address_usa_tx():
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        street_address_1="1100 Congress Ave",
        city="Austin",
        postal_code="78701",
        country_area="TX",
        country="US",
        phone="",
    )


@pytest.fixture
def warehouse(address_usa_tx, shipping_zone):
    warehouse = Warehouse.objects.create(
        address=address_usa_tx,
        name="Example Warehouse",
        slug="example-warehouse",
        email="test@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.save()
    return warehouse


@pytest.mark.vcr(filter_headers=["Authorization"])
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (True, "15.00", "15.00", True),  # TODO real values
    ],
)
def test_calculate_checkout_line_total(
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    discount_info,
    checkout_with_item,
    address_usa_tx,
    address_usa,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(
        plugins=["saleor.plugins.avatax.excise.plugin.AvataxExcisePlugin"]
    )

    checkout_with_item.shipping_address = address_usa_tx
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}  # TODO consider adding ATE fields here
    product.save()
    product.product_type.save()
    discounts = [discount_info] if with_discount else None
    channel = checkout_with_item.channel
    channel_listing = line.variant.channel_listings.get(channel=channel)
    total = manager.calculate_checkout_line_total(
        checkout_with_item,
        line,
        line.variant,
        line.variant.product,
        [],
        checkout_with_item.shipping_address,
        channel,
        channel_listing,
        discounts,
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )
