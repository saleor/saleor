from __future__ import unicode_literals
from decimal import Decimal

from django.db import models
from django.test import TestCase
from django.utils.encoding import smart_text
from mock import MagicMock
from prices import Price
import pytest
from satchless.item import InsufficientStock

from . import Cart, SessionCart
from . import forms
from .forms import ReplaceCartLineForm, ReplaceCartLineFormSet
from ..product.models import (ProductVariant, StockedProduct, PhysicalProduct)


class BigShip(ProductVariant, StockedProduct, PhysicalProduct):
    name = models.CharField(max_length=250)

    def get_price_per_item(self, discounted=True, **kwargs):
        return self.price

    def get_slug(self):
        return 'bigship'

    @property
    def product(self):
        return self


class ShipPhoto(ProductVariant, PhysicalProduct):
    name = models.CharField(max_length=250)

    def get_slug(self):
        return 'bigship-photo'

    @property
    def product(self):
        return self


class AddToCartForm(forms.AddToCartForm):

    def get_variant(self, cleaned_data):
        return self.product


stock_product = BigShip(name='BigShip', stock=10,
                        price=Price(10, currency='USD'), weight=Decimal(123))
non_stock_product = ShipPhoto(price=Price(10, currency='USD'))


def test_cart_checks_quantity():
    cart = Cart(session_cart=MagicMock())
    with pytest.raises(InsufficientStock):
        cart.add(stock_product, 100)
    assert not cart


def test_cart_add_adds_to_session_cart():
    cart = Cart(session_cart=SessionCart())
    cart.add(stock_product, 10)
    assert cart.session_cart.count() == 10
    assert cart.session_cart.modified
    assert cart.session_cart[0].product == smart_text(stock_product)


def test_quantity_is_correctly_saved():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 5}
    form = AddToCartForm(data, cart=cart, product=stock_product)
    assert form.is_valid()
    assert not cart
    form.save()
    product_quantity = cart.get_line(stock_product).quantity
    assert product_quantity == 5


def test_multiple_actions_result_in_combined_quantity():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 5}
    form = AddToCartForm(data, cart=cart, product=stock_product)
    assert form.is_valid()
    form.save()
    form = AddToCartForm(data, cart=cart, product=stock_product)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stock_product).quantity
    assert product_quantity == 10


def test_excessive_quantity_is_rejected():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 15}
    form = AddToCartForm(data, cart=cart, product=stock_product)
    assert not form.is_valid()
    assert not cart


def test_any_quantity_is_valid_for_non_stock_products():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 999}
    form = AddToCartForm(data, cart=cart, product=non_stock_product)
    assert form.is_valid()
    assert not cart
    form.save()
    assert cart


def test_replace_form_replaces_quantity():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 5}
    form = ReplaceCartLineForm(data, cart=cart, product=stock_product)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stock_product).quantity
    assert product_quantity == 5
    form = ReplaceCartLineForm(data, cart=cart, product=stock_product)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stock_product).quantity
    assert product_quantity == 5


def test_replace_form_rejects_excessive_quantity():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 15}
    form = ReplaceCartLineForm(data, cart=cart, product=stock_product)
    assert not form.is_valid()


def test_replace_formset_works():
    cart = Cart(session_cart=MagicMock())
    cart.add(stock_product, 5)
    cart.add(non_stock_product, 100)
    data = {
        'form-TOTAL_FORMS': 2,
        'form-INITIAL_FORMS': 2,
        'form-0-quantity': 5,
        'form-1-quantity': 5}
    form = ReplaceCartLineFormSet(data, cart=cart)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stock_product).quantity
    assert product_quantity == 5


def test_session_cart_returns_correct_prices():
    cart = Cart(session_cart=SessionCart())
    cart.add(stock_product, quantity=10)
    cart_price = cart[0].get_price_per_item()
    sessioncart_price = cart.session_cart[0].get_price_per_item()
    assert cart_price == sessioncart_price
