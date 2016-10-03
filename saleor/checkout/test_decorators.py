from django.contrib.auth.models import AnonymousUser
from mock import MagicMock

from ..cart.models import Cart
from .core import get_or_empty_db_cart
from ..cart import decorators


def test_get_cart_from_request(rf, monkeypatch):
    request = rf.get('/')
    request.user = AnonymousUser()
    request.discounts = []
    empty_cart = Cart()
    qs_mock = MagicMock(return_value=[empty_cart])
    qs_mock.get.return_value = empty_cart
    qs_mock.open.return_value = qs_mock
    monkeypatch.setattr(Cart.objects, 'anonymous', lambda: qs_mock)
    cart = decorators.get_cart_from_request(request)
    assert cart.pk == empty_cart.pk


def test_get_or_create_db_cart():
    assert False  # FIXME


def test_assign_anonymous_cart():
    assert False  # FIXME


def test_get_or_empty_db_cart(rf, monkeypatch):
    request = rf.get('/')
    empty_cart = Cart()
    monkeypatch.setattr(decorators, 'get_cart_from_request',
                        lambda req: empty_cart)
    decorated_view = get_or_empty_db_cart(lambda req, cart: cart)
    view_cart = decorated_view(request)
    assert view_cart.pk == empty_cart.pk
