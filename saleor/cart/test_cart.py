from __future__ import unicode_literals
from decimal import Decimal
import json

from prices import Price
import pytest
from mock import Mock, MagicMock
from satchless.item import InsufficientStock

from django.core.exceptions import ObjectDoesNotExist
from .models import Cart
from .context_processors import cart_counter
from . import forms
from . import utils
from . import views
from ..product.models import Product, ProductVariant




@pytest.fixture
def cart(db):
    return Cart.objects.create()


@pytest.fixture
def product(db):
    product = Product(name='Big Ship', price=Price(10, currency='USD'),
                      weight=Decimal(123))
    product.save()
    return product

@pytest.fixture
def variant(db, monkeypatch, product):
    variant = ProductVariant(name='Big Ship', product=product)
    variant.save()
    monkeypatch.setattr('saleor.product.models.ProductVariant.check_quantity',
                        Mock())
    return variant


def test_adding_without_checking(cart, variant):
    cart.add(variant, 1000, check_quantity=False)
    assert len(cart) == 1


def test_adding_zero_quantity(cart, variant):
    cart.add(variant, 0)
    assert len(cart) == 0


def test_adding_same_variant(cart, variant):
    cart.add(variant, 1)
    cart.add(variant, 2)
    price_total = 10 * 3
    assert len(cart) == 1
    assert cart.count() == {'total_quantity': 3}
    assert cart.get_total().gross == price_total


def test_replacing_same_variant(cart, variant):
    cart.add(variant, 1, replace=True)
    cart.add(variant, 2, replace=True)
    assert len(cart) == 1
    assert cart.count() == {'total_quantity': 2}


def test_adding_invalid_quantity(cart, variant):
    with pytest.raises(ValueError):
        cart.add(variant, -1)


def test_getting_line(cart, variant):
    assert cart.get_line(variant) is None

    line = cart.create_line(variant, 1, None)
    assert line == cart.get_line(variant)


def test_change_status(cart):
    with pytest.raises(ValueError):
        cart.change_status('spanish inquisition')

    cart.change_status(Cart.OPEN)
    assert cart.status == Cart.OPEN
    cart.change_status(Cart.CANCELED)
    assert cart.status == Cart.CANCELED


def test_shipping_detection(cart, variant):
    assert not cart.is_shipping_required()
    cart.add(variant, 1, replace=True)
    assert cart.is_shipping_required()


def test_cart_counter(db, monkeypatch):
    monkeypatch.setattr('saleor.cart.context_processors.get_cart_from_request',
                        Mock(return_value=Mock(quantity=4)))
    ret = cart_counter(Mock())
    assert ret == {'cart_counter': 4}


def test_get_product_variants_and_prices():
    product = Mock(product_id=1, id=1)
    cart = MagicMock()
    cart.__iter__.return_value = [
        Mock(quantity=1, product=product,
             get_price_per_item=Mock(return_value=10))]
    products = list(utils.get_product_variants_and_prices(cart, product))
    assert products == [(product, 10)]


def test_get_user_open_cart_token():
    cart = Mock()
    carts = []
    user = Mock(carts=Mock(open=Mock(return_value=Mock(
        values_list=Mock(return_value=carts)))))
    assert utils.get_user_open_cart_token(user) is None

    carts.append(cart)
    user = Mock(carts=Mock(open=Mock(return_value=Mock(
        values_list=Mock(return_value=carts)))))
    assert utils.get_user_open_cart_token(user) == cart


def test_contains_unavailable_products():
    missing_product = Mock(
        check_quantity=Mock(side_effect=InsufficientStock('')))
    cart = MagicMock()
    cart.__iter__.return_value = [Mock(product=missing_product)]
    assert utils.contains_unavailable_products(cart)

    product = Mock(check_quantity=Mock())
    cart.__iter__.return_value = [Mock(product=product)]
    assert not utils.contains_unavailable_products(cart)


