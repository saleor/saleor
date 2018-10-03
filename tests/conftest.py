from io import BytesIO
from unittest.mock import MagicMock, Mock

import pytest

from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ModelForm
from django.utils.encoding import smart_text
from django_countries import countries
from django_prices_vatlayer.models import VAT
from django_prices_vatlayer.utils import get_tax_for_rate
from payments import FraudStatus, PaymentStatus
from PIL import Image
from prices import Money
from saleor.account.models import Address, User
from saleor.checkout import utils
from saleor.checkout.models import Cart
from saleor.checkout.utils import add_variant_to_cart
from saleor.dashboard.menu.utils import update_menu
from saleor.dashboard.order.utils import fulfill_order_line
from saleor.discount.models import Sale, Voucher, VoucherTranslation
from saleor.menu.models import Menu, MenuItem
from saleor.order import OrderStatus
from saleor.order.models import Order
from saleor.order.utils import recalculate_order
from saleor.page.models import Page
from saleor.product.models import (
    Attribute, AttributeTranslation, AttributeValue, Category, Collection,
    Product, ProductImage, ProductTranslation, ProductType, ProductVariant)
from saleor.shipping.models import (
    ShippingMethod, ShippingMethodType, ShippingZone)
from saleor.site.models import AuthorizationKey, SiteSettings


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

    main_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS['top_menu_name'])[0]
    update_menu(main_menu)
    secondary_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS['bottom_menu_name'])[0]
    update_menu(secondary_menu)
    obj.top_menu = main_menu
    obj.bottom_menu = secondary_menu
    obj.save()
    return obj


@pytest.fixture
def cart(db):
    return Cart.objects.create()


@pytest.fixture
def cart_with_item(cart, product):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, 3)
    cart.save()
    return cart


@pytest.fixture
def cart_with_voucher(cart, product, voucher):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, 3)
    cart.voucher_code = voucher.code
    cart.discount_amount = Money('20.00', 'USD')
    cart.save()
    return cart


@pytest.fixture
def address(db):  # pylint: disable=W0613
    return Address.objects.create(
        first_name='John', last_name='Doe',
        company_name='Mirumee Software',
        street_address_1='Tęczowa 7',
        city='Wrocław',
        postal_code='53-601',
        country='PL',
        phone='+48713988102')


@pytest.fixture
def customer_user(address):  # pylint: disable=W0613
    default_address = address.get_copy()
    user = User.objects.create_user(
        'test@example.com',
        'password',
        default_billing_address=default_address,
        default_shipping_address=default_address)
    user.addresses.add(default_address)
    return user


@pytest.fixture
def request_cart(cart, monkeypatch):
    # FIXME: Fixtures should not have any side effects
    monkeypatch.setattr(
        utils, 'get_cart_from_request',
        lambda request, cart_queryset=None: cart)
    return cart


@pytest.fixture
def request_cart_with_item(product, request_cart):
    variant = product.variants.get()
    add_variant_to_cart(request_cart, variant)
    return request_cart


@pytest.fixture
def order(customer_user):
    address = customer_user.default_billing_address.get_copy()
    return Order.objects.create(
        billing_address=address,
        user_email=customer_user.email,
        user=customer_user)


@pytest.fixture()
def admin_user(db):
    """Return a Django admin user."""
    return User.objects.create_superuser('admin@example.com', 'password')


@pytest.fixture()
def admin_client(admin_user):
    """Return a Django test client logged in as an admin user."""
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
def shipping_zone(db):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(
        name='Europe', countries=[code for code, name in countries])
    shipping_zone.shipping_methods.create(
        name='DHL', minimum_order_price=Money(0, 'USD'),
        type=ShippingMethodType.PRICE_BASED, price=Money(10, 'USD'),
        shipping_zone=shipping_zone)
    return shipping_zone


@pytest.fixture
def shipping_method(shipping_zone):
    return ShippingMethod.objects.create(
        name='DHL', minimum_order_price=Money(0, 'USD'),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(10, 'USD'), shipping_zone=shipping_zone)


@pytest.fixture
def color_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(
        slug='color', name='Color')
    AttributeValue.objects.create(
        attribute=attribute, name='Red', slug='red')
    AttributeValue.objects.create(
        attribute=attribute, name='Blue', slug='blue')
    return attribute


@pytest.fixture
def pink_attribute_value(color_attribute):  # pylint: disable=W0613
    value = AttributeValue.objects.create(
        slug='pink', name='Pink', attribute=color_attribute, value='#FF69B4')
    return value


