from dataclasses import asdict
from urllib.parse import urljoin

import pytest

from ....core.taxes import TaxError
from ....order import OrderEvents
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
        username_or_account="",
        password_or_license="",
        use_sandbox=True,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-601",
        from_country="PL",
    )
    request_data = get_order_request_data(order_with_lines, config, tax_included=True)

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
        username_or_account="",
        password_or_license="",
        use_sandbox=True,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-601",
        from_country="PL",
    )
    request_data = get_order_request_data(order_with_lines, config, tax_included=True)

    transaction_url = urljoin(
        get_api_url(config.use_sandbox), "transactions/createoradjust"
    )
    api_post_request_task(
        transaction_url, request_data, asdict(config), order_with_lines.id
    )

    expected_event_msg = f"Order sent to Avatax. Order ID: {order_with_lines.id}"
    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    assert event.parameters["message"] == expected_event_msg


def test_api_post_request_task_missing_response(
    order_with_lines, shipping_zone, monkeypatch
):
    mock_api_post_request = {"error": {"message": "Wrong credentials"}}
    monkeypatch.setattr(
        "saleor.plugins.avatax.tasks.api_post_request", lambda *_: mock_api_post_request
    )

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-601",
        from_country="PL",
    )
    request_data = get_order_request_data(order_with_lines, config, tax_included=True)

    transaction_url = urljoin(
        get_api_url(config.use_sandbox), "transactions/createoradjust"
    )
    with pytest.raises(TaxError):
        api_post_request_task(
            transaction_url, request_data, asdict(config), order_with_lines.pk
        )

    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    expected_msg = "Unable to send order to Avatax. Wrong credentials"
    assert event.parameters["message"] == expected_msg


def test_api_post_request_task_order_doesnt_have_any_lines_with_taxes_to_calculate(
    order_with_lines, shipping_zone, monkeypatch
):
    mock_api_post_request = {"error": {"message": "Wrong credentials"}}
    monkeypatch.setattr(
        "saleor.plugins.avatax.tasks.api_post_request", lambda *_: mock_api_post_request
    )

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-601",
        from_country="PL",
    )
    request_data = {}

    transaction_url = urljoin(
        get_api_url(config.use_sandbox), "transactions/createoradjust"
    )

    api_post_request_task(
        transaction_url, request_data, asdict(config), order_with_lines.pk
    )

    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.get()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    expected_msg = "The order doesn't have any line which should be sent to Avatax."
    assert event.parameters["message"] == expected_msg
