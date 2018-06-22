import itertools
import os
import random
import unicodedata

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.core.files import File
from django.template.defaultfilters import slugify
from django_countries.fields import Country
from faker import Factory
from faker.providers import BaseProvider
from payments import PaymentStatus
from prices import Money

from ...account.models import Address, User
from ...account.utils import store_user_address
from ...checkout import AddressType
from ...core.utils.taxes import get_tax_rate_by_name, get_taxes_for_country
from ...core.utils.text import strip_html_and_truncate
from ...discount import DiscountValueType, VoucherType
from ...discount.models import Sale, Voucher
from ...menu.models import Menu
from ...order.models import Fulfillment, Order, Payment
from ...order.utils import update_order_status
from ...page.models import Page
from ...product.models import (
    AttributeChoiceValue, Category, Collection, Product, ProductAttribute,
    ProductImage, ProductType, ProductVariant)
from ...product.thumbnails import create_product_thumbnails
from ...product.utils.attributes import get_name_from_attributes
from ...shipping.models import ANY_COUNTRY, ShippingMethod
from ...shipping.utils import get_taxed_shipping_price

fake = Factory.create()

DELIVERY_REGIONS = [ANY_COUNTRY, 'US', 'PL', 'DE', 'GB']
PRODUCTS_LIST_DIR = 'products-list/'

GROCERIES_CATEGORY = {'name': 'Groceries', 'image_name': 'groceries.jpg'}

DEFAULT_SCHEMA = {
    'T-Shirt': {
        'category': {
            'name': 'Apparel',
            'image_name': 'apparel.jpg'},
        'product_attributes': {
            'Color': ['Blue', 'White'],
            'Collar': ['Round', 'V-Neck', 'Polo'],
            'Brand': ['Saleor']},
        'variant_attributes': {
            'Size': ['XS', 'S', 'M', 'L', 'XL', 'XXL']},
        'images_dir': 't-shirts/',
        'is_shipping_required': True},
    'Mugs': {
        'category': {
            'name': 'Accessories',
            'image_name': 'accessories.jpg'},
        'product_attributes': {
            'Brand': ['Saleor']},
        'variant_attributes': {},
        'images_dir': 'mugs/',
        'is_shipping_required': True},
    'Coffee': {
        'category': {
            'name': 'Coffees',
            'image_name': 'coffees.jpg',
            'parent': GROCERIES_CATEGORY},
        'product_attributes': {
            'Coffee Genre': ['Arabica', 'Robusta'],
            'Brand': ['Saleor']},
        'variant_attributes': {
            'Box Size': ['100g', '250g', '500g', '1kg']},
        'different_variant_prices': True,
        'images_dir': 'coffee/',
        'is_shipping_required': True},
    'Candy': {
        'category': {
            'name': 'Candies',
            'image_name': 'candies.jpg',
            'parent': GROCERIES_CATEGORY},
        'product_attributes': {
            'Flavor': ['Sour', 'Sweet'],
            'Brand': ['Saleor']},
        'variant_attributes': {
            'Candy Box Size': ['100g', '250g', '500g']},
        'images_dir': 'candy/',
        'is_shipping_required': True},
    'E-books': {
        'category': {
            'name': 'Books',
            'image_name': 'books.jpg'},
        'product_attributes': {
            'Author': ['John Doe', 'Milionare Pirate'],
            'Publisher': ['Mirumee Press', 'Saleor Publishing'],
            'Language': ['English', 'Pirate']},
        'variant_attributes': {},
        'images_dir': 'books/',
        'is_shipping_required': False},
    'Books': {
        'category': {
            'name': 'Books',
            'image_name': 'books.jpg'},
        'product_attributes': {
            'Author': ['John Doe', 'Milionare Pirate'],
            'Publisher': ['Mirumee Press', 'Saleor Publishing'],
            'Language': ['English', 'Pirate']},
        'variant_attributes': {
            'Cover': ['Soft', 'Hard']},
        'images_dir': 'books/',
        'is_shipping_required': True}}
COLLECTIONS_SCHEMA = [
    {
        'name': 'Summer collection',
        'image_name': 'summer.jpg'},
    {
        'name': 'Winter sale',
        'image_name': 'sale.jpg'}]


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
            [current_price + fake.money() for _ in range(combinations_num)],
            reverse=True)
    return prices


def create_products_by_type(
        product_type, schema, placeholder_dir, how_many=10, create_images=True,
        stdout=None):
    category = get_or_create_category(schema['category'], placeholder_dir)

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
    def money(self):
        return Money(
            fake.pydecimal(2, 2, positive=True), settings.DEFAULT_CURRENCY)

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


