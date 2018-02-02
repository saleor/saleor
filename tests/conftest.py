from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.encoding import smart_text
from PIL import Image
from prices import Price

from saleor.cart import utils
from saleor.cart.models import Cart
from saleor.checkout.core import Checkout
from saleor.discount.models import Sale, Voucher
from saleor.order import GroupStatus
from saleor.order.models import DeliveryGroup, Order, OrderLine
from saleor.order.utils import recalculate_order
from saleor.product.models import (
    AttributeChoiceValue, Category, Collection, Product, ProductAttribute,
    ProductImage, ProductType, ProductVariant, Stock, StockLocation)
from saleor.shipping.models import ShippingMethod
from saleor.site.models import AuthorizationKey, SiteSettings
from saleor.userprofile.models import Address, User


@pytest.fixture(autouse=True)
def site_settings(db, settings):
    """Create a site and matching site settings.

    This fixture is autouse because django.contrib.sites.models.Site and
    saleor.site.models.SiteSettings have a one-to-one relationship and a site
    should never exist without a matching settings object.
    """
    site = Site.objects.get_or_create(
        name="mirumee.com", domain="mirumee.com")[0]
    obj = SiteSettings.objects.get_or_create(site=site)[0]
    settings.SITE_ID = site.pk
    return obj


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
def admin_user(db):
    """Return a Django admin user."""
    return User.objects.create_superuser('admin@example.com', 'password')


@pytest.fixture()
def admin_client(admin_user):
    """Return a Django test client logged in as an admin user."""
    from django.test.client import Client
    client = Client()
    client.login(username=admin_user.email, password='password')
    return client


@pytest.fixture()
def staff_user(db):
    """Return a staff member."""
    return User.objects.create_user(
        email='staff_test@example.com', password='password', is_staff=True,
        is_active=True)


@pytest.fixture()
def staff_client(client, staff_user):
    """Return a Django test client logged in as an staff member."""
    client.login(username=staff_user.email, password='password')
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
        country='PL',
        phone='+48713988102')


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
def default_stock_location(db):
    return StockLocation.objects.create(name='Warehouse 1')


@pytest.fixture
def staff_group():
    return Group.objects.create(name='test')


@pytest.fixture
def permission_view_product():
    return Permission.objects.get(codename='view_product')


@pytest.fixture
def permission_edit_product():
    return Permission.objects.get(codename='edit_product')


@pytest.fixture
def permission_view_category():
    return Permission.objects.get(codename='view_category')


@pytest.fixture
def permission_edit_category():
    return Permission.objects.get(codename='edit_category')


@pytest.fixture
def permission_view_stock_location():
    return Permission.objects.get(codename='view_stock_location')


@pytest.fixture
def permission_edit_stock_location():
    return Permission.objects.get(codename='edit_stock_location')


@pytest.fixture
def permission_view_sale():
    return Permission.objects.get(codename='view_sale')


@pytest.fixture
def permission_edit_sale():
    return Permission.objects.get(codename='edit_sale')


@pytest.fixture
def permission_view_voucher():
    return Permission.objects.get(codename='view_voucher')


@pytest.fixture
def permission_edit_voucher():
    return Permission.objects.get(codename='edit_voucher')


@pytest.fixture
def permission_view_order():
    return Permission.objects.get(codename='view_order')


@pytest.fixture
def permission_edit_order():
    return Permission.objects.get(codename='edit_order')


@pytest.fixture
def product_type(color_attribute, size_attribute):
    product_type = ProductType.objects.create(
        name='Default Type', has_variants=False, is_shipping_required=True)
    product_type.product_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)
    return product_type


@pytest.fixture
def product_in_stock(product_type, default_category):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    attributes = {smart_text(product_attr.pk): smart_text(attr_value.pk)}

    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_type=product_type, attributes=attributes,
        category=default_category)

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()
    variant_attributes = {
        smart_text(variant_attr.pk): smart_text(variant_attr_value.pk)}

    variant = ProductVariant.objects.create(
        product=product, sku='123', attributes=variant_attributes)
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
def product_without_shipping(default_category):
    product_type = ProductType.objects.create(
        name='Type with no shipping', has_variants=False,
        is_shipping_required=False)
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_type=product_type, category=default_category)
    ProductVariant.objects.create(product=product, sku='SKU_B')
    return product


