from __future__ import unicode_literals

import os
import random
import unicodedata

from django.conf import settings
from django.core.files import File
from faker import Factory
from faker.providers import BaseProvider
from prices import Price

from ...shipping.models import ShippingMethod, ShippingMethodCountry
from ...order.models import DeliveryGroup, Order, OrderedItem, Payment
from ...product.models import Category, Product, ProductImage, ProductVariant, Stock
from ...userprofile.models import Address, User

fake = Factory.create()
STOCK_LOCATION = 'default'

DELIVERY_REGIONS = [ShippingMethodCountry.ANY_COUNTRY, 'US', 'PL', 'DE', 'GB']


class SaleorProvider(BaseProvider):
    def price(self):
        return Price(fake.pydecimal(2, 2, positive=True),
                     currency=settings.DEFAULT_CURRENCY)

    def delivery_region(self):
        return random.choice(DELIVERY_REGIONS)

    def shipping_method(self):
        return random.choice(ShippingMethod.objects.all())
fake.add_provider(SaleorProvider)


def get_email(first_name, last_name):
    _first = unicodedata.normalize('NFD', first_name).encode('ascii', 'ignore')
    _last = unicodedata.normalize('NFD', last_name).encode('ascii', 'ignore')
    return '%s.%s@example.com' % (
        _first.lower().decode('utf-8'), _last.lower().decode('utf-8'))


def get_or_create_category(name, **kwargs):
    defaults = {
        'description': fake.text()}
    defaults.update(kwargs)
    defaults['slug'] = fake.slug(name)

    return Category.objects.get_or_create(name=name, defaults=defaults)[0]


def create_product(**kwargs):
    defaults = {
        'name': fake.company(),
        'price': fake.price(),
        'weight': fake.random_digit(),
        'description': '\n\n'.join(fake.paragraphs(5))}
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_stock(variant, **kwargs):
    defaults = {
        'variant': variant,
        'location': STOCK_LOCATION,
        'quantity': fake.random_int(1, 50)}
    defaults.update(kwargs)
    return Stock.objects.create(**defaults)


def create_variant(product, **kwargs):
    defaults = {
        'name': fake.word(),
        'sku': fake.random_int(1, 100000),
        'product': product}
    defaults.update(kwargs)
    variant = ProductVariant.objects.create(**defaults)
    create_stock(variant)
    return variant


def create_product_image(product, placeholder_dir):
    img_path = '%s/%s' % (placeholder_dir,
                          random.choice(os.listdir(placeholder_dir)))
    image = ProductImage(
        product=product,
        image=File(open(img_path, 'rb'))).save()
    return image


def create_product_images(product, how_many, placeholder_dir):
    for dummy in range(how_many):
        create_product_image(product, placeholder_dir)


def create_items(placeholder_dir, how_many=10, create_images=True):
    default_category = get_or_create_category('Default')

    for dummy in range(how_many):
        product = create_product()
        product.categories.add(default_category)
        if create_images:
            create_product_images(
                product, random.randrange(1, 5), placeholder_dir)
        num_variants = random.randrange(1, 5)
        for _ in range(num_variants):
            create_variant(product)
        yield 'Product: %s, %s variant(s)' % (product, num_variants)


def create_address():
    address = Address.objects.create(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        street_address_1=fake.street_address(),
        city=fake.city(),
        postal_code=fake.postcode(),
        country=fake.country_code())
    return address


def create_fake_user():
    address = create_address()
    email = get_email(address.first_name, address.last_name)

    user = User.objects.create_user(email=email, password='password')

    user.addresses.add(address)
    user.default_billing_address = address
    user.default_shipping_address = address
    user.is_active = True
    user.save()
    return user


def create_payment(delivery_group):
    order = delivery_group.order
    status = random.choice(['waiting', 'preauth', 'confirmed'])
    payment = Payment.objects.create(
        order=order,
        status=status,
        variant='default',
        transaction_id=str(fake.random_int(1, 100000)),
        currency=settings.DEFAULT_CURRENCY,
        total=order.get_total().gross,
        delivery=delivery_group.shipping_price.gross,
        customer_ip_address=fake.ipv4(),
        billing_first_name=order.billing_address.first_name,
        billing_last_name=order.billing_address.last_name,
        billing_address_1=order.billing_address.street_address_1,
        billing_city=order.billing_address.city,
        billing_postcode=order.billing_address.postal_code,
        billing_country_code=order.billing_address.country)
    if status == 'confirmed':
        payment.captured_amount = payment.total
        payment.save()
    return payment


def create_delivery_group(order):
    region = order.shipping_address.country
    if region not in DELIVERY_REGIONS:
        region = ShippingMethodCountry.ANY_COUNTRY
    shipping_method = fake.shipping_method()
    shipping_country = shipping_method.price_per_country.get_or_create(
        country_code=region, defaults={'price': fake.price()})[0]
    delivery_group = DeliveryGroup.objects.create(
        status=random.choice(['new', 'shipped']),
        order=order,
        shipping_method_name=str(shipping_country),
        shipping_price=shipping_country.price)
    return delivery_group


def create_order_line(delivery_group):
    product = Product.objects.all().order_by('?')[0]
    variant = product.variants.all()[0]
    return OrderedItem.objects.create(
        delivery_group=delivery_group,
        product=product,
        product_name=product.name,
        product_sku=variant.sku,
        quantity=random.randrange(1, 5),
        unit_price_net=product.price.net,
        unit_price_gross=product.price.gross)


def create_order_lines(delivery_group, how_many=10):
    for dummy in range(how_many):
        yield create_order_line(delivery_group)


def create_fake_order():
    user = random.choice([None, User.objects.filter(
        is_superuser=False).order_by('?')[0]])
    if user:
        user_data = {
            'user': user,
            'billing_address': user.default_billing_address,
            'shipping_address': user.default_shipping_address}
    else:
        address = create_address()
        user_data = {
            'billing_address': address,
            'shipping_address': address,
            'anonymous_user_email': get_email(
                address.first_name, address.last_name)}
    order = Order.objects.create(**user_data)
    order.change_status('payment-pending')

    delivery_group = create_delivery_group(order)
    lines = create_order_lines(delivery_group, random.randrange(1, 5))

    order.total = sum(
        [line.get_total() for line in lines], delivery_group.shipping_price)
    order.save()

    payment = create_payment(delivery_group)
    if payment.status == 'confirmed':
        order.change_status('fully-paid')
        if random.choice([True, False]):
            order.change_status('shipped')
    return order


def create_users(how_many=10):
    for dummy in range(how_many):
        user = create_fake_user()
        yield 'User: %s' % (user.email,)


def create_orders(how_many=10):
    for dummy in range(how_many):
        order = create_fake_order()
        yield 'Order: %s' % (order,)


def create_shipping_methods():
    shipping_method = ShippingMethod.objects.create(name='UPC')
    shipping_method.price_per_country.create(price=fake.price())
    yield 'Shipping method #%d' % shipping_method.id
    shipping_method = ShippingMethod.objects.create(name='DHL')
    shipping_method.price_per_country.create(price=fake.price())
    yield 'Shipping method #%d' % shipping_method.id
