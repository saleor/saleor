from prices import Price

from .models import Order


def test_total_property():
    order = Order(total_net=20, total_tax=5)
    assert order.total.gross == 25
    assert order.total.tax == 5
    assert order.total.net == 20


def test_total_property_empty_value():
    order = Order(total_net=None, total_tax=None)
    assert order.total is None


def test_total_setter():
    price = Price(net=10, gross=20, currency='USD')
    order = Order()
    order.total = price
    assert order.total_net.net == 10
    assert order.total_tax.net == 10