@pytest.fixture
def product_list(product_type, default_category):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    attributes = {smart_text(product_attr.pk): smart_text(attr_value.pk)}

    product_1 = Product.objects.create(
        name='Test product 1', price=Decimal('10.00'),
        product_type=product_type, attributes=attributes, is_published=True,
        category=default_category)

    product_2 = Product.objects.create(
        name='Test product 2', price=Decimal('20.00'),
        product_type=product_type, attributes=attributes, is_published=False,
        category=default_category)

    product_3 = Product.objects.create(
        name='Test product 3', price=Decimal('20.00'),
        product_type=product_type, attributes=attributes, is_published=True,
        category=default_category)

    return [product_1, product_2, product_3]


@pytest.fixture
def order_list(admin_user, billing_address):
    data = {
        'billing_address': billing_address, 'user': admin_user,
        'user_email': admin_user.email, 'total': Price(123, currency='USD')}
    order = Order.objects.create(**data)
    order1 = Order.objects.create(**data)
    order2 = Order.objects.create(**data)

    return [order, order1, order2]


@pytest.fixture
def stock_location():
    warehouse_1 = StockLocation.objects.create(name='Warehouse 1')
    return warehouse_1


@pytest.fixture
def product_image():
    img_data = BytesIO()
    image = Image.new('RGB', size=(1, 1))
    image.save(img_data, format='JPEG')
    return SimpleUploadedFile('product.jpg', img_data.getvalue())


@pytest.fixture
def product_with_image(product_in_stock, product_image):
    product = product_in_stock
    ProductImage.objects.create(product=product, image=product_image)
    return product


@pytest.fixture
def unavailable_product(product_type, default_category):
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_type=product_type, is_published=False,
        category=default_category)
    return product


@pytest.fixture
def product_with_images(product_type, default_category):
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_type=product_type, category=default_category)
    file_mock_0 = MagicMock(spec=File, name='FileMock0')
    file_mock_0.name = 'image0.jpg'
    file_mock_1 = MagicMock(spec=File, name='FileMock1')
    file_mock_1.name = 'image1.jpg'
    product.images.create(image=file_mock_0)
    product.images.create(image=file_mock_1)
    return product


@pytest.fixture
def anonymous_checkout():
    return Checkout((), AnonymousUser(), 'tracking_code')


@pytest.fixture
def voucher(db):  # pylint: disable=W0613
    return Voucher.objects.create(code='mirumee', discount_value=20)


@pytest.fixture()
def order_with_lines(order, product_type, default_category):
    group = DeliveryGroup.objects.create(order=order)
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_type=product_type, category=default_category)

    OrderLine.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_%d' % (product.pk,),
        is_shipping_required=product.product_type.is_shipping_required,
        quantity=1,
        unit_price_net=Decimal('10.00'),
        unit_price_gross=Decimal('10.00'))
    product = Product.objects.create(
        name='Test product 2', price=Decimal('20.00'),
        product_type=product_type, category=default_category)

    OrderLine.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_%d' % (product.pk,),
        is_shipping_required=product.product_type.is_shipping_required,
        quantity=1,
        unit_price_net=Decimal('20.00'),
        unit_price_gross=Decimal('20.00'))
    product = Product.objects.create(
        name='Test product 3', price=Decimal('30.00'),
        product_type=product_type, category=default_category)

    OrderLine.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_%d' % (product.pk,),
        is_shipping_required=product.product_type.is_shipping_required,
        quantity=1,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'))

    recalculate_order(order)
    return order


@pytest.fixture()
def order_with_lines_and_stock(order, product_type, default_category):
    group = DeliveryGroup.objects.create(order=order)
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_type=product_type, category=default_category)
    variant = ProductVariant.objects.create(product=product, sku='SKU_A')
    warehouse = StockLocation.objects.create(name='Warehouse 1')
    stock = Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=3,
        location=warehouse)
    OrderLine.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_A',
        is_shipping_required=product.product_type.is_shipping_required,
        quantity=3,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'),
        stock=stock,
        stock_location=stock.location.name)
    product = Product.objects.create(
        name='Test product 2', price=Decimal('20.00'),
        product_type=product_type, category=default_category)
    variant = ProductVariant.objects.create(product=product, sku='SKU_B')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=2,
        location=warehouse)
    OrderLine.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_B',
        is_shipping_required=product.product_type.is_shipping_required,
        quantity=2,
        unit_price_net=Decimal('20.00'),
        unit_price_gross=Decimal('20.00'),
        stock=stock,
        stock_location=stock.location.name)
    recalculate_order(order)
    order.refresh_from_db()
    return order


