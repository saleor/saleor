from collections import defaultdict
import itertools
import os
import random
import unicodedata

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.files import File
from django.template.defaultfilters import slugify
from faker import Factory
from faker.providers import BaseProvider
from payments import PaymentStatus
from prices import Price

from ...discount import DiscountValueType, VoucherType
from ...discount.models import Sale, Voucher
from ...order import GroupStatus
from ...order.models import DeliveryGroup, Order, OrderLine, Payment
from ...product.models import (
    AttributeChoiceValue, Category, Collection, Product, ProductAttribute,
    ProductImage, ProductType, ProductVariant, Stock, StockLocation)
from ...shipping.models import ANY_COUNTRY, ShippingMethod
from ...userprofile.models import Address, User
from ...userprofile.utils import store_user_address

fake = Factory.create()
STOCK_LOCATION = 'default'

DEFAULT_CATEGORY = 'Default'

DELIVERY_REGIONS = [ANY_COUNTRY, 'US', 'PL', 'DE', 'GB']

DEFAULT_SCHEMA = {
    'T-Shirt': {
        'category': 'Apparel',
        'product_attributes': {
            'Color': ['Blue', 'White'],
            'Collar': ['Round', 'V-Neck', 'Polo'],
            'Brand': ['Saleor']},
        'variant_attributes': {
            'Size': ['XS', 'S', 'M', 'L', 'XL', 'XXL']},
        'images_dir': 't-shirts/',
        'is_shipping_required': True},
    'Mugs': {
        'category': 'Accessories',
        'product_attributes': {
            'Brand': ['Saleor']},
        'variant_attributes': {},
        'images_dir': 'mugs/',
        'is_shipping_required': True},
    'Coffee': {
        'category': 'Groceries',
        'product_attributes': {
            'Coffee Genre': ['Arabica', 'Robusta'],
            'Brand': ['Saleor']},
        'variant_attributes': {
            'Box Size': ['100g', '250g', '500g', '1kg']},
        'different_variant_prices': True,
        'images_dir': 'coffee/',
        'is_shipping_required': True},
    'Candy': {
        'category': 'Groceries',
        'product_attributes': {
            'Flavor': ['Sour', 'Sweet'],
            'Brand': ['Saleor']},
        'variant_attributes': {
            'Candy Box Size': ['100g', '250g', '500g']},
        'images_dir': 'candy/',
        'is_shipping_required': True},
    'E-books': {
        'category': 'Books',
        'product_attributes': {
            'Author': ['John Doe', 'Milionare Pirate'],
            'Publisher': ['Mirumee Press', 'Saleor Publishing'],
            'Language': ['English', 'Pirate']},
        'variant_attributes': {},
        'images_dir': 'books/',
        'is_shipping_required': False},
    'Books': {
        'category': 'Books',
        'product_attributes': {
            'Author': ['John Doe', 'Milionare Pirate'],
            'Publisher': ['Mirumee Press', 'Saleor Publishing'],
            'Language': ['English', 'Pirate']},
        'variant_attributes': {
            'Cover': ['Soft', 'Hard']},
        'images_dir': 'books/',
        'is_shipping_required': True}}


def create_attributes_and_values(attribute_data):
    attributes = []
    for attribute_name, attribute_values in attribute_data.items():
        attribute = create_attribute(
            slug=slugify(attribute_name), name=attribute_name)
        for value in attribute_values:
            create_attribute_value(attribute, name=value)
        attributes.append(attribute)
    return attributes


def create_product_type_with_attributes(name, schema):
    product_attributes_schema = schema.get('product_attributes', {})
    variant_attributes_schema = schema.get('variant_attributes', {})
    is_shipping_required = schema.get('is_shipping_required', True)
    product_type = get_or_create_product_type(
        name=name, is_shipping_required=is_shipping_required)
    product_attributes = create_attributes_and_values(
        product_attributes_schema)
    variant_attributes = create_attributes_and_values(
        variant_attributes_schema)
    product_type.product_attributes.add(*product_attributes)
    product_type.variant_attributes.add(*variant_attributes)
    return product_type


def create_product_types_by_schema(root_schema):
    results = []
    for product_type_name, schema in root_schema.items():
        product_type = create_product_type_with_attributes(
            product_type_name, schema)
        results.append((product_type, schema))
    return results


def set_product_attributes(product, product_type):
    attr_dict = {}
    for product_attribute in product_type.product_attributes.all():
        value = random.choice(product_attribute.values.all())
        attr_dict[str(product_attribute.pk)] = str(value.pk)
    product.attributes = attr_dict
    product.save(update_fields=['attributes'])