@pytest.fixture
def size_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(slug='size', name='Size')
    AttributeValue.objects.create(
        attribute=attribute, name='Small', slug='small')
    AttributeValue.objects.create(
        attribute=attribute, name='Big', slug='big')
    return attribute


@pytest.fixture
def category(db):  # pylint: disable=W0613
    return Category.objects.create(name='Default', slug='default')


@pytest.fixture
def non_default_category(db):  # pylint: disable=W0613
    return Category.objects.create(name='Not default', slug='not-default')


@pytest.fixture
def permission_manage_discounts():
    return Permission.objects.get(codename='manage_discounts')


@pytest.fixture
def permission_manage_orders():
    return Permission.objects.get(codename='manage_orders')


@pytest.fixture
def product_type(color_attribute, size_attribute):
    product_type = ProductType.objects.create(
        name='Default Type', has_variants=False, is_shipping_required=True)
    product_type.product_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)
    return product_type


@pytest.fixture
def product(product_type, category):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    attributes = {smart_text(product_attr.pk): smart_text(attr_value.pk)}

    product = Product.objects.create(
        name='Test product', price=Money('10.00', 'USD'),
        product_type=product_type, attributes=attributes, category=category)

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()
    variant_attributes = {
        smart_text(variant_attr.pk): smart_text(variant_attr_value.pk)}

    ProductVariant.objects.create(
        product=product, sku='123', attributes=variant_attributes,
        cost_price=Money('1.00', 'USD'), quantity=10, quantity_allocated=1)
    return product


@pytest.fixture
def variant(product):
    product_variant = ProductVariant.objects.create(
        product=product, sku='SKU_A', cost_price=Money(1, 'USD'), quantity=5,
        quantity_allocated=3)
    return product_variant


@pytest.fixture
def product_without_shipping(category):
    product_type = ProductType.objects.create(
        name='Type with no shipping', has_variants=False,
        is_shipping_required=False)
    product = Product.objects.create(
        name='Test product', price=Money('10.00', 'USD'),
        product_type=product_type, category=category)
    ProductVariant.objects.create(product=product, sku='SKU_B')
    return product


@pytest.fixture
def product_list(product_type, category):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    attributes = {smart_text(product_attr.pk): smart_text(attr_value.pk)}

    product_1 = Product.objects.create(
        name='Test product 1', price=Money('10.00', 'USD'), category=category,
        product_type=product_type, attributes=attributes, is_published=True)

    product_2 = Product.objects.create(
        name='Test product 2', price=Money('20.00', 'USD'), category=category,
        product_type=product_type, attributes=attributes, is_published=False)

    product_3 = Product.objects.create(
        name='Test product 3', price=Money('20.00', 'USD'), category=category,
        product_type=product_type, attributes=attributes, is_published=True)

    return [product_1, product_2, product_3]


@pytest.fixture
def order_list(customer_user):
    address = customer_user.default_billing_address.get_copy()
    data = {
        'billing_address': address, 'user': customer_user,
        'user_email': customer_user.email}
    order = Order.objects.create(**data)
    order1 = Order.objects.create(**data)
    order2 = Order.objects.create(**data)

    return [order, order1, order2]


@pytest.fixture
def product_image():
    img_data = BytesIO()
    image = Image.new('RGB', size=(1, 1))
    image.save(img_data, format='JPEG')
    return SimpleUploadedFile('product.jpg', img_data.getvalue())


@pytest.fixture
def product_with_image(product, product_image):
    ProductImage.objects.create(product=product, image=product_image)
    return product


@pytest.fixture
def unavailable_product(product_type, category):
    product = Product.objects.create(
        name='Test product', price=Money('10.00', 'USD'),
        product_type=product_type, is_published=False, category=category)
    return product


@pytest.fixture
def product_with_images(product_type, category):
    product = Product.objects.create(
        name='Test product', price=Money('10.00', 'USD'),
        product_type=product_type, category=category)
    file_mock_0 = MagicMock(spec=File, name='FileMock0')
    file_mock_0.name = 'image0.jpg'
    file_mock_1 = MagicMock(spec=File, name='FileMock1')
    file_mock_1.name = 'image1.jpg'
    product.images.create(image=file_mock_0)
    product.images.create(image=file_mock_1)
    return product


@pytest.fixture
def voucher(db):  # pylint: disable=W0613
    return Voucher.objects.create(code='mirumee', discount_value=20)


