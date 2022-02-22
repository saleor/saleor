import dataclasses
from decimal import Decimal

import pytest

from .....plugins.manager import get_plugins_manager
from .....plugins.models import PluginConfiguration
from ....interface import AddressData, PaymentLineData, PaymentLinesData
from ..api_types import get_api_config
from ..const import (
    FILL_MISSING_ADDRESS,
    MERCHANT_CODE,
    SHIPPING_COMPANY,
    SP_CODE,
    TERMINAL_ID,
    USE_SANDBOX,
)
from ..plugin import NPAtobaraiGatewayPlugin


@pytest.fixture
def np_atobarai_plugin(settings, monkeypatch, channel_USD):
    def fun(
        merchant_code="merchant-code",
        sp_code="sp-code",
        terminal_id="terminal-id",
        use_sandbox=True,
        fill_missing_address=True,
        shipping_company="50000",
        active=True,
    ):
        settings.PLUGINS = [
            "saleor.payment.gateways.np_atobarai.plugin.NPAtobaraiGatewayPlugin"
        ]

        configuration = [
            {"name": MERCHANT_CODE, "value": merchant_code},
            {"name": SP_CODE, "value": sp_code},
            {"name": TERMINAL_ID, "value": terminal_id},
            {"name": USE_SANDBOX, "value": use_sandbox},
            {"name": FILL_MISSING_ADDRESS, "value": fill_missing_address},
            {"name": SHIPPING_COMPANY, "value": shipping_company},
        ]
        PluginConfiguration.objects.create(
            identifier=NPAtobaraiGatewayPlugin.PLUGIN_ID,
            name=NPAtobaraiGatewayPlugin.PLUGIN_NAME,
            description="",
            active=active,
            channel=channel_USD,
            configuration=configuration,
        )

        manager = get_plugins_manager()
        return manager.plugins_per_channel[channel_USD.slug][0]

    return fun


def _resolve_lines():
    return PaymentLinesData(
        lines=[
            PaymentLineData(
                amount=Decimal("100.00"),
                product_name=f"Product Name {i}",
                product_sku=f"PRODUCT_SKU_{i}",
                variant_id=i,
                quantity=5,
            )
            for i in range(3)
        ],
        shipping_amount=Decimal("120.00"),
        voucher_amount=Decimal("-10.00"),
    )


@pytest.fixture
def np_address_data():
    return AddressData(
        first_name="John",
        last_name="Doe",
        company_name="",
        phone="+81 03-1234-5678",
        country="JP",
        postal_code="370-2625",
        country_area="群馬県",
        city="甘楽郡下仁田町",
        city_area="本宿",
        street_address_1="2-16-3",
        street_address_2="",
    )


@pytest.fixture
def np_payment_data(np_address_data, dummy_payment_data):
    return dataclasses.replace(
        dummy_payment_data,
        billing=np_address_data,
        shipping=np_address_data,
        _resolve_lines_data=_resolve_lines,
    )


@pytest.fixture
def config(np_atobarai_plugin):
    return get_api_config(np_atobarai_plugin().config.connection_params)
