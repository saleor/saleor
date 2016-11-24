from __future__ import unicode_literals

from saleor.product.models import Category
from saleor.integrations.feeds import SaleorFeed


def test_saleor_feed_items(product_in_stock):
    valid_variant = product_in_stock.variants.first()
    feed = SaleorFeed()
    items = feed.items()
    assert len(items) == 1
    attributes = feed.item_attributes(items[0])
    assert attributes.get('mpn') == valid_variant.sku
    assert attributes.get('availability') == 'in stock'


def test_category_formatter(db):
    feed = SaleorFeed()
    main_category = Category(name='Main', slug='main')
    main_category.save()
    sub_category = Category(name='Sub', slug='sub', parent=main_category)
    sub_category.save()
    assert feed.get_full_category_name_path(main_category) == 'Main'
    assert feed.get_full_category_name_path(sub_category) == 'Main > Sub'

