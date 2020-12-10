from datetime import datetime
from unittest.mock import Mock, patch

import pytz

from ....plugins.invoicing.utils import (
    chunk_products,
    generate_invoice_number,
    generate_invoice_pdf,
    get_product_limit_first_page,
    make_full_invoice_number,
)


def test_chunk_products(product):
    assert chunk_products([product] * 3, 3) == [[product] * 3]
    assert chunk_products([product] * 5, 3) == [[product] * 3, [product] * 2]
    assert chunk_products([product] * 8, 3) == [
        [product] * 3,
        [product] * 3,
        [product] * 2,
    ]


def test_get_product_limit_first_page(product):
    assert get_product_limit_first_page([product] * 3) == 3
    assert get_product_limit_first_page([product] * 4) == 4
    assert get_product_limit_first_page([product] * 16) == 4


@patch("saleor.plugins.invoicing.utils.HTML")
@patch("saleor.plugins.invoicing.utils.get_template")
@patch("saleor.plugins.invoicing.utils.os")
def test_generate_invoice_pdf_for_order(
    os_mock, get_template_mock, HTML_mock, fulfilled_order
):
    get_template_mock.return_value.render = Mock(return_value="<html></html>")
    os_mock.path.join.return_value = "test"

    content, creation = generate_invoice_pdf(fulfilled_order.invoices.first())

    get_template_mock.return_value.render.assert_called_once_with(
        {
            "invoice": fulfilled_order.invoices.first(),
            "creation_date": datetime.now(tz=pytz.utc).strftime("%d %b %Y"),
            "order": fulfilled_order,
            "font_path": "file://test",
            "products_first_page": list(fulfilled_order.lines.all()),
            "rest_of_products": [],
        }
    )
    HTML_mock.assert_called_once_with(
        string=get_template_mock.return_value.render.return_value
    )


def test_generate_invoice_number_invalid_numeration(fulfilled_order):
    invoice = fulfilled_order.invoices.last()
    invoice.number = "invalid/06/2020"
    invoice.save(update_fields=["number"])
    assert generate_invoice_number() == make_full_invoice_number()


def test_generate_invoice_number_no_existing_invoice(fulfilled_order):
    fulfilled_order.invoices.all().delete()
    assert generate_invoice_number() == make_full_invoice_number()