def get_or_create_category(category_schema, placeholder_dir):
    if 'parent' in category_schema:
        parent_id = get_or_create_category(
            category_schema['parent'], placeholder_dir).id
    else:
        parent_id = None
    category_name = category_schema['name']
    image_name = category_schema['image_name']
    image_dir = get_product_list_images_dir(placeholder_dir)
    defaults = {
        'description': fake.text(),
        'slug': fake.slug(category_name),
        'background_image': get_image(image_dir, image_name)}
    return Category.objects.get_or_create(
        name=category_name, parent_id=parent_id, defaults=defaults)[0]


def get_or_create_product_type(name, **kwargs):
    return ProductType.objects.get_or_create(name=name, defaults=kwargs)[0]


def get_or_create_collection(name, placeholder_dir, image_name):
    background_image = get_image(placeholder_dir, image_name)
    defaults = {
        'slug': fake.slug(name),
        'background_image': background_image}
    return Collection.objects.get_or_create(name=name, defaults=defaults)[0]


def create_product(**kwargs):
    description = fake.paragraphs(5)
    defaults = {
        'name': fake.company(),
        'price': fake.money(),
        'description': '\n\n'.join(description),
        'seo_description': strip_html_and_truncate(description[0], 300)}
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_variant(product, **kwargs):
    defaults = {
        'product': product,
        'quantity': fake.random_int(1, 50),
        'cost_price': fake.money(),
        'quantity_allocated': fake.random_int(1, 50)}
    defaults.update(kwargs)
    variant = ProductVariant(**defaults)
    if variant.attributes:
        variant.name = get_name_from_attributes(variant)
    variant.save()
    return variant


def create_product_image(product, placeholder_dir):
    placeholder_root = os.path.join(settings.PROJECT_ROOT, placeholder_dir)
    image_name = random.choice(os.listdir(placeholder_root))
    image = get_image(placeholder_dir, image_name)
    product_image = ProductImage(product=product, image=image)
    product_image.save()
    create_product_thumbnails.delay(product_image.pk)
    return product_image


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


def create_payment(order):
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
        total=order.total.gross.amount,
        tax=order.total.tax.amount,
        delivery=order.shipping_price.net.amount,
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


def create_order_line(order, discounts, taxes):
    product = Product.objects.all().order_by('?')[0]
    variant = product.variants.all()[0]
    quantity = random.randrange(1, 5)
    variant.quantity += quantity
    variant.quantity_allocated += quantity
    variant.save()
    return order.lines.create(
        product_name=variant.display_product(),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=variant.get_price(discounts=discounts, taxes=taxes),
        tax_rate=get_tax_rate_by_name(variant.product.tax_rate, taxes))


def create_order_lines(order, discounts, taxes, how_many=10):
    for dummy in range(how_many):
        yield create_order_line(order, discounts, taxes)


def create_fulfillments(order):
    for line in order:
        if random.choice([False, True]):
            fulfillment, _ = Fulfillment.objects.get_or_create(order=order)
            quantity = random.randrange(0, line.quantity) + 1
            fulfillment.lines.create(order_line=line, quantity=quantity)
            line.quantity_fulfilled = quantity
            line.save(update_fields=['quantity_fulfilled'])

    update_order_status(order)


def create_fake_order(discounts, taxes):
    user = random.choice([None, User.objects.filter(
        is_superuser=False).order_by('?').first()])
    if user:
        order_data = {
            'user': user,
            'billing_address': user.default_billing_address,
            'shipping_address': user.default_shipping_address}
    else:
        address = create_address()
        order_data = {
            'billing_address': address,
            'shipping_address': address,
            'user_email': get_email(
                address.first_name, address.last_name)}

    shipping_method = ShippingMethod.objects.order_by('?').first()
    shipping_price = shipping_method.price_per_country.first().price
    shipping_price = get_taxed_shipping_price(shipping_price, taxes)
    order_data.update({
        'shipping_method_name': shipping_method.name,
        'shipping_price': shipping_price})

    order = Order.objects.create(**order_data)

    lines = create_order_lines(order, discounts, taxes, random.randrange(1, 5))

    order.total = sum(
        [line.get_total() for line in lines], order.shipping_price)
    order.save()

    create_fulfillments(order)

    create_payment(order)
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
    taxes = get_taxes_for_country(Country(settings.DEFAULT_COUNTRY))
    discounts = Sale.objects.prefetch_related('products', 'categories')
    for dummy in range(how_many):
        order = create_fake_order(discounts, taxes)
        yield 'Order: %s' % (order,)


