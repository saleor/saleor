from __future__ import unicode_literals

import itertools
import os
import random
import unicodedata
from collections import defaultdict

from django.conf import settings
from django.core.files import File
from django.template.defaultfilters import slugify
from faker import Factory
from faker.providers import BaseProvider
from prices import Price

from ...order.models import DeliveryGroup, Order, OrderedItem, Payment
from ...product.models import (AttributeChoiceValue, Category, Product,
                               ProductAttribute, ProductClass, ProductImage,
                               ProductVariant, Stock, StockLocation)
from ...shipping.models import ANY_COUNTRY, ShippingMethod
from ...userprofile.models import Address, User

fake = Factory.create()
STOCK_LOCATION = 'default'

DELIVERY_REGIONS = [ANY_COUNTRY, 'US', 'PL', 'DE', 'GB']

DEFAULT_SCHEMA = {
    'T-Shirt': {
        'product_attributes': {
            'Color': ['Blue', 'White'],
            'Collar': ['Round', 'V-Neck', 'Polo'],
            'Brand': ['Saleor']
        },
        'variant_attributes': {
            'Size': ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        },
        'images_dir': 't-shirts/',
    },
    'Mugs': {
        'product_attributes': {
            'Brand': ['Saleor']
        },
        'variant_attributes': {},
        'images_dir': 'mugs/'
    },
    'Coffee': {
        'product_attributes': {
            'Coffee Genre': ['Arabica', 'Robusta'],
            'Brand': ['Saleor']
        },
        'variant_attributes': {
            'Box Size': ['100g', '250g', '500g', '1kg']
        },
        'different_variant_prices': True,
        'images_dir': 'coffee/',
    },
    'Candy': {
        'product_attributes': {
            'Flavor': ['Sour', 'Sweet'],
            'Brand': ['Saleor']
        },
        'variant_attributes': {
            'Candy Box Size': ['100g', '250g', '500g']
        },
        'images_dir': 'candy/',
        'different_variant_prices': True
    },
}


def create_attributes_and_values(schema, attribute_key):
    attributes = []
    attribute_data = schema.get(attribute_key, {})
    for attribute_name, attribute_values in attribute_data.items():
        attribute = create_attribute(
            name=slugify(attribute_name), display=attribute_name)
        for value in attribute_values:
            create_attribute_value(attribute, display=value)
        attributes.append(attribute)
    return attributes


def create_product_class_with_attributes(name, schema):
    product_class = get_or_create_product_class(name=name)
    product_attributes = create_attributes_and_values(
        schema, 'product_attributes')
    variant_attributes = create_attributes_and_values(
        schema, 'variant_attributes')
    product_class.product_attributes.add(*product_attributes)
    product_class.variant_attributes.add(*variant_attributes)
    return product_class


def create_product_classes_by_schema(root_schema):
    results = []
    for product_class_name, schema in root_schema.items():
        product_class = create_product_class_with_attributes(
            product_class_name, schema)
        results.append((product_class, schema))
    return results


def set_product_attributes(product, product_class):
    attr_dict = {}
    for product_attribute in product_class.product_attributes.all():
        value = random.choice(product_attribute.values.all())
        attr_dict[str(product_attribute.pk)] = str(value.pk)
    product.attributes = attr_dict
    product.save(update_fields=['attributes'])


def set_variant_attributes(variant, product_class):
    attr_dict = {}
    existing_variants = variant.product.variants.values_list(
        'attributes', flat=True)
    existing_variant_attributes = defaultdict(list)
    for variant_attrs in existing_variants:
        for attr_id, value_id in variant_attrs.items():
            existing_variant_attributes[attr_id].append(value_id)

    for product_attribute in product_class.variant_attributes.all():
        available_values = product_attribute.values.exclude(
            pk__in=[int(pk) for pk in existing_variant_attributes[str(product_attribute.pk)]])
        if not available_values:
            return
        value = random.choice(available_values)
        attr_dict[str(product_attribute.pk)] = str(value.pk)
    variant.attributes = attr_dict
    variant.save(update_fields=['attributes'])


