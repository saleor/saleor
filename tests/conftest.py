# coding: utf-8
from __future__ import unicode_literals

from decimal import Decimal
import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils.encoding import smart_text
from mock import Mock

from saleor.cart import utils
from saleor.cart.models import Cart
from saleor.checkout.core import Checkout
from saleor.discount.models import Voucher, Sale
from saleor.order.models import Order, OrderedItem, DeliveryGroup
from saleor.product.models import (AttributeChoiceValue, Category, Product,
                                   ProductAttribute, ProductClass,
                                   ProductVariant, Stock, StockLocation)
from saleor.shipping.models import ShippingMethod
from saleor.site.models import SiteSettings, AuthorizationKey
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
        utils, 'get_cart_from_request',
        lambda request, cart_queryset=None: cart)
    cart.discounts = Sale.objects.all()
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
def color_attribute(db):  # pylint: disable=W0613
    attribute = ProductAttribute.objects.create(
        slug='color', name='Color')
    AttributeChoiceValue.objects.create(
        attribute=attribute, name='Red', slug='red')
    AttributeChoiceValue.objects.create(
        attribute=attribute, name='Blue', slug='blue')
    return attribute


@pytest.fixture
def size_attribute(db):  # pylint: disable=W0613
    attribute = ProductAttribute.objects.create(slug='size', name='Size')
    AttributeChoiceValue.objects.create(
        attribute=attribute, name='Small', slug='small')
    AttributeChoiceValue.objects.create(
        attribute=attribute, name='Big', slug='big')
    return attribute


@pytest.fixture
def default_category(db):  # pylint: disable=W0613
    return Category.objects.create(name='Default', slug='default')


@pytest.fixture
def product_class(color_attribute, size_attribute):
    product_class = ProductClass.objects.create(name='Default Class',
                                                has_variants=False,
                                                is_shipping_required=True)
    product_class.product_attributes.add(color_attribute)
    product_class.variant_attributes.add(size_attribute)
    return product_class


@pytest.fixture
def product_in_stock(product_class, default_category):
    product_attr = product_class.product_attributes.first()
    attr_value = product_attr.values.first()
    attributes = {smart_text(product_attr.pk): smart_text(attr_value.pk)}

    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_class=product_class, attributes=attributes)
    product.categories.add(default_category)

    variant = ProductVariant.objects.create(product=product, sku='123')
    warehouse_1 = StockLocation.objects.create(name='Warehouse 1')
    warehouse_2 = StockLocation.objects.create(name='Warehouse 2')
    warehouse_3 = StockLocation.objects.create(name='Warehouse 3')
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


@pytest.fixture()
def order_with_items(order, product_class):
    group = DeliveryGroup.objects.create(order=order)
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_class=product_class)

    OrderedItem.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_%d' % (product.pk,),
        quantity=1,
        unit_price_net=Decimal('10.00'),
        unit_price_gross=Decimal('10.00'),
    )
    product = Product.objects.create(
        name='Test product 2', price=Decimal('20.00'),
        product_class=product_class)

    OrderedItem.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_%d' % (product.pk,),
        quantity=1,
        unit_price_net=Decimal('20.00'),
        unit_price_gross=Decimal('20.00'),
    )
    product = Product.objects.create(
        name='Test product 3', price=Decimal('30.00'),
        product_class=product_class)

    OrderedItem.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_%d' % (product.pk,),
        quantity=1,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'),
    )

    return order


@pytest.fixture()
def order_with_items_and_stock(order, product_class):
    group = DeliveryGroup.objects.create(order=order)
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_class=product_class)
    variant = ProductVariant.objects.create(product=product, sku='SKU_A')
    warehouse = StockLocation.objects.create(name='Warehouse 1')
    stock = Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=3,
        location=warehouse)
    OrderedItem.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_A',
        quantity=3,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'),
        stock=stock
    )
    product = Product.objects.create(
        name='Test product 2', price=Decimal('20.00'),
        product_class=product_class)
    variant = ProductVariant.objects.create(product=product, sku='SKU_B')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=2,
        location=warehouse)
    OrderedItem.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_B',
        quantity=2,
        unit_price_net=Decimal('20.00'),
        unit_price_gross=Decimal('20.00'),
        stock=stock
    )
    Order.objects.recalculate_order(order)
    order.refresh_from_db()
    return order


@pytest.fixture()
def sale(db, default_category):
    sale = Sale.objects.create(name="Sale", value=5)
    sale.categories.add(default_category)
    return sale


@pytest.fixture
def site_settings(db, settings):
    obj = SiteSettings.objects.create(name="mirumee.com",
                                      header_text="mirumee.com",
                                      domain="mirumee.com")
    settings.SITE_SETTINGS_ID = obj.pk
    return obj


@pytest.fixture
def authorization_key(db, site_settings):
    return AuthorizationKey.objects.create(
        site_settings=site_settings, name='Backend', key='Key',
        password='Password')
