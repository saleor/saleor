from decimal import Decimal
from unittest import mock

from ..analytics import get_order_payloads, report_order, report_view


def test_get_order_payloads(order_with_lines):
    order = order_with_lines

    generator = get_order_payloads(order)
    data = list(generator)
    assert len(data) == order.lines.count() + 1

    transaction = data[0]
    assert transaction["ti"] == order.pk
    assert transaction["cu"] == order.total.currency
    assert Decimal(transaction["tr"]) == order.total.gross.amount
    assert Decimal(transaction["tt"]) == order.total.tax.amount
    assert Decimal(transaction["ts"]) == order.shipping_price.net.amount

    for i, line in enumerate(order):
        item = data[i + 1]
        assert item["ti"] == order.pk
        assert item["in"] == line.variant.display_product()
        assert item["ic"] == line.product_sku
        assert item["iq"] == str(int(line.quantity))
        assert item["cu"] == line.unit_price.currency
        assert Decimal(item["ip"]) == line.unit_price.gross.amount


@mock.patch("google_measurement_protocol.report")
def test_report_order_has_no_errors(mocked_ga_report, order_with_lines, settings):
    settings.GOOGLE_ANALYTICS_TRACKING_ID = "ga_id"
    report_order("dummy_client_id", order_with_lines)
    mocked_ga_report.assert_called_once()


@mock.patch("google_measurement_protocol.report")
def test_get_view_payloads(mocked_ga_report, settings):
    settings.GOOGLE_ANALYTICS_TRACKING_ID = "ga_id"
    headers = {"HTTP_HOST": "getsaleor.com", "HTTP_REFERER": "example.com"}
    report_view("dummy_client_id", "/test-path/", "en-us", headers)
    expected_payload = [
        {
            "t": "pageview",
            "dp": "/test-path/",
            "dh": "getsaleor.com",
            "dr": "example.com",
            "ul": "en-us",
        }
    ]
    mocked_ga_report.assert_called_once_with(
        "ga_id", "dummy_client_id", expected_payload, extra_headers={}
    )
