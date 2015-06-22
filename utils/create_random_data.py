from __future__ import unicode_literals
import os
import random
import unicodedata

from faker import Factory
from django.core.files import File

from saleor.product.models import (Product, ProductVariant, ProductImage, Stock)
from saleor.product.models import Category
from saleor.userprofile.models import User, Address

fake = Factory.create()
PRODUCT_COLLECTIONS = fake.words(10)
STOCK_LOCATION = 'default'


def get_or_create_category(name, **kwargs):
    defaults = {
        'description': fake.text()
    }
    defaults.update(kwargs)
    defaults['slug'] = fake.slug(name)

    return Category.objects.get_or_create(name=name, defaults=defaults)[0]


def create_product(**kwargs):
    if random.choice([True, False]):
        collection = random.choice(PRODUCT_COLLECTIONS)
    else:
        collection = ''

    defaults = {
        'name': fake.company(),
        'price': fake.pyfloat(2, 2, positive=True),
        'collection': collection,
        'weight': fake.random_digit(),
        'description': '\n\n'.join(fake.paragraphs(5))
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_variant(product, **kwargs):
    defaults = {
        'name': fake.word(),
        'sku': fake.random_int(1, 100000),
        'product': product,
    }
    defaults.update(kwargs)
    return ProductVariant.objects.create(**defaults)


def create_stock(product, **kwargs):
    for variant in product.variants.all():
        _create_stock(variant, **kwargs)


def _create_stock(variant, **kwargs):
    defaults = {
        'variant': variant,
        'location': STOCK_LOCATION,
        'quantity': fake.random_int(1, 50)
    }
    defaults.update(kwargs)
    return Stock.objects.create(**defaults)


def create_product_image(product, placeholder_dir):
    img_path = "%s/%s" % (placeholder_dir,
                          random.choice(os.listdir(placeholder_dir)))
    image = ProductImage(
        product=product,
        image=File(open(img_path, 'rb'))
    ).save()

    return image


def create_product_images(product, how_many, placeholder_dir):
    for i in range(how_many):
        create_product_image(product, placeholder_dir)


def create_items(placeholder_dir, how_many=10):
    default_category = get_or_create_category('Default')

    for i in range(how_many):
        product = create_product(collection='')
        product.categories.add(default_category)

        create_variant(product)  # ensure at least one variant
        create_product_images(product, random.randrange(1, 5), placeholder_dir)

        for _ in range(random.randrange(1, 5)):
            if random.choice([True, False]):
                create_variant(product)

        create_stock(product)
        yield "Product - %s %s Variants" % (product, product.variants.count())


def create_fake_user():
    first_name = fake.first_name()
    last_name = fake.last_name()

    _first = unicodedata.normalize('NFD', first_name).encode('ascii', 'ignore')
    _last = unicodedata.normalize('NFD', last_name).encode('ascii', 'ignore')

    email = u'%s.%s@example.com' % (_first.lower(), _last.lower())

    user = User.objects.create_user(email=email, password='password')

    address = Address.objects.create(
        first_name=first_name,
        last_name=last_name,
        street_address_1=fake.street_address(),
        city=fake.city(),
        postal_code=fake.postcode(),
        country=fake.country_code())

    user.addresses.add(address)
    user.default_billing_address = address
    user.default_shipping_address = address
    user.is_active = True
    user.save()
    return user


def create_users(how_many=10):
    for i in range(how_many):
        user = create_fake_user()
        yield "User - %s" % user.email
