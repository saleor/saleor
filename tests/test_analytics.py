from saleor.core.analytics import report_order


def test_report_order(order_with_lines):
    report_order('', order_with_lines)
