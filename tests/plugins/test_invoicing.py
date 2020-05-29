from datetime import datetime
from unittest.mock import Mock, patch
from uuid import UUID

from saleor.plugins.invoicing.utils import (
    chunk_products,
    generate_invoice_pdf,
    get_product_limit_first_page,
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


@patch("saleor.plugins.invoicing.utils.static_finders")
@patch("saleor.plugins.invoicing.utils.get_template")
@patch("saleor.plugins.invoicing.utils.default_storage")
@patch("saleor.plugins.invoicing.utils.os")
def test_generate_invoice_pdf_for_order(
    os_mock, storage_mock, get_template_mock, static_mock, fulfilled_order
):
    file_path = "/dev/null"
    static_mock.find.return_value = file_path
    storage_mock.save = Mock()
    get_template_mock.return_value.render = Mock(return_value="<html></html>")
    os_mock.path.join.return_value = "test"

    generate_invoice_pdf(fulfilled_order.invoices.first())

    get_template_mock.return_value.render.assert_called_once_with(
        {
            "invoice": fulfilled_order.invoices.first(),
            "creation_date": datetime.today().strftime("%d %b %Y"),
            "order": fulfilled_order,
            "logo_path": f"file://{file_path}",
            "font_path": "file://test",
            "products_first_page": list(fulfilled_order.lines.all()),
            "rest_of_products": [],
        }
    )

    file_name, extension = storage_mock.save.call_args[0][0].split(".")
    assert UUID(file_name, version=4)
    assert extension == "pdf"
