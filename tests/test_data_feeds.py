from __future__ import unicode_literals

import csv

from mock import Mock

from django.contrib.sites.models import Site
from django.utils import six
from django.utils.encoding import smart_text
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from saleor.product.models import AttributeChoiceValue, Category
from saleor.data_feeds.google_merchant import (get_feed_items,
                                               item_attributes,
                                               item_google_product_category,
                                               write_feed)


def test_saleor_feed_items(product_in_stock):
    valid_variant = product_in_stock.variants.first()
    items = get_feed_items()
    assert len(items) == 1
    categories = Category.objects.all()
    discounts = []
    category_paths = {}
    attributes_dict = {}
    current_site = Site.objects.get_current()
    attribute_values_dict = {smart_text(a.pk): smart_text(a) for a
                             in AttributeChoiceValue.objects.all()}
    attributes = item_attributes(items[0], categories, category_paths,
                                 current_site, discounts, attributes_dict,
                                 attribute_values_dict)
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


def test_write_feed(product_in_stock, monkeypatch):
    buffer = StringIO()
    write_feed(buffer)
    buffer.seek(0)
    dialect = csv.Sniffer().sniff(buffer.getvalue())
    assert dialect.delimiter == csv.excel_tab.delimiter
    assert dialect.quotechar == csv.excel_tab.quotechar
    assert dialect.escapechar == csv.excel_tab.escapechar
    assert csv.Sniffer().has_header(buffer.getvalue())
    lines = [line for line in csv.reader(buffer, dialect=csv.excel_tab)]
    assert len(lines) == 2
    header = lines[0]
    google_required_fields = ['id', 'title', 'link', 'image_link',
                              'availability', 'price', 'condition']
    for field in google_required_fields:
        assert field in header
