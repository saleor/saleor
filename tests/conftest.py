# coding: utf-8
from __future__ import unicode_literals

import pytest

from saleor.cart import decorators
from saleor.cart.models import Cart
from saleor.product.models import Product, ProductVariant, Stock
from saleor.userprofile.models import Address, User



@pytest.fixture
def cart(db):  # pylint: disable=W0613
    return Cart.objects.create()


@pytest.fixture
def request_cart(cart, monkeypatch):
    monkeypatch.setattr(
        decorators, 'get_cart_from_request',
        lambda request, create=False: cart)
    return cart

@pytest.fixture()
def admin_user(db):
    """A Django admin user.

    This uses an existing user with username "admin", or creates a new one with
    password "password".
    """
    try:
        user = User.objects.get(email='admin@example.com')
    except User.DoesNotExist:
        user = User.objects.create_superuser(
            'admin@example.com', 'password')
    return user


@pytest.fixture()
def admin_client(db, admin_user):
    """A Django test client logged in as an admin user."""
    from django.test.client import Client

    client = Client()
    client.login(username=admin_user.email, password='password')
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
def product_in_stock(db):  # pylint: disable=W0613
    product = Product.objects.create(
        name='Test product', price=10, weight=1)
    variant = ProductVariant.objects.create(product=product, sku='123')
    Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=5,
        location='Warehouse 1')
    Stock.objects.create(
        variant=variant, cost_price=100, quantity=5, quantity_allocated=5,
        location='Warehouse 2')
    Stock.objects.create(
        variant=variant, cost_price=10, quantity=5, quantity_allocated=0,
        location='Warehouse 3')
    return product
