from datetime import datetime
from unittest.mock import patch

from ....invoice.models import Invoice
from ....plugins.invoicing.utils import generate_invoice_number
from ..utils import is_event_active_for_any_plugin


@patch("saleor.plugins.invoicing.utils.datetime")
def test_generate_invoice_number(datetime_mock, order):
    datetime_mock.now.return_value = datetime(2020, 7, 23, 12, 59, 59)
    Invoice.objects.create(order=order, number="5/07/2020")
    assert generate_invoice_number() == "6/07/2020"


@patch("saleor.plugins.invoicing.utils.datetime")
def test_generate_invoice_number_old_invoice(datetime_mock, order):
    datetime_mock.now.return_value = datetime(2020, 7, 23, 12, 59, 59)
    Invoice.objects.create(order=order, number="5/06/1991")
    assert generate_invoice_number() == "1/07/2020"


@patch("saleor.plugins.invoicing.utils.datetime")
def test_generate_invoice_number_no_existing_invoice(datetime_mock, order):
    datetime_mock.now.return_value = datetime(2020, 7, 23, 12, 59, 59)
    assert generate_invoice_number() == "1/07/2020"


class MockInvoicePluginActive:
    active = True

    @staticmethod
    def is_event_active(_):
        return True


class MockInvoicePluginInactive:
    active = False

    @staticmethod
    def is_event_active(_):
        return True


def test_is_event_active_for_any_plugin_plugin_active():
    result = is_event_active_for_any_plugin(
        "event", [MockInvoicePluginActive(), MockInvoicePluginInactive()]
    )
    assert result is True


def test_is_event_active_for_any_plugin_plugin_inactive():
    result = is_event_active_for_any_plugin(
        "event", [MockInvoicePluginInactive(), MockInvoicePluginInactive()]
    )
    assert result is False