def test_check_product_availability_and_warn(monkeypatch, cart, variant):
    cart.add(variant, 1)
    monkeypatch.setattr('django.contrib.messages.warning',
                        Mock(warning=Mock()))
    monkeypatch.setattr('saleor.cart.utils.contains_unavailable_products',
                        Mock(return_value=False))

    utils.check_product_availability_and_warn(MagicMock(), cart)
    assert len(cart) == 1

    monkeypatch.setattr('saleor.cart.utils.contains_unavailable_products',
                        Mock(return_value=True))
    monkeypatch.setattr('saleor.cart.utils.remove_unavailable_products',
                        lambda c: c.add(variant, 0, replace=True))

    utils.check_product_availability_and_warn(MagicMock(), cart)
    assert len(cart) == 0


def test_add_to_cart_form():
    cart_lines = []
    cart = Mock(add=lambda product, quantity: cart_lines.append(product),
                get_line=Mock(return_value=Mock(quantity=1)))
    data = {'quantity': 1}
    form = forms.AddToCartForm(data=data, cart=cart, product=Mock())

    product_variant = Mock(check_quantity=Mock(return_value=None))
    form.get_variant = Mock(return_value=product_variant)

    assert form.is_valid()
    form.save()
    assert cart_lines == [product_variant]

    with pytest.raises(NotImplementedError):
        data = {'quantity': 1}
        form = forms.AddToCartForm(data=data, cart=cart, product=Mock())
        form.is_valid()


