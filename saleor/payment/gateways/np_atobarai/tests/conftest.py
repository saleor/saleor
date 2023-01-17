import dataclasses
from decimal import Decimal
from unittest.mock import patch

import pytest

from .....order.actions import create_refund_fulfillment
from .....plugins.manager import get_plugins_manager
from .....plugins.models import PluginConfiguration
from .....tests.fixtures import recalculate_order
from ....interface import AddressData, PaymentLineData, PaymentLinesData
from ..api_types import get_api_config
from ..const import (
    FILL_MISSING_ADDRESS,
    MERCHANT_CODE,
    SHIPPING_COMPANY,
    SKU_AS_NAME,
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
        sku_as_name=False,
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
            {"name": SKU_AS_NAME, "value": sku_as_name},
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


@pytest.fixture
def payment_lines_data(order_with_lines):
    return PaymentLinesData(
        lines=[
            PaymentLineData(
                amount=line.unit_price_gross_amount,
                product_name=f"{line.product_name} {line.variant_name}",
                product_sku=line.product_sku,
                variant_id=line.variant_id,
                quantity=line.quantity,
            )
            for line in order_with_lines.lines.all()
        ],
        shipping_amount=order_with_lines.shipping_price_gross_amount,
        voucher_amount=(
            order_with_lines.total_gross_amount
            - order_with_lines.undiscounted_total_gross_amount
        ),
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
        metadata={},
        private_metadata={},
    )


@pytest.fixture
def np_payment_data(np_address_data, dummy_payment_data, payment_lines_data):
    return dataclasses.replace(
        dummy_payment_data,
        billing=np_address_data,
        shipping=np_address_data,
        amount=Decimal("0.00"),
        _resolve_lines_data=lambda: payment_lines_data,
    )


@pytest.fixture
def config(np_atobarai_plugin):
    return get_api_config(np_atobarai_plugin().config.connection_params)


@pytest.fixture
def payment_dummy(payment_dummy, order_with_lines):
    payment_dummy.captured_amount = order_with_lines.total_gross_amount
    payment_dummy.save(update_fields=["captured_amount"])
    return payment_dummy


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.shipping_price_net_amount = Decimal("5.55")
    order_with_lines.shipping_price_gross_amount = Decimal("5.55") * Decimal("1.34")
    order_with_lines.shipping_tax_rate = Decimal("1.34")

    order_with_lines.save()

    recalculate_order(order_with_lines)

    return order_with_lines


@pytest.fixture
def order_lines(order_with_lines):
    return list(order_with_lines.lines.all())


@pytest.fixture
def create_refund(payment_dummy):
    def factory(
        order,
        order_lines=None,
        fulfillment_lines=None,
        manual_refund_amount=None,
        refund_shipping_costs=False,
    ):
        def mocked_refund(payment, manager, channel_slug, amount, refund_data):
            payment.captured_amount -= amount
            payment.save(update_fields=["captured_amount"])

        with patch("saleor.order.actions.gateway.refund", side_effect=mocked_refund):
            return create_refund_fulfillment(
                user=None,
                app=None,
                order=order,
                payment=payment_dummy,
                transactions=[],
                order_lines_to_refund=order_lines or [],
                fulfillment_lines_to_refund=fulfillment_lines or [],
                manager=get_plugins_manager(),
                amount=manual_refund_amount,
                refund_shipping_costs=refund_shipping_costs,
            )

    return factory
