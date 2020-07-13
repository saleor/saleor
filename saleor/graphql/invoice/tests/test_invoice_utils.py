from datetime import datetime
from unittest.mock import patch

from ....invoice.models import Invoice
from ....plugins.invoicing.utils import generate_invoice_number


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
