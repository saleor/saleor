from dataclasses import asdict
from urllib.parse import urljoin

import pytest

from saleor.order import OrderEvents

from .. import AvataxConfiguration, get_api_url, get_order_request_data
from ..tasks import api_post_request_task


@pytest.mark.vcr
def test_api_post_request_task_sends_request(
    order_with_lines, address_usa, shipping_zone, site_settings
):
    method = shipping_zone.shipping_methods.get()
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = method.name
    order_with_lines.shipping_method = method
    order_with_lines.save()

    site_settings.company_address = address_usa
    site_settings.save()

    config = AvataxConfiguration(
        username_or_account="2000134479",
        password_or_license="AEBCF1A2FBF932D5",
        use_sandbox=False,
    )
    request_data = get_order_request_data(order_with_lines, config)

    transaction_url = urljoin(
        get_api_url(config.use_sandbox), "transactions/createoradjust"
    )
    api_post_request_task(
        transaction_url, request_data, asdict(config), order_with_lines.id
    )


@pytest.mark.vcr
def test_api_post_request_task_creates_order_event(
    order_with_lines, address_usa, shipping_zone, site_settings
):
    method = shipping_zone.shipping_methods.get()
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = method.name
    order_with_lines.shipping_method = method
    order_with_lines.save()

    site_settings.company_address = address_usa
    site_settings.save()

    config = AvataxConfiguration(
        username_or_account="2000134479",
        password_or_license="AEBCF1A2FBF932D5",
        use_sandbox=False,
    )
    request_data = get_order_request_data(order_with_lines, config)

    transaction_url = urljoin(
        get_api_url(config.use_sandbox), "transactions/createoradjust"
    )
    api_post_request_task(
        transaction_url, request_data, asdict(config), order_with_lines.id
    )
    order_with_lines.refresh_from_db()
    expected_event_msg = f"Order sent to Avatax. Order ID: {order_with_lines.token}"
    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    assert event.parameters["message"] == expected_event_msg
