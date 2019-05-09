# coding=utf-8

from faker.providers import BaseProvider


class Provider(BaseProvider):

    safe_colors = (
        'fekete', 'bordó', 'zöld', 'királykék', 'oliva',
        'bíbor', 'kékeszöld', 'citromzöld', 'kék', 'ezüst',
        'szürke', 'sárga', 'mályva', 'akvamarin', 'fehér',
    )