def create_product_sales(how_many=5):
    for dummy in range(how_many):
        sale = create_fake_sale()
        yield 'Sale: %s' % (sale,)


def create_shipping_methods():
    shipping_method = ShippingMethod.objects.create(name='UPC')
    shipping_method.price_per_country.create(price=fake.money())
    yield 'Shipping method #%d' % shipping_method.id
    shipping_method = ShippingMethod.objects.create(name='DHL')
    shipping_method.price_per_country.create(price=fake.money())
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
    return 'Group: %s' % (group.name,)


def set_featured_products(how_many=8):
    pks = Product.objects.order_by('?')[:how_many].values_list('pk', flat=True)
    Product.objects.filter(pk__in=pks).update(is_featured=True)
    yield 'Featured products created'


def add_address_to_admin(email):
    address = create_address()
    user = User.objects.get(email=email)
    store_user_address(user, address, AddressType.BILLING)
    store_user_address(user, address, AddressType.SHIPPING)


def create_fake_collection(placeholder_dir, collection_data):
    image_dir = get_product_list_images_dir(placeholder_dir)
    collection = get_or_create_collection(
        name=collection_data['name'], placeholder_dir=image_dir,
        image_name=collection_data['image_name'])
    products = Product.objects.order_by('?')[:4]
    collection.products.add(*products)
    return collection


def create_collections_by_schema(placeholder_dir, schema=COLLECTIONS_SCHEMA):
    for collection_data in COLLECTIONS_SCHEMA:
        collection = create_fake_collection(placeholder_dir, collection_data)
        yield 'Collection: %s' % (collection,)


def create_page():
    content = """
    <h2 align="center">AN OPENSOURCE STOREFRONT PLATFORM FOR PERFECTIONISTS</h2>
    <h3 align="center">WRITTEN IN PYTHON, BEST SERVED AS A BESPOKE, HIGH-PERFORMANCE E-COMMERCE SOLUTION</h3>
    <p><br></p>
    <p><img src="http://getsaleor.com/images/main-pic.svg"></p>
    <p style="text-align: center;">
        <a href="https://github.com/mirumee/saleor/">Get Saleor</a> today!
    </p>
    """
    page_data = {'content': content, 'title': 'About', 'is_visible': True}
    page, dummy = Page.objects.get_or_create(slug='about', **page_data)
    yield 'Page %s created' % page.slug


def generate_menu_items(menu: Menu, category: Category, parent_menu_item):
    menu_item, created = menu.items.get_or_create(
        name=category.name, category=category, parent=parent_menu_item)

    if created:
        yield 'Created menu item for category %s' % category

    for child in category.get_children():
        for msg in generate_menu_items(menu, child, menu_item):
            yield '\t%s' % msg


def generate_menu_tree(menu):
    categories = Category.tree.get_queryset()
    for category in categories:
        if not category.parent_id:
            for msg in generate_menu_items(menu, category, None):
                yield msg


def create_menus():
    # Create navbar menu with category links
    top_menu, _ = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS['top_menu_name'])
    if not top_menu.items.exists():
        yield 'Created navbar menu'
        for msg in generate_menu_tree(top_menu):
            yield msg

    # Create footer menu with collections and pages
    bottom_menu, _ = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS['bottom_menu_name'])
    if not bottom_menu.items.exists():
        collection = Collection.objects.order_by('?')[0]
        item, _ = bottom_menu.items.get_or_create(
            name='Collections',
            collection=collection)

        for collection in Collection.objects.filter(
                background_image__isnull=False):
            bottom_menu.items.get_or_create(
                name=collection.name,
                collection=collection,
                parent=item)

        page = Page.objects.order_by('?')[0]
        bottom_menu.items.get_or_create(
            name=page.title,
            page=page)
        yield 'Created footer menu'
    site = Site.objects.get_current()
    site_settings = site.settings
    site_settings.top_menu = top_menu
    site_settings.bottom_menu = bottom_menu
    site_settings.save()


def get_product_list_images_dir(placeholder_dir):
    product_list_images_dir = os.path.join(
        placeholder_dir, PRODUCTS_LIST_DIR)
    return product_list_images_dir


def get_image(image_dir, image_name):
    img_path = os.path.join(image_dir, image_name)
    return File(open(img_path, 'rb'))
