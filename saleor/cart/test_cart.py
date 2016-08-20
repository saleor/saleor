from __future__ import unicode_literals
from decimal import Decimal

from mock import MagicMock, Mock
from prices import Price
import pytest
from satchless.item import InsufficientStock

from . import Cart, SessionCart
from . import forms
from .forms import ReplaceCartLineForm, ReplaceCartLineFormSet
from ..cart.utils import (
    contains_unavailable_products, remove_unavailable_products)
from ..product.models import ProductVariant, Product
from ..product.test_product import product_in_stock, product_without_shipping  # NOQA


@pytest.fixture
def stocked_variant(monkeypatch):
    product = Product(name='Big Ship', price=Price(10, currency='USD'),
                      weight=Decimal(123))
    variant = ProductVariant(name='Big Ship', product=product)
    monkeypatch.setattr(
        'saleor.product.models.ProductVariant.get_stock_quantity',
        Mock(return_value=10))
    monkeypatch.setattr('saleor.product.models.ProductVariant.display_variant',
                        Mock(return_value='BIG SHIP'))
    monkeypatch.setattr(
        'saleor.product.models.ProductVariant.get_price_per_item',
        Mock(return_value=Price(10, currency='USD')))
    monkeypatch.setattr('saleor.product.models.Product.get_slug',
                        Mock(return_value='bigship'))
    return variant


@pytest.fixture
def non_stocked_variant(stocked_variant, product_without_shipping,
                        monkeypatch):
    stocked_variant.name = 'Ship Photo'
    monkeypatch.setattr('saleor.product.models.ProductVariant.check_quantity',
                        Mock(return_value=None))
    monkeypatch.setattr('saleor.product.models.ProductVariant.display_variant',
                        Mock(return_value='SHIP PHOTO'))
    monkeypatch.setattr('saleor.product.models.Product.get_slug',
                        Mock(return_value='bigship-photo'))
    return stocked_variant


class AddToCartForm(forms.AddToCartForm):

    def get_variant(self, cleaned_data):
        return self.product


def test_cart_checks_quantity(stocked_variant):
    cart = Cart(session_cart=MagicMock())
    with pytest.raises(InsufficientStock):
        cart.add(stocked_variant, 100)
    assert not cart


def test_cart_add_adds_to_session_cart(stocked_variant):
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, 10)
    assert cart.session_cart.count() == 10
    assert cart.session_cart.modified
    assert cart.session_cart[0].product == stocked_variant.display_product()


def test_quantity_is_correctly_saved(stocked_variant):
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 5}
    form = AddToCartForm(data, cart=cart, product=stocked_variant)
    assert form.is_valid()
    assert not cart
    form.save()
    product_quantity = cart.get_line(stocked_variant).quantity
    assert product_quantity == 5


def test_multiple_actions_result_in_combined_quantity(stocked_variant):
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


def test_excessive_quantity_is_rejected(stocked_variant):
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 15}
    form = AddToCartForm(data, cart=cart, product=stocked_variant)
    assert not form.is_valid()
    assert not cart


def test_replace_form_replaces_quantity(stocked_variant):
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


def test_replace_form_rejects_excessive_quantity(stocked_variant):
    cart = Cart(session_cart=MagicMock())
    data = {'quantity': 15}
    form = ReplaceCartLineForm(data, cart=cart, product=stocked_variant)
    assert not form.is_valid()


def test_replace_formset_works(stocked_variant):
    non_stocked_variant = ProductVariant(name='Ship Photo',
                                         product=stocked_variant.product)
    non_stocked_variant.check_quantity = Mock(return_value=None)
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


def test_session_cart_returns_correct_prices(stocked_variant):
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, quantity=10)
    cart_price = cart[0].get_price_per_item()
    sessioncart_price = cart.session_cart[0].get_price_per_item()
    assert cart_price == sessioncart_price


def test_cart_contains_unavailable_products(stocked_variant):
    non_stocked_variant = ProductVariant(name='Ship Photo',
                                         product=stocked_variant.product)
    non_stocked_variant.check_quantity = Mock(return_value=None)
    cart = Cart(session_cart=SessionCart())
    cart.add(non_stocked_variant, quantity=100)
    cart.add(stocked_variant, quantity=12, check_quantity=False)
    assert contains_unavailable_products(cart)


def test_cart_contains_only_available_products(stocked_variant,
                                               non_stocked_variant):
    cart = Cart(session_cart=SessionCart())
    cart.add(non_stocked_variant, quantity=100)
    cart.add(stocked_variant, quantity=10, check_quantity=False)
    assert not contains_unavailable_products(cart)


def test_cart_contains_products_on_stock(stocked_variant):
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, quantity=12, check_quantity=False)
    assert cart.count() == 12
    remove_unavailable_products(cart)
    assert cart.count() == 10


def test_cart_doesnt_contain_empty_products(stocked_variant):
    stocked_variant.get_stock_quantity = MagicMock(return_value=0)
    cart = Cart(session_cart=SessionCart())
    cart.add(stocked_variant, quantity=10, check_quantity=False)
    remove_unavailable_products(cart)
    assert len(cart) == 0