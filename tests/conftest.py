# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import AnonymousUser
from mock import Mock

from saleor.cart import decorators
from saleor.cart.models import Cart
from saleor.checkout.core import Checkout
from saleor.discount.models import Voucher
from saleor.order.models import Order
from saleor.product.models import Product, ProductVariant, Stock, StockLocation
from saleor.shipping.models import ShippingMethod
from saleor.userprofile.models import Address, User


@pytest.fixture
def cart(db):  # pylint: disable=W0613
    return Cart.objects.create()


@pytest.fixture
def customer_user(db):  # pylint: disable=W0613
    return User.objects.create_user('test@example.com', 'password')


@pytest.fixture
def request_cart(cart, monkeypatch):
    # FIXME: Fixtures should not have any side effects
    monkeypatch.setattr(
        decorators, 'get_cart_from_request',
        lambda request, create=False, cart_queryset=None: cart)
    return cart


@pytest.fixture
def request_cart_with_item(product_in_stock, request_cart):
    variant = product_in_stock.variants.get()
    # Prepare some data
    request_cart.add(variant)
    return request_cart


@pytest.fixture
def order(billing_address):
    return Order.objects.create(billing_address=billing_address)


@pytest.fixture()
def admin_user(db):  # pylint: disable=W0613
    """A Django admin user.
    """
    return User.objects.create_superuser('admin@example.com', 'password')


@pytest.fixture()
def admin_client(admin_user):
    """A Django test client logged in as an admin user."""
    from django.test.client import Client
    client = Client()
    client.login(username=admin_user.email, password='password')
    return client


@pytest.fixture()
def authorized_client(client, customer_user):
    client.login(username=customer_user.email, password='password')
    return client


@pytest.fixture
def billing_address(db):  # pylint: disable=W0613
    return Address.objects.create(
        first_name='John', last_name='Doe',
        company_name='Mirumee Software',
        street_address_1='Tęczowa 7',
        city='Wrocław',
        postal_code='53-601',
        country='PL')


@pytest.fixture
def shipping_method(db):  # pylint: disable=W0613
    shipping_method = ShippingMethod.objects.create(name='DHL')
    shipping_method.price_per_country.create(price=10)
    return shipping_method


@pytest.fixture
def product_in_stock(db):  # pylint: disable=W0613
    product = Product.objects.create(
        name='Test product', price=10, weight=1)
    variant = ProductVariant.objects.create(product=product, sku='123')
    warehouse_1 = StockLocation.objects.create(location='Warehouse 1')
    warehouse_2 = StockLocation.objects.create(location='Warehouse 2')
    warehouse_3 = StockLocation.objects.create(location='Warehouse 3')
    Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=5,
        location=warehouse_1)
    Stock.objects.create(
        variant=variant, cost_price=100, quantity=5, quantity_allocated=5,
        location=warehouse_2)
    Stock.objects.create(
        variant=variant, cost_price=10, quantity=5, quantity_allocated=0,
        location=warehouse_3)
    return product


@pytest.fixture
def anonymous_checkout():
    return Checkout(Mock(), AnonymousUser(), 'tracking_code')


@pytest.fixture
def voucher(db):  # pylint: disable=W0613
    return Voucher.objects.create(code='mirumee', discount_value=20)
