from __future__ import unicode_literals

import gzip
import csv
from os import path

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.syndication.views import add_domain
from django.core.files.storage import default_storage

from ..discount.models import Sale
from ..product.models import ProductVariant, Category

CATEGORY_SEPARATOR = ' > '

FILE_PATH = path.join(settings.INTEGRATIONS_DIR, 'saleor-feed.csv.gz')
FILE_URL = default_storage.url(FILE_PATH)
COMPRESSION = False

ATTRIBUTES = ['id', 'title', 'product_type', 'google_product_category',
              'link', 'image_link', 'condition', 'availability',
              'price', 'tax', 'shipping', 'sale_price',
              'mpn', 'brand', 'item_group_id', 'gender', 'age_group',
              'color', 'size', 'description']


def get_feed_items():
    items = ProductVariant.objects.all()
    items = items.select_related('product')
    items = items.prefetch_related(
        'images', 'stock', 'product__attributes', 'product__categories',
        'product__images',
    )
    return items


def item_id(item):
    return item.sku


def item_mpn(item):
    return str(item.sku)


def item_guid(item):
    return item.sku


def item_link(item, current_site):
    return add_domain(current_site.domain,
                      item.get_absolute_url(),
                      not settings.DEBUG)


def item_title(item):
    return item.display_product()


def item_description(item):
    return item.product.description[:100]


def item_condition(item):
    """
    Allowed values: new, refurbished, or used
    Read more:
    https://support.google.com/merchants/answer/6324469
    """
    return 'new'


def item_brand(item):
    """
    This field is required.
    Read more:
    https://support.google.com/merchants/answer/6324351?hl=en&ref_topic=6324338
    """
    return 'Saleor'


def item_tax(item, discounts):
    """
    For some countries you need to set tax info
    Read more:
    https://support.google.com/merchants/answer/6324454
    """
    price = item.get_price_per_item(discounts=discounts)
    return 'US::%s:y' % price.tax


def item_group_id(item):
    return str(item.product.pk)


def item_image_link(item, current_site):
    image = item.get_first_image()
    if image:
        return add_domain(current_site.domain, image.url, False)
    else:
        return None


def item_availability(item):
    if item.get_stock_quantity():
        return 'in stock'
    else:
        return 'out of stock'


def item_shipping(item):
    """
    You can set one shipping cost in feed settings or precise shipping cost
    for every item.
    Read more:
    https://support.google.com/merchants/answer/7050921
    """
    return ''


def item_google_product_category(item, category_paths):
    """
    To have your categories accepted, please use names accepted by Google or
    write custom function which maps your category names into to Google codes.
    Read more:
    https://support.google.com/merchants/answer/6324436
    """
    category = item.product.get_first_category()
    if category:
        if category.pk in category_paths:
            return category_paths[category.pk]
        ancestors = [ancestor.name for ancestor
                     in list(category.get_ancestors())]
        category_path = CATEGORY_SEPARATOR.join(ancestors + [category.name])
        category_paths[category.pk] = category_path
        return category_path
    else:
        return ''


def item_price(item):
    price = item.get_price_per_item(discounts=None)
    return '%s %s' % (price.gross, price.currency)


def item_sale_price(item, discounts):
    sale_price = item.get_price_per_item(discounts=discounts)
    return '%s %s' % (sale_price.gross, sale_price.currency)


def item_attributes(item, categories, category_paths, current_site,
                    discounts):
    product_data = {
        'id': item_id(item),
        'title': item_title(item),
        'description': item_description(item),
        'condition': item_condition(item),
        'mpn': item_mpn(item),
        'item_group_id': item_group_id(item),
        'availability': item_availability(item),
        'google_product_category': item_google_product_category(
            item, category_paths),
        'link': item_link(item, current_site),
        'shipping': item_shipping(item),
        'brand': item_brand(item)
    }

    image_link = item_image_link(item, current_site)
    if image_link:
        product_data['image_link'] = image_link

    price = item_price(item)
    product_data['price'] = price
    sale_price = item_sale_price(item, discounts)
    if sale_price != price:
        product_data['sale_price'] = sale_price

    tax = item_tax(item, discounts)
    if tax:
        product_data['tax'] = tax

    shipping = item_shipping(item)
    if shipping:
        product_data['shipping'] = shipping

    brand = item_brand(item)
    if brand:
        product_data['brand'] = brand

    return product_data


def update_feed():
    with default_storage.open(FILE_PATH, 'wb') as output_file:
        if COMPRESSION:
            try:
                output = gzip.open(output_file, 'wt')
            except TypeError:
                output = gzip.GzipFile(fileobj=output_file, mode='w')
        else:
            output = output_file

        writer = csv.DictWriter(output, ATTRIBUTES,
                                dialect=csv.excel_tab)
        writer.writeheader()

        categories = Category.objects.all()
        discounts = Sale.objects.all().prefetch_related('products',
                                                        'categories')
        category_paths = {}
        current_site = Site.objects.get_current()

        for item in get_feed_items():
            writer.writerow(
                item_attributes(item, categories, category_paths,
                                current_site, discounts))

        if COMPRESSION:
            output.close()