def set_variant_attributes(variant, product_type):
    attr_dict = {}
    existing_variants = variant.product.variants.values_list(
        'attributes', flat=True)
    existing_variant_attributes = defaultdict(list)
    for variant_attrs in existing_variants:
        for attr_id, value_id in variant_attrs.items():
            existing_variant_attributes[attr_id].append(value_id)

    for product_attribute in product_type.variant_attributes.all():
        available_values = product_attribute.values.exclude(
            pk__in=[int(pk) for pk
                    in existing_variant_attributes[str(product_attribute.pk)]])
        if not available_values:
            return
        value = random.choice(available_values)
        attr_dict[str(product_attribute.pk)] = str(value.pk)
    variant.attributes = attr_dict
    variant.save(update_fields=['attributes'])


def get_variant_combinations(product):
    # Returns all possible variant combinations
    # For example: product type has two variant attributes: Size, Color
    # Size has available values: [S, M], Color has values [Red, Green]
    # All combinations will be generated (S, Red), (S, Green), (M, Red),
    # (M, Green)
    # Output is list of dicts, where key is product attribute id and value is
    # attribute value id. Casted to string.
    variant_attr_map = {
        attr: attr.values.all()
        for attr in product.product_type.variant_attributes.all()}
    all_combinations = itertools.product(*variant_attr_map.values())
    return [
        {str(attr_value.attribute.pk): str(attr_value.pk)
         for attr_value in combination}
        for combination in all_combinations]


def get_price_override(schema, combinations_num, current_price):
    prices = []
    if schema.get('different_variant_prices'):
        prices = sorted(
            [current_price + fake.price() for _ in range(combinations_num)],
            reverse=True)
    return prices


def create_products_by_type(
        product_type, schema, placeholder_dir, how_many=10, create_images=True,
        stdout=None):
    category_name = schema.get('category') or DEFAULT_CATEGORY
    category = get_or_create_category(category_name)

    for dummy in range(how_many):
        product = create_product(
            product_type=product_type, category=category)
        set_product_attributes(product, product_type)
        if create_images:
            type_placeholders = os.path.join(
                placeholder_dir, schema['images_dir'])
            create_product_images(
                product, random.randrange(1, 5), type_placeholders)
        variant_combinations = get_variant_combinations(product)

        prices = get_price_override(
            schema, len(variant_combinations), product.price)
        variants_with_prices = itertools.zip_longest(
            variant_combinations, prices)

        for i, variant_price in enumerate(variants_with_prices, start=1337):
            attr_combination, price = variant_price
            sku = '%s-%s' % (product.pk, i)
            create_variant(
                product, attributes=attr_combination, sku=sku,
                price_override=price)

        if not variant_combinations:
            # Create min one variant for products without variant level attrs
            sku = '%s-%s' % (product.pk, fake.random_int(1000, 100000))
            create_variant(product, sku=sku)
        if stdout is not None:
            stdout.write('Product: %s (%s), %s variant(s)' % (
                product, product_type.name, len(variant_combinations) or 1))