def test_form_when_variant_does_not_exist():
    cart_lines = []
    cart = Mock(add=lambda product, quantity: cart_lines.append(Mock()),
                get_line=Mock(return_value=Mock(quantity=1)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    form.get_variant = Mock(side_effect=ObjectDoesNotExist)
    assert not form.is_valid()


def test_add_to_cart_form_when_empty_stock():
    cart_lines = []
    cart = Mock(add=lambda product, quantity: cart_lines.append(Mock()),
                get_line=Mock(return_value=Mock(quantity=1)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    exception_mock = InsufficientStock(
        Mock(get_stock_quantity=Mock(return_value=1)))
    product_variant = Mock(check_quantity=Mock(side_effect=exception_mock))
    form.get_variant = Mock(return_value=product_variant)
    assert not form.is_valid()


def test_add_to_cart_form_when_insufficient_stock():
    cart_lines = []
    cart = Mock(add=lambda product, quantity: cart_lines.append(product),
                get_line=Mock(return_value=Mock(quantity=1)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    exception_mock = InsufficientStock(
        Mock(get_stock_quantity=Mock(return_value=4)))
    product_variant = Mock(check_quantity=Mock(side_effect=exception_mock))
    form.get_variant = Mock(return_value=product_variant)
    assert not form.is_valid()


def test_replace_cart_line_form(cart, variant):
    initial_quantity = 1
    replaced_quantity = 4

    cart.add(variant, initial_quantity)
    data = {'quantity': replaced_quantity}
    form = forms.ReplaceCartLineForm(data=data, cart=cart, product=variant)
    assert form.is_valid()
    form.save()
    assert cart.quantity == replaced_quantity


def test_replace_cartline_form_when_insufficient_stock(monkeypatch, cart,
                                                       variant):
    initial_quantity = 1
    replaced_quantity = 4

    cart.add(variant, initial_quantity)
    exception_mock = InsufficientStock(
        Mock(get_stock_quantity=Mock(return_value=2)))
    monkeypatch.setattr('saleor.product.models.ProductVariant.check_quantity',
                        Mock(side_effect=exception_mock))
    data = {'quantity': replaced_quantity}
    form = forms.ReplaceCartLineForm(data=data, cart=cart, product=variant)
    assert not form.is_valid()
    with pytest.raises(KeyError):
        form.save()
    assert cart.quantity == initial_quantity

def test_get_new_cart_data():
    cart_dict = {'token': 'randomtoken', 'total': 1, 'quantity': 1,
                 'current_quantity': 0}
    cart = Mock(**cart_dict)
    queryset_mock = Mock(create=Mock(return_value=cart))
    assert views.get_new_cart_data(queryset_mock) == cart_dict


def test_get_old_cart_from_request_when_authenticated(db, monkeypatch):
    cart = Cart.objects.create()

    monkeypatch.setattr(
        views, 'get_user_open_cart_token',
        lambda user: cart.token
    )

    user_mock = Mock(
        is_authenticated=Mock(return_value=True),
        get_signed_cookie=Mock(return_value=cart.token)
    )

    request = Mock(user=user_mock)

    views.get_cart_from_request(request)

    assert True


def test_get_new_cart_from_request_when_authenticated(db, monkeypatch):
    monkeypatch.setattr(
        views, 'get_user_open_cart_token',
        lambda user: None
    )

    user_mock = Mock(
        is_authenticated=Mock(return_value=True),
        get_signed_cookie=Mock(return_value=None),
        carts=Mock(open=Mock(return_value=Mock(get=Mock(
            side_effect=Cart.DoesNotExist))))
    )

    request = Mock(user=user_mock)

    carts_before = Cart.objects.open().count()
    returned_cart = views.get_cart_from_request(request, create=False)

    assert isinstance(returned_cart, Cart)
    assert len(returned_cart) == 0
    assert Cart.objects.open().count() == carts_before


def test_create_new_cart_from_request_when_anonymous(db, monkeypatch):
    monkeypatch.setattr(
        views, 'get_user_open_cart_token',
        lambda user: None
    )

    user_mock = Mock(
        is_authenticated=Mock(return_value=False),
        get_signed_cookie=Mock(return_value=None),
        carts=Mock(open=Mock(return_value=Mock(
                   get=Mock(side_effect=Cart.DoesNotExist))))
    )

    request = Mock(user=user_mock,
                   get_signed_cookie=Mock(return_value=None))

    carts_before = Cart.objects.open().count()
    returned_cart = views.get_cart_from_request(request, create=True)

    assert isinstance(returned_cart, Cart)
    assert len(returned_cart) == 0
    assert returned_cart.user is None
    assert Cart.objects.open().count() == carts_before + 1


def test_view_empty_cart(monkeypatch, client, cart):
    monkeypatch.setattr(
        views, 'get_cart_from_request',
        lambda request: cart
    )
    request = client.get('/cart/')
    request.discounts = None
    response = views.index(request)
    assert response.status_code == 200


def test_view_cart(monkeypatch, client, cart, variant):
    cart.add(variant, 1)
    monkeypatch.setattr(
        views, 'get_cart_from_request',
        lambda request: cart
    )
    request = client.get('/cart/')
    request.discounts = None
    response = views.index(request)
    assert response.status_code == 200


def test_view_update_cart_quantity(monkeypatch, client, cart, variant):
    cart.add(variant, 1)
    monkeypatch.setattr(
        views, 'get_cart_from_request',
        lambda request: cart
    )
    request = client.post('/cart/update/{}'.format(variant.pk), {'quantity': 3})    
    request.discounts = None
    request.POST = {'quantity': 3}
    request.is_ajax = lambda: True
    response = views.index(request, variant.pk)
    assert response.status_code == 200
    assert cart.quantity == 3

    request.POST = {'quantity': 5}
    request.is_ajax = lambda: False
    response = views.index(request, variant.pk)
    assert response.status_code == 302
    assert cart.quantity == 5


def test_view_invalid_update_cart(monkeypatch, client, cart, variant):
    cart.add(variant, 1)
    monkeypatch.setattr(
        views, 'get_cart_from_request',
        lambda request: cart
    )
    request = client.post('/cart/update/{}'.format(variant.pk), {})
    request.discounts = None
    request.POST = {}
    request.is_ajax = lambda: True
    response = views.index(request, variant.pk)
    assert response.status_code == 400
    assert 'error' in json.loads(response.content).keys() 
    assert cart.quantity == 1