@pytest.fixture()
def order_with_variant_from_different_stocks(order_with_lines_and_stock):
    line = OrderLine.objects.get(product_sku='SKU_A')
    variant = ProductVariant.objects.get(sku=line.product_sku)
    warehouse_2 = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=2,
        location=warehouse_2)
    OrderLine.objects.create(
        delivery_group=line.delivery_group,
        product=variant.product,
        product_name=variant.product.name,
        product_sku=line.product_sku,
        is_shipping_required=variant.product.product_type.is_shipping_required,
        quantity=2,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'),
        stock=stock,
        stock_location=stock.location.name)
    warehouse_2 = StockLocation.objects.create(name='Warehouse 3')
    Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=0,
        location=warehouse_2)
    recalculate_order(order_with_lines_and_stock)
    return order_with_lines_and_stock


@pytest.fixture()
def delivery_group(order, product_type, default_category):
    group = DeliveryGroup.objects.create(order=order)
    product = Product.objects.create(
        name='Test product', price=Decimal('10.00'),
        product_type=product_type, category=default_category)
    variant = ProductVariant.objects.create(product=product, sku='SKU_A')
    warehouse = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=1, quantity=5, quantity_allocated=3,
        location=warehouse)
    OrderLine.objects.create(
        delivery_group=group,
        product=product,
        product_name=product.name,
        product_sku='SKU_A',
        is_shipping_required=product.product_type.is_shipping_required,
        quantity=3,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'),
        stock=stock,
        stock_location=stock.location.name)
    recalculate_order(order)
    order.refresh_from_db()
    return group


@pytest.fixture()
def sale(db, default_category):
    sale = Sale.objects.create(name="Sale", value=5)
    sale.categories.add(default_category)
    return sale


@pytest.fixture
def authorization_key(db, site_settings):
    return AuthorizationKey.objects.create(
        site_settings=site_settings, name='Backend', key='Key',
        password='Password')


@pytest.fixture
def permission_view_staff():
    return Permission.objects.get(codename='view_staff')


@pytest.fixture
def permission_edit_staff():
    return Permission.objects.get(codename='edit_staff')


@pytest.fixture
def permission_view_group():
    return Permission.objects.get(codename='view_group')


@pytest.fixture
def permission_edit_group():
    return Permission.objects.get(codename='edit_group')


@pytest.fixture
def permission_view_properties():
    return Permission.objects.get(codename='view_properties')


@pytest.fixture
def permission_edit_properties():
    return Permission.objects.get(codename='edit_properties')


@pytest.fixture
def permission_view_shipping():
    return Permission.objects.get(codename='view_shipping')


@pytest.fixture
def permission_edit_shipping():
    return Permission.objects.get(codename='edit_shipping')


@pytest.fixture
def permission_view_user():
    return Permission.objects.get(codename='view_user')


@pytest.fixture
def permission_edit_user():
    return Permission.objects.get(codename='edit_user')


@pytest.fixture
def permission_edit_settings():
    return Permission.objects.get(codename='edit_settings')


@pytest.fixture
def permission_impersonate_user():
    return Permission.objects.get(codename='impersonate_user')


@pytest.fixture
def open_orders(billing_address):
    def group_data(orders, status):
        return {'order': orders[-1], 'status': status}

    orders = []

    orders.append(Order.objects.create(billing_address=billing_address))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.NEW))

    orders.append(Order.objects.create(billing_address=billing_address))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.NEW))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.CANCELLED))

    orders.append(Order.objects.create(billing_address=billing_address))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.NEW))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.SHIPPED))

    orders.append(Order.objects.create(billing_address=billing_address))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.NEW))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.SHIPPED))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.CANCELLED))

    return orders


@pytest.fixture
def closed_orders(billing_address):
    def group_data(orders, status):
        return {'order': orders[-1], 'status': status}

    orders = []

    orders.append(Order.objects.create(billing_address=billing_address))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.SHIPPED))

    orders.append(Order.objects.create(billing_address=billing_address))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.SHIPPED))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.CANCELLED))

    orders.append(Order.objects.create(billing_address=billing_address))
    DeliveryGroup.objects.create(**group_data(orders, GroupStatus.CANCELLED))

    # empty order is considered as closed
    orders.append(Order.objects.create(billing_address=billing_address))

    return orders


@pytest.fixture
def collection(db):
    collection = Collection.objects.create(name='Collection', slug='collection')
    return collection
