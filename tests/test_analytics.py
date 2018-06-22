from decimal import Decimal

from saleor.core.analytics import (
    get_order_payloads, get_view_payloads, report_order, report_view)


def test_get_order_payloads(order_with_lines):
    order = order_with_lines

    generator = get_order_payloads(order)
    data = list(generator)
    assert len(data) == order.lines.count() + 1

    transaction = data[0]
    assert transaction['ti'] == order.pk
    assert transaction['cu'] == order.total.currency
    assert Decimal(transaction['tr']) == order.total.gross.amount
    assert Decimal(transaction['tt']) == order.total.tax.amount
    assert Decimal(transaction['ts']) == order.shipping_price.net.amount

    for i, line in enumerate(order):
        item = data[i + 1]
        assert item['ti'] == order.pk
        assert item['in'] == line.product_name
        assert item['ic'] == line.product_sku
        assert item['iq'] == str(int(line.quantity))
        assert item['cu'] == line.unit_price.currency
        assert Decimal(item['ip']) == line.unit_price.gross.amount


def test_report_order_has_no_errors(order_with_lines):
    report_order('', order_with_lines)


def test_get_view_payloads():
    headers = {'HTTP_HOST': 'getsaleor.com', 'HTTP_REFERER': 'example.com'}
    generator = get_view_payloads('/test-path/', 'en-us', headers)
    data = list(generator)[0]
    assert data['dp'] == '/test-path/'
    assert data['dh'] == 'getsaleor.com'
    assert data['dr'] == 'example.com'
    assert data['ul'] == 'en-us'


def test_report_view_has_no_errors():
    headers = {'HTTP_HOST': 'getsaleor.com', 'HTTP_REFERER': 'example.com'}
    report_view('', '/test-path/', 'en-us', headers)
