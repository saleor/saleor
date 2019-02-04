import csv
import gzip
from datetime import date

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.syndication.views import add_domain
from django.core.files.storage import default_storage
from django.utils.encoding import smart_text

from ..discount.models import Sale
from ..product.models import (
    Attribute, AttributeValue, Category, ProductVariant)

CATEGORY_SEPARATOR = ' > '

FILE_PATH = 'google-feed.csv.gz'

ATTRIBUTES = ['id', 'title', 'product_type', 'google_product_category',
              'link', 'image_link', 'condition', 'availability',
              'price', 'tax', 'sale_price', 'mpn', 'brand', 'item_group_id',
              'gender', 'age_group', 'color', 'size', 'description']


def get_feed_file_url():
    return default_storage.url(FILE_PATH)


def get_feed_items():
    items = ProductVariant.objects.all()
    items = items.select_related('product')
    items = items.prefetch_related(
        'images', 'product__category',
        'product__images', 'product__product_type__product_attributes',
        'product__product_type__variant_attributes')
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
    """Return a valid item condition.

    Allowed values: new, refurbished, and used.
    Read more:
    https://support.google.com/merchants/answer/6324469
    """
    return 'new'


def item_brand(item, attributes_dict, attribute_values_dict):
    """Return an item brand.

    This field is required.
    Read more:
    https://support.google.com/merchants/answer/6324351?hl=en&ref_topic=6324338
    """
    brand = None
    brand_attribute_pk = attributes_dict.get('brand')
    publisher_attribute_pk = attributes_dict.get('publisher')

    if brand_attribute_pk:
        brand = item.attributes.get(str(brand_attribute_pk))
        if brand is None:
            brand = item.product.attributes.get(str(brand_attribute_pk))

    if brand is None and publisher_attribute_pk is not None:
        brand = item.attributes.get(str(publisher_attribute_pk))
        if brand is None:
            brand = item.product.attributes.get(str(publisher_attribute_pk))

    if brand is not None:
        brand_name = attribute_values_dict.get(brand)
        if brand_name is not None:
            return brand_name
    return brand


def item_tax(item, discounts):
    """Return item tax.

    For some countries you need to set tax info
    Read more:
    https://support.google.com/merchants/answer/6324454
    """
    price = item.get_price(discounts=discounts)
    return 'US::%s:y' % price.tax


def item_group_id(item):
    return str(item.product.pk)


def item_image_link(item, current_site):
    product_image = item.get_first_image()
    if product_image:
        image = product_image.image
        return add_domain(current_site.domain, image.url, False)
    return None


def item_availability(item):
    if item.quantity_available:
        return 'in stock'
    return 'out of stock'


def item_google_product_category(item, category_paths):
    """Return a canonical product category.

    To have your categories accepted, please use names accepted by Google or
    write custom function which maps your category names into to Google codes.
    Read more:
    https://support.google.com/merchants/answer/6324436
    """
    category = item.product.category
    if category.pk in category_paths:
        return category_paths[category.pk]
    ancestors = [
        ancestor.name for ancestor in list(category.get_ancestors())]
    category_path = CATEGORY_SEPARATOR.join(ancestors + [category.name])
    category_paths[category.pk] = category_path
    return category_path


def item_price(item):
    price = item.get_price(discounts=None)
    return '%s %s' % (price.gross.amount, price.currency)


def item_sale_price(item, discounts):
    sale_price = item.get_price(discounts=discounts)
    return '%s %s' % (sale_price.gross.amount, sale_price.currency)


def item_attributes(item, categories, category_paths, current_site,
                    discounts, attributes_dict, attribute_values_dict):
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
        'link': item_link(item, current_site)}

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

    brand = item_brand(item, attributes_dict, attribute_values_dict)
    if brand:
        product_data['brand'] = brand

    return product_data


def write_feed(file_obj):
    """Write feed contents info provided file object."""
    writer = csv.DictWriter(file_obj, ATTRIBUTES, dialect=csv.excel_tab)
    writer.writeheader()
    categories = Category.objects.all()
    discounts = Sale.objects.active(date.today()).prefetch_related(
        'products', 'categories')
    attributes_dict = {a.slug: a.pk for a in Attribute.objects.all()}
    attribute_values_dict = {smart_text(a.pk): smart_text(a) for a
                             in AttributeValue.objects.all()}
    category_paths = {}
    current_site = Site.objects.get_current()
    for item in get_feed_items():
        item_data = item_attributes(item, categories, category_paths,
                                    current_site, discounts, attributes_dict,
                                    attribute_values_dict)
        writer.writerow(item_data)


def update_feed(file_path=FILE_PATH):
    """Save updated feed into path provided as argument.

    Default path is defined in module as FILE_PATH.
    """
    with default_storage.open(file_path, 'wb') as output_file:
        output = gzip.open(output_file, 'wt')
        write_feed(output)
        output.close()
