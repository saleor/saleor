from ..models import Invoice
from ..notifications import get_invoice_payload


def test_collect_invoice_data_for_email(order):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    invoice = Invoice.objects.create(number=number, url=url, order=order)
    payload = get_invoice_payload(invoice)
    assert payload["id"] == invoice.id
    assert payload["number"] == number
    assert payload["download_url"] == url
