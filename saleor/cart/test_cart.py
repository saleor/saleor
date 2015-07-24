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
from ..cart.utils import has_available_products, remove_unavailable_products
from ..product.models import (ProductVariant, Product)


class BigShipVariant(ProductVariant):

    def get_price_per_item(self, discounted=True, **kwargs):
        return Price(10, currency='USD')

    def get_stock_quantity(self):
        return 10

    @property
    def product(self):
        return BigShip(name='Big Ship', price=Price(10, currency='USD'),
                       weight=Decimal(123))

    def display_variant(self, attributes=None):
        return 'BIG SHIP'


class BigShip(Product):

    def get_slug(self):
        return 'bigship'


class ShipPhotoVariant(ProductVariant):

    @property
    def product(self):
        return ShipPhoto(name='Ship Photo', price=Price(10, currency='USD'))

    def check_quantity(self, quantity):
        pass

    def display_variant(self, attributes=None):
        return 'SHIP PHOTO'

    def display_variant(self, attributes=None):
        return 'BIG SHIP'


class ShipPhoto(Product):

    def get_slug(self):
        return 'bigship-photo'

    def is_shipping_required(self):
        return False


class AddToCartForm(forms.AddToCartForm):

    def get_variant(self, cleaned_data):
        return self.product


stocked_variant = BigShipVariant(name='Big Ship')
non_stocked_variant = ShipPhotoVariant(name='Ship Photo')


def test_cart_checks_quantity():
    cart = Cart(session_cart=MagicMock())
    with pytest.raises(InsufficientStock):
        cart.add(stocked_variant, 100)
    assert not cart


def test_cart_add_adds_to_session_cart():
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, 10)
    assert cart.session_cart.count() == 10
    assert cart.session_cart.modified
    assert cart.session_cart[0].product == stocked_variant.display_product()


def test_quantity_is_correctly_saved():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 5}
    form = AddToCartForm(data, cart=cart, product=stocked_variant)
    assert form.is_valid()
    assert not cart
    form.save()
    product_quantity = cart.get_line(stocked_variant).quantity
    assert product_quantity == 5


def test_multiple_actions_result_in_combined_quantity():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 5}
    form = AddToCartForm(data, cart=cart, product=stocked_variant)
    assert form.is_valid()
    form.save()
    form = AddToCartForm(data, cart=cart, product=stocked_variant)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stocked_variant).quantity
    assert product_quantity == 10


def test_excessive_quantity_is_rejected():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 15}
    form = AddToCartForm(data, cart=cart, product=stocked_variant)
    assert not form.is_valid()
    assert not cart


def test_replace_form_replaces_quantity():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 5}
    form = ReplaceCartLineForm(data, cart=cart, product=stocked_variant)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stocked_variant).quantity
    assert product_quantity == 5
    form = ReplaceCartLineForm(data, cart=cart, product=stocked_variant)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stocked_variant).quantity
    assert product_quantity == 5


def test_replace_form_rejects_excessive_quantity():
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 15}
    form = ReplaceCartLineForm(data, cart=cart, product=stocked_variant)
    assert not form.is_valid()


def test_replace_formset_works():
    cart = Cart(session_cart=MagicMock())
    cart.add(stocked_variant, 5)
    cart.add(non_stocked_variant, 100)
    data = {
        'form-TOTAL_FORMS': 2,
        'form-INITIAL_FORMS': 2,
        'form-0-quantity': 5,
        'form-1-quantity': 5}
    form = ReplaceCartLineFormSet(data, cart=cart)
    assert form.is_valid()
    form.save()
    product_quantity = cart.get_line(stocked_variant).quantity
    assert product_quantity == 5


def test_session_cart_returns_correct_prices():
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, quantity=10)
    cart_price = cart[0].get_price_per_item()
    sessioncart_price = cart.session_cart[0].get_price_per_item()
    assert cart_price == sessioncart_price


def test_cart_has_unavailable_products():
    cart = Cart(session_cart=SessionCart())
    cart.add(non_stocked_variant, quantity=100)
    cart.add(stocked_variant, quantity=12, check_quantity=False)
    assert not has_available_products(cart)


def test_cart_has_available_products():
    cart = Cart(session_cart=SessionCart())
    cart.add(non_stocked_variant, quantity=100)
    cart.add(stocked_variant, quantity=10, check_quantity=False)
    assert has_available_products(cart)


def test_cart_contains_products_on_stock():
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, quantity=12, check_quantity=False)
    updated_cart = remove_unavailable_products(cart)
    assert cart.count() == 12
    assert updated_cart.count() == 10


def test_cart_doesnt_contain_empty_products():
    stocked_variant.get_stock_quantity = MagicMock(return_value=0)
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, quantity=10, check_quantity=False)
    updated_cart = remove_unavailable_products(cart)
    assert len(updated_cart) == 0
