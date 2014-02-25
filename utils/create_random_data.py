from __future__ import unicode_literals
import random
import os

from faker import Factory
from django.core.files import File

from saleor.product.models import (Shirt, ShirtVariant, ProductCollection,
                                   Bag, BagVariant, ProductImage)
from saleor.product.models import Category, Color


fake = Factory.create()


def create_color(**kwargs):
    r = lambda: random.randint(0, 255)

    defaults = {
        'name': fake.word(),
        'color': '%02X%02X%02X' % (r(), r(), r())
    }
    defaults.update(kwargs)

    return Color.objects.create(**defaults)


def create_category(**kwargs):
    defaults = {
        'name': fake.word(),
        'description': fake.text()
    }
    defaults['slug'] = fake.slug(defaults['name'])
    defaults.update(kwargs)

    return Category.objects.create(**defaults)


def create_product(product_type, **kwargs):
    defaults = {
        'name': fake.company(),
        'category': Category.objects.order_by('?')[0],
        'collection': ProductCollection.objects.order_by('?')[0],
        'color': Color.objects.order_by('?')[0],
        'weight': fake.random_digit(),
    }
    defaults.update(kwargs)

    return product_type.objects.create(**defaults)


def create_variant(product, **kwargs):
    defaults = {
        'stock': fake.random_int(),
        'name': fake.word(),
        'price': fake.pyfloat(2, 2, positive=True),
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


def create_shirt(**kwargs):
    return create_product(Shirt, **kwargs)


def create_bag(**kwargs):
    return create_product(Bag, **kwargs)


def create_items(placeholder_dir, how_many=10):
    if Color.objects.count() < 2:
        create_color()
    shirt_category = create_category(name='Shirts')
    bag_category = create_category(name='Grocery bags')

    if ProductCollection.objects.count() < 2:
        ProductCollection.objects.create(name="Test")

    for i in range(how_many):
        # Shirt
        shirt = create_shirt(category=shirt_category)
        create_product_image(shirt, placeholder_dir)
        # Bag
        bag = create_bag(category=bag_category, collection=None)
        create_product_image(bag, placeholder_dir)
        # chance to generate couple of sizes
        for size in ShirtVariant.SIZE_CHOICES:
            if random.choice([True, False]):
                create_variant(shirt, size=size[0])

        create_variant(bag)

        print("Shirt - %s %s Variants" % (shirt, shirt.variants.count()))
        print("Bag - %s %s Variants" % (bag, bag.variants.count()))