from __future__ import unicode_literals

import pytest
import re
from lxml import etree
from lxml.etree import XMLSyntaxError

from saleor.integrations.feeds import SaleorFeed
from saleor.integrations.utils import get_feed_content
from saleor.product.models import ProductVariant


def entry_node_to_dict(node):
    text_nodes = {re.sub('\{.*\}', '', n.tag): n.text for n in node}
    for attribute in node.attrib:
        text_nodes[attribute] = node.attrib[attribute]
    return text_nodes


def test_saleor_feed_is_valid_xml(product_in_stock):
    content = get_feed_content(SaleorFeed())
    try:
        etree.fromstring(content.encode('utf-8'))
    except XMLSyntaxError:
        pytest.fail("Generated feed is not a valid XML.")


def test_saleor_feed(product_in_stock):
    valid_variant = ProductVariant.objects.first()
    content = get_feed_content(SaleorFeed())
    parsed_feed = etree.fromstring(content.encode('utf-8'))
    entries = [entry_node_to_dict(node)
               for node in parsed_feed if node.tag.endswith('entry')]
    assert len(entries) == 1
    feed_variant = entries[0]
    assert feed_variant.get('mpn') == valid_variant.sku
    assert feed_variant.get('availability') == 'in stock'
    price = valid_variant.get_price_per_item(discounts=None)
    assert feed_variant.get('price') == '%s %s' % (price.gross,
                                                   price.currency)