@pytest.fixture()
def order_with_lines(
        order, product_type, category, shipping_zone, vatlayer):
    taxes = vatlayer
    product = Product.objects.create(
        name='Test product', price=Money('10.00', 'USD'),
        product_type=product_type, category=category)
    variant = ProductVariant.objects.create(
        product=product, sku='SKU_A', cost_price=Money(1, 'USD'), quantity=5,
        quantity_allocated=3)
    order.lines.create(
        product_name=variant.display_product(),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=3,
        variant=variant,
        unit_price=variant.get_price(taxes=taxes),
        tax_rate=taxes['standard']['value'])

    product = Product.objects.create(
        name='Test product 2', price=Money('20.00', 'USD'),
        product_type=product_type, category=category)
    variant = ProductVariant.objects.create(
        product=product, sku='SKU_B', cost_price=Money(2, 'USD'), quantity=2,
        quantity_allocated=2)
    order.lines.create(
        product_name=variant.display_product(),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=2,
        variant=variant,
        unit_price=variant.get_price(taxes=taxes),
        tax_rate=taxes['standard']['value'])

    order.shipping_address = order.billing_address.get_copy()
    method = shipping_zone.shipping_methods.get()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.shipping_price = method.get_total(taxes)
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture()
def fulfilled_order(order_with_lines):
    order = order_with_lines
    fulfillment = order.fulfillments.create()
    line_1 = order.lines.first()
    line_2 = order.lines.last()
    fulfillment.lines.create(order_line=line_1, quantity=line_1.quantity)
    fulfill_order_line(line_1, line_1.quantity)
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity)
    fulfill_order_line(line_2, line_2.quantity)
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=['status'])
    return order


@pytest.fixture
def fulfillment(fulfilled_order):
    return fulfilled_order.fulfillments.first()


@pytest.fixture
def draft_order(order_with_lines):
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.save(update_fields=['status'])
    return order_with_lines


@pytest.fixture()
def payment_waiting(order_with_lines):
    return order_with_lines.payments.create(
        variant='default', status=PaymentStatus.WAITING,
        fraud_status=FraudStatus.ACCEPT, currency='USD',
        total=order_with_lines.total_gross.amount)


@pytest.fixture()
def payment_preauth(order_with_lines):
    return order_with_lines.payments.create(
        variant='default', status=PaymentStatus.PREAUTH,
        fraud_status=FraudStatus.ACCEPT, currency='USD',
        total=order_with_lines.total.gross.amount,
        tax=order_with_lines.total.tax.amount)


@pytest.fixture()
def payment_confirmed(order_with_lines):
    order_amount = order_with_lines.total_gross.amount
    return order_with_lines.payments.create(
        variant='default', status=PaymentStatus.CONFIRMED,
        fraud_status=FraudStatus.ACCEPT, currency='USD',
        total=order_amount, captured_amount=order_amount,
        tax=order_with_lines.total.tax.amount)


@pytest.fixture()
def payment_rejected(order_with_lines):
    return order_with_lines.payments.create(
        variant='default', status=PaymentStatus.REJECTED,
        fraud_status=FraudStatus.ACCEPT, currency='USD',
        total=order_with_lines.total_gross.amount)


@pytest.fixture()
def payment_refunded(order_with_lines):
    return order_with_lines.payments.create(
        variant='default', status=PaymentStatus.REFUNDED,
        fraud_status=FraudStatus.ACCEPT, currency='USD',
        total=order_with_lines.total_gross.amount)


@pytest.fixture()
def payment_error(order_with_lines):
    return order_with_lines.payments.create(
        variant='default', status=PaymentStatus.ERROR,
        fraud_status=FraudStatus.ACCEPT, currency='USD',
        total=order_with_lines.total_gross.amount)


@pytest.fixture()
def payment_input(order_with_lines):
    return order_with_lines.payments.create(
        variant='default', status=PaymentStatus.INPUT,
        fraud_status=FraudStatus.ACCEPT, currency='USD',
        total=order_with_lines.total_gross.amount)


@pytest.fixture()
def sale(category, collection):
    sale = Sale.objects.create(name="Sale", value=5)
    sale.categories.add(category)
    sale.collections.add(collection)
    return sale


@pytest.fixture
def authorization_key(site_settings):
    return AuthorizationKey.objects.create(
        site_settings=site_settings, name='Backend', key='Key',
        password='Password')