def get_variant_combinations(product):
    # Returns all possible variant combinations
    # For example: product class has two variant attributes: Size, Color
    # Size has available values: [S, M], Color has values [Red, Green]
    # All combinations will be generated (S, Red), (S, Green), (M, Red),
    # (M, Green)
    # Output is list of dicts, where key is product attribute id and value is
    # attribute value id. Casted to string.
    variant_attr_map = {attr: attr.values.all()
                        for attr in product.product_class.variant_attributes.all()}
    all_combinations = itertools.product(*variant_attr_map.values())
    return [{str(attr_value.attribute.pk): str(attr_value.pk)}
            for combination in all_combinations
            for attr_value in combination]


def get_price_override(schema):
    if schema.get('different_variant_prices'):
        return fake.price()


def create_items_by_class(product_class, schema,
                          placeholder_dir, how_many=10, create_images=True,
                          stdout=None):
    default_category = get_or_create_category('Default')

    for dummy in range(how_many):
        product = create_product(product_class=product_class)
        set_product_attributes(product, product_class)
        product.categories.add(default_category)
        if create_images:
            class_placeholders = os.path.join(
                placeholder_dir, schema['images_dir'])
            create_product_images(
                product, random.randrange(1, 5), class_placeholders)
        variant_combinations = get_variant_combinations(product)
        for attr_combination in variant_combinations:
            create_variant(product, attributes=attr_combination,
                           price_override=get_price_override(schema))
        if not variant_combinations:
            # Create min one variant for products without variant level attrs
            create_variant(product)
        if stdout is not None:
            stdout.write('Product: %s (%s), %s variant(s)' % (
                product, product_class.name, len(variant_combinations) or 1))


def create_items_by_schema(placeholder_dir, how_many, create_images, stdout,
                           schema=DEFAULT_SCHEMA):
    for product_class, class_schema in create_product_classes_by_schema(schema):
        create_items_by_class(
            product_class, class_schema, placeholder_dir,
            how_many=how_many, create_images=create_images, stdout=stdout)


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


def get_or_create_product_class(name, **kwargs):
    return ProductClass.objects.get_or_create(name=name, defaults=kwargs)[0]


def create_product(**kwargs):
    defaults = {
        'name': fake.company(),
        'price': fake.price(),
        'weight': fake.random_digit(),
        'description': '\n\n'.join(fake.paragraphs(5))}
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_stock(variant, **kwargs):
    default_location = StockLocation.objects.get_or_create(
        name=STOCK_LOCATION)[0]
    defaults = {
        'variant': variant,
        'location': default_location,
        'quantity': fake.random_int(1, 50)}
    defaults.update(kwargs)
    return Stock.objects.create(**defaults)


def create_variant(product, **kwargs):
    defaults = {
        'name': fake.word(),
        'sku': '%s-%s' % (product.pk, fake.random_int(1, 100000)),
        'product': product}
    defaults.update(kwargs)
    variant = ProductVariant.objects.create(**defaults)
    create_stock(variant)
    return variant


def create_product_image(product, placeholder_dir):
    placeholder_root = os.path.join(settings.PROJECT_ROOT, placeholder_dir)
    img_path = '%s/%s' % (placeholder_dir,
                          random.choice(os.listdir(placeholder_root)))
    image = ProductImage(
        product=product,
        image=File(open(img_path, 'rb'))).save()
    return image


def create_attribute(**kwargs):
    name = fake.word()
    defaults = {
        'name': name,
        'display': name.title()}
    defaults.update(kwargs)
    attribute = ProductAttribute.objects.get_or_create(**defaults)[0]
    return attribute


def create_attribute_value(attribute, **kwargs):
    defaults = {
        'display': fake.word(),
        'attribute': attribute}
    defaults.update(kwargs)
    attribute_value = AttributeChoiceValue.objects.get_or_create(**defaults)[0]
    return attribute_value


def create_product_images(product, how_many, placeholder_dir):
    for dummy in range(how_many):
        create_product_image(product, placeholder_dir)


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
        region = ANY_COUNTRY
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
            'user_email': get_email(
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
