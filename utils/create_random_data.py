from __future__ import unicode_literals
import random
import os

from faker import Factory
from django.core.files import File

from saleor.product.models import (Shirt, ShirtVariant,
                                   Bag, BagVariant, ProductImage)
from saleor.product.models import Category, Color


fake = Factory.create()
PRODUCT_COLLECTIONS = fake.words(10)


def create_color(**kwargs):
    r = lambda: random.randint(0, 255)

    defaults = {
        'name': fake.word(),
        'color': '%02X%02X%02X' % (r(), r(), r())
    }
    defaults.update(kwargs)

    return Color.objects.create(**defaults)


def get_or_create_category(name, **kwargs):
    defaults = {
        'description': fake.text()
    }
    defaults.update(kwargs)
    defaults['slug'] = fake.slug(name)

    return Category.objects.get_or_create(name=name, defaults=defaults)[0]


def create_product(product_type, **kwargs):
    if random.choice([True, False]):
        collection = random.choice(PRODUCT_COLLECTIONS)
    else:
        collection = ''

    defaults = {
        'name': fake.company(),
        'price': fake.pyfloat(2, 2, positive=True),
        'category': Category.objects.order_by('?')[0],
        'collection': collection,
        'color': Color.objects.order_by('?')[0],
        'weight': fake.random_digit(),
        'description': '\n\n'.join(fake.paragraphs(5))
    }
    defaults.update(kwargs)

    return product_type.objects.create(**defaults)


def create_variant(product, **kwargs):
    defaults = {
        'stock': fake.random_int(),
        'name': fake.word(),
        'sku': fake.random_int(1, 100000),
        'product': product
    }
    if isinstance(product, Shirt):
        if not 'size' in kwargs:
            defaults['size'] = random.choice(ShirtVariant.SIZE_CHOICES)[0]
        variant_class = ShirtVariant
    elif isinstance(product, Bag):
        variant_class = BagVariant
    else:
        raise NotImplemented
    defaults.update(kwargs)

    return variant_class.objects.create(**defaults)


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


def create_shirt(**kwargs):
    return create_product(Shirt, **kwargs)


def create_bag(**kwargs):
    return create_product(Bag, **kwargs)


def create_items(placeholder_dir, how_many=10):
    # Create few colors
    [create_color() for i in range(5)]

    shirt_category = get_or_create_category('Shirts')
    bag_category = get_or_create_category('Grocery bags')

    for i in range(how_many):
        # Shirt
        shirt = create_shirt(category=shirt_category)
        create_product_images(shirt, random.randrange(1, 5),
                              placeholder_dir + "shirts")
        # Bag
        bag = create_bag(category=bag_category, collection='')
        create_product_images(bag, random.randrange(1, 5),
                              placeholder_dir + "bags")
        # chance to generate couple of sizes
        for size in ShirtVariant.SIZE_CHOICES:
            # Create min. one size
            if shirt.variants.count() == 0:
                create_variant(shirt, size=size[0])
                continue
            if random.choice([True, False]):
                create_variant(shirt, size=size[0])

        create_variant(bag)

        yield "Shirt - %s %s Variants" % (shirt, shirt.variants.count())
        yield "Bag - %s %s Variants" % (bag, bag.variants.count())