@pytest.fixture
def permission_manage_staff():
    return Permission.objects.get(codename='manage_staff')


@pytest.fixture
def permission_manage_products():
    return Permission.objects.get(codename='manage_products')


@pytest.fixture
def permission_manage_shipping():
    return Permission.objects.get(codename='manage_shipping')


@pytest.fixture
def permission_manage_users():
    return Permission.objects.get(codename='manage_users')


@pytest.fixture
def permission_manage_settings():
    return Permission.objects.get(codename='manage_settings')


@pytest.fixture
def permission_impersonate_users():
    return Permission.objects.get(codename='impersonate_users')


@pytest.fixture
def permission_manage_menus():
    return Permission.objects.get(codename='manage_menus')


@pytest.fixture
def collection(db):
    collection = Collection.objects.create(
        name='Collection', slug='collection', is_published=True)
    return collection


@pytest.fixture
def draft_collection(db):
    collection = Collection.objects.create(
        name='Draft collection', slug='draft-collection')
    return collection


@pytest.fixture
def page(db):
    data = {
        'slug': 'test-url',
        'title': 'Test page',
        'content': 'test content'}
    page = Page.objects.create(**data)
    return page


@pytest.fixture
def model_form_class():
    mocked_form_class = MagicMock(name='test', spec=ModelForm)
    mocked_form_class._meta = Mock(name='_meta')
    mocked_form_class._meta.model = 'test_model'
    mocked_form_class._meta.fields = 'test_field'
    return mocked_form_class


@pytest.fixture
def menu(db):
    return Menu.objects.get_or_create(name='test-navbar', json_content={})[0]


@pytest.fixture
def menu_item(menu):
    return MenuItem.objects.create(
        menu=menu,
        name='Link 1',
        url='http://example.com/')


@pytest.fixture
def menu_with_items(menu, category, collection):
    menu.items.create(name='Link 1', url='http://example.com/')
    menu_item = menu.items.create(name='Link 2', url='http://example.com/')
    menu.items.create(name=category.name, category=category, parent=menu_item)
    menu.items.create(
        name=collection.name, collection=collection, parent=menu_item)
    update_menu(menu)
    return menu


@pytest.fixture
def tax_rates():
    return {
        'standard_rate': 23,
        'reduced_rates': {
            'pharmaceuticals': 8,
            'medical': 8,
            'passenger transport': 8,
            'newspapers': 8,
            'hotels': 8,
            'restaurants': 8,
            'admission to cultural events': 8,
            'admission to sporting events': 8,
            'admission to entertainment events': 8,
            'foodstuffs': 5}}


@pytest.fixture
def taxes(tax_rates):
    taxes = {'standard': {
        'value': tax_rates['standard_rate'],
        'tax': get_tax_for_rate(tax_rates)}}
    if tax_rates['reduced_rates']:
        taxes.update({
            rate: {
                'value': tax_rates['reduced_rates'][rate],
                'tax': get_tax_for_rate(tax_rates, rate)}
            for rate in tax_rates['reduced_rates']})
    return taxes


@pytest.fixture
def vatlayer(db, settings, tax_rates, taxes):
    settings.VATLAYER_ACCESS_KEY = 'enablevatlayer'
    VAT.objects.create(country_code='PL', data=tax_rates)

    tax_rates_2 = {
        'standard_rate': 19,
        'reduced_rates': {
            'admission to cultural events': 7,
            'admission to entertainment events': 7,
            'books': 7,
            'foodstuffs': 7,
            'hotels': 7,
            'medical': 7,
            'newspapers': 7,
            'passenger transport': 7}}
    VAT.objects.create(country_code='DE', data=tax_rates_2)
    return taxes


@pytest.fixture
def translated_variant_fr(product):
    attribute = product.product_type.variant_attributes.first()
    return AttributeTranslation.objects.create(
        language_code='fr', attribute=attribute,
        name='Name tranlsated to french')


@pytest.fixture
def translated_attribute(product):
    attribute = product.product_type.product_attributes.first()
    return AttributeTranslation.objects.create(
        language_code='fr', attribute=attribute,
        name='Name tranlsated to french')


@pytest.fixture
def voucher_translation_fr(voucher):
    return VoucherTranslation.objects.create(
        language_code='fr', voucher=voucher, name='French name')


@pytest.fixture
def product_translation_fr(product):
    return ProductTranslation.objects.create(
        language_code='fr', product=product, name='French name',
        description='French description')
