from __future__ import unicode_literals

import csv
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from saleor.product.models import Category
from saleor.integrations.feeds import SaleorGoogleMerchant
from saleor.integrations.utils import update_feed


def test_saleor_feed_items(product_in_stock):
    valid_variant = product_in_stock.variants.first()
    feed = SaleorGoogleMerchant()
    items = feed.items()
    assert len(items) == 1
    attributes = feed.item_attributes(items[0])
    assert attributes.get('mpn') == valid_variant.sku
    assert attributes.get('availability') == 'in stock'


def test_category_formatter(db):
    feed = SaleorGoogleMerchant()
    main_category = Category(name='Main', slug='main')
    main_category.save()
    sub_category = Category(name='Sub', slug='sub', parent=main_category)
    sub_category.save()
    assert feed.get_full_category_name_path(main_category) == 'Main'
    assert feed.get_full_category_name_path(sub_category) == 'Main > Sub'


def test_feed_updater(product_in_stock, monkeypatch):
    variant = product_in_stock.variants.first()
    fake_file = StringIO()
    fake_file.__exit__ = lambda x, y, z: None
    fake_file.close = lambda: None
    fake_file.__enter__ = lambda: fake_file
    monkeypatch.setattr('saleor.integrations.utils.default_storage.open',
                        lambda path, mode: fake_file)
    feed = SaleorGoogleMerchant()
    feed.compression = False
    update_feed(feed)
    fake_file.seek(0)
    reader = csv.DictReader(fake_file, dialect=csv.excel_tab)
    for generated_item in reader:
        attributes = feed.item_attributes(variant)
        for key in attributes.keys():
            assert attributes[key] == generated_item[key]