def create_products_by_schema(placeholder_dir, how_many, create_images,
                              stdout=None, schema=DEFAULT_SCHEMA):
    for product_type, type_schema in create_product_types_by_schema(schema):
        create_products_by_type(
            product_type, type_schema, placeholder_dir,
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


def get_or_create_product_type(name, **kwargs):
    return ProductType.objects.get_or_create(name=name, defaults=kwargs)[0]


def get_or_create_collection(name, **kwargs):
    kwargs['slug'] = fake.slug(name)
    return Collection.objects.get_or_create(name=name, defaults=kwargs)[0]


def create_product(**kwargs):
    defaults = {
        'name': fake.company(),
        'price': fake.price(),
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
    slug = fake.word()
    defaults = {
        'slug': slug,
        'name': slug.title()}
    defaults.update(kwargs)
    attribute = ProductAttribute.objects.get_or_create(**defaults)[0]
    return attribute


def create_attribute_value(attribute, **kwargs):
    name = fake.word()
    defaults = {
        'attribute': attribute,
        'name': name}
    defaults.update(kwargs)
    defaults['slug'] = slugify(defaults['name'])
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
    status = random.choice(
        [
            PaymentStatus.WAITING,
            PaymentStatus.PREAUTH,
            PaymentStatus.CONFIRMED])
    payment = Payment.objects.create(
        order=order,
        status=status,
        variant='default',
        transaction_id=str(fake.random_int(1, 100000)),
        currency=settings.DEFAULT_CURRENCY,
        total=order.get_total().gross,
        delivery=order.shipping_price.gross,
        customer_ip_address=fake.ipv4(),
        billing_first_name=order.billing_address.first_name,
        billing_last_name=order.billing_address.last_name,
        billing_address_1=order.billing_address.street_address_1,
        billing_city=order.billing_address.city,
        billing_postcode=order.billing_address.postal_code,
        billing_country_code=order.billing_address.country)
    if status == PaymentStatus.CONFIRMED:
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
        status=random.choice([GroupStatus.NEW, GroupStatus.SHIPPED]),
        order=order,
        shipping_method_name=str(shipping_country))
    return delivery_group


def create_order_line(delivery_group):
    product = Product.objects.all().order_by('?')[0]
    variant = product.variants.all()[0]
    quantity = random.randrange(1, 5)
    stock = variant.stock.first()
    stock.quantity += quantity
    stock.quantity_allocated += quantity
    stock.save()
    return OrderLine.objects.create(
        delivery_group=delivery_group,
        product=product,
        product_name=product.name,
        product_sku=variant.sku,
        is_shipping_required=product.product_type.is_shipping_required,
        quantity=quantity,
        stock=stock,
        stock_location=stock.location.name,
        unit_price_net=product.price.net,
        unit_price_gross=product.price.gross)


def create_order_lines(delivery_group, how_many=10):
    for dummy in range(how_many):
        yield create_order_line(delivery_group)


def create_fake_order():
    user = random.choice([None, User.objects.filter(
        is_superuser=False).order_by('?').first()])
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

    delivery_group = create_delivery_group(order)
    lines = create_order_lines(delivery_group, random.randrange(1, 5))

    order.total = sum(
        [line.get_total() for line in lines], order.shipping_price)
    order.save()

    create_payment(delivery_group)
    return order


def create_fake_sale():
    sale = Sale.objects.create(
        name='Happy %s day!' % fake.word(),
        type=DiscountValueType.PERCENTAGE,
        value=random.choice([10, 20, 30, 40, 50]))
    for product in Product.objects.all().order_by('?')[:4]:
        sale.products.add(product)
    return sale


def create_users(how_many=10):
    for dummy in range(how_many):
        user = create_fake_user()
        yield 'User: %s' % (user.email,)


def create_orders(how_many=10):
    for dummy in range(how_many):
        order = create_fake_order()
        yield 'Order: %s' % (order,)


def create_product_sales(how_many=5):
    for dummy in range(how_many):
        sale = create_fake_sale()
        yield 'Sale: %s' % (sale,)


def create_shipping_methods():
    shipping_method = ShippingMethod.objects.create(name='UPC')
    shipping_method.price_per_country.create(price=fake.price())
    yield 'Shipping method #%d' % shipping_method.id
    shipping_method = ShippingMethod.objects.create(name='DHL')
    shipping_method.price_per_country.create(price=fake.price())
    yield 'Shipping method #%d' % shipping_method.id


def create_vouchers():
    voucher, created = Voucher.objects.get_or_create(
        code='FREESHIPPING', defaults={
            'type': VoucherType.SHIPPING,
            'name': 'Free shipping',
            'discount_value_type': DiscountValueType.PERCENTAGE,
            'discount_value': 100})
    if created:
        yield 'Voucher #%d' % voucher.id
    else:
        yield 'Shipping voucher already exists'

    voucher, created = Voucher.objects.get_or_create(
        code='DISCOUNT', defaults={
            'type': VoucherType.VALUE,
            'name': 'Big order discount',
            'discount_value_type': DiscountValueType.FIXED,
            'discount_value': 25,
            'limit': 200})
    if created:
        yield 'Voucher #%d' % voucher.id
    else:
        yield 'Value voucher already exists'


def create_fake_group():
    group, _ = Group.objects.get_or_create(name='Products Manager')
    group.permissions.add(Permission.objects.get(codename='edit_product'))
    group.permissions.add(Permission.objects.get(codename='view_product'))
    group.save()
    return group


def create_groups():
    group = create_fake_group()
    return 'Group: %s' % (group.name)


def set_featured_products(how_many=8):
    pks = Product.objects.order_by('?')[:how_many].values_list('pk', flat=True)
    Product.objects.filter(pk__in=pks).update(is_featured=True)
    yield 'Featured products created'


def add_address_to_admin(email):
    address = create_address()
    user = User.objects.get(email=email)
    store_user_address(user, address, True, True)


def create_fake_collection():
    collection = get_or_create_collection(name='%s collection' % fake.word())
    products = Product.objects.order_by('?')[:4]
    collection.products.add(*products)
    return collection


def create_collections(how_many=2):
    for dummy in range(how_many):
        collection = create_fake_collection()
        yield 'Collection: %s' % (collection,)
