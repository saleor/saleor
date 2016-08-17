from __future__ import unicode_literals

import pytest
from mock import Mock, MagicMock
from satchless.item import InsufficientStock

from .models import Cart
from .context_processors import cart_counter
from ..product import models
from . import utils

from ..product.models import Product, ProductVariant
from prices import Price
from decimal import Decimal


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


@pytest.mark.django_db
def test_cart_counter():

    product = models.Product.objects.create(
        name='Test product', price=10, weight=1)

    variant = models.ProductVariant.objects.create(product=product, sku='123')

    models.Stock.objects.create(
        variant=variant, cost_price=10, quantity=5, quantity_allocated=0,
        location='Warehouse 3')

    cart = Cart.objects.create()
    cart.add(variant)

    resp = cart_counter(
        Mock(
            user=Mock(is_authenticated=lambda: False),
            get_signed_cookie=lambda a, default: cart.token
        )
    )
    assert resp == {'cart_counter': 1}

    resp = cart_counter(
        Mock(
            user=Mock(is_authenticated=lambda: False),
            get_signed_cookie=lambda a, default: 'randomtoken'
        )
    )
    assert resp == {'cart_counter': 0}


def test_contains_unavailable_products():
    cart = MagicMock()
    cart.__iter__.return_value = []
    assert not utils.contains_unavailable_products(cart)

    item = MagicMock()
    item.product.check_quantity.side_effect = InsufficientStock("")
    cart.__iter__.return_value = [item]
    assert not utils.contains_unavailable_products(cart)


def test_check_product_availability_and_warn(monkeypatch, cart, variant):
    monkeypatch.setattr('django.contrib.messages.warning',
                        Mock(warning=Mock()))


    cart.add(variant, 1)

    monkeypatch.setattr('saleor.cart.utils.contains_unavailable_products',
                        Mock(return_value=False))


    utils.check_product_availability_and_warn(MagicMock(), cart)

    assert len(cart) == 1

    monkeypatch.setattr('saleor.cart.utils.contains_unavailable_products',
                        Mock(return_value=True))

    utils.check_product_availability_and_warn(MagicMock(), cart)

    assert len(cart) == 0
