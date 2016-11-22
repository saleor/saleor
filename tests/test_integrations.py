from __future__ import unicode_literals

from saleor.integrations.feeds import SaleorFeed


def test_saleor_feed_items(product_in_stock):
    valid_variant = product_in_stock.variants.first()
    feed = SaleorFeed()
    items = feed.items()
    assert len(items) == 1
    attributes = feed.item_attributes(items[0])
    assert attributes.get('mpn') == valid_variant.sku
    assert attributes.get('availability') == 'in stock'
