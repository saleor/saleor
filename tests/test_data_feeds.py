from __future__ import unicode_literals

import csv
from mock import Mock
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from django.contrib.sites.models import Site

from saleor.discount.models import Sale
from saleor.product.models import Category
from saleor.data_feeds.google_merchant import (get_feed_items,
                                               item_attributes,
                                               item_google_product_category,
                                               update_feed)


def test_saleor_feed_items(product_in_stock):
    valid_variant = product_in_stock.variants.first()
    items = get_feed_items()
    assert len(items) == 1
    categories = Category.objects.all()
    discounts = []
    category_paths = {}
    current_site = Site.objects.get_current()
    attributes = item_attributes(items[0], categories, category_paths,
                                 current_site, discounts)
    assert attributes.get('mpn') == valid_variant.sku
    assert attributes.get('availability') == 'in stock'


def test_category_formatter(db):
    main_category = Category(name='Main', slug='main')
    main_category.save()
    main_category_item = Mock(
        product=Mock(get_first_category=lambda: main_category))
    sub_category = Category(name='Sub', slug='sub', parent=main_category)
    sub_category.save()
    sub_category_item = Mock(
        product=Mock(get_first_category=lambda: sub_category))
    assert item_google_product_category(
        main_category_item, {}) == 'Main'
    assert item_google_product_category(
        sub_category_item, {}) == 'Main > Sub'


def test_feed_updater(product_in_stock, monkeypatch):
    variant = product_in_stock.variants.first()
    fake_file = StringIO()
    fake_file.__exit__ = lambda x, y, z: None
    fake_file.close = lambda: None
    fake_file.__enter__ = lambda: fake_file
    monkeypatch.setattr(
        'saleor.data_feeds.google_merchant.default_storage.open',
        lambda path, mode: fake_file)
    monkeypatch.setattr(
        'saleor.data_feeds.google_merchant.COMPRESSION', False)
    update_feed()
    fake_file.seek(0)
    categories = Category.objects.all()
    discounts = Sale.objects.all().prefetch_related('products',
                                                    'categories')
    category_paths = {}
    current_site = Site.objects.get_current()
    reader = csv.DictReader(fake_file, dialect=csv.excel_tab)
    for generated_item in reader:
        attributes = item_attributes(variant, categories, category_paths,
                                     current_site, discounts)
        for key in attributes.keys():
            assert attributes[key] == generated_item[key]
