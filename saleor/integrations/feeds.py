from __future__ import unicode_literals

from os import path

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.syndication.views import add_domain
from prices import Price

from ..product.models import ProductVariant, Category

CATEGORY_SEPARATOR = ' > '


class GoogleProductFeed(object):
    """
    Basic Google feed class. To adjust feed to your needs inherit from
    this class.

    Depending on target country and law changes required fields can change,
    please validate your feed at Google Merchant dashboard and override
    missing methods.

    Google feeds dashboard:
    https://merchants.google.com/mc/feeds/dashboard

    For more info check Google support pages:
    https://support.google.com/merchants/answer/7052112?visit_id=1-636148270257062854-1147518273&rd=1
    """
    file_path = path.join(settings.INTEGRATIONS_DIR, 'google-feed.csv.gz')
    file_url = settings.STATIC_URL + file_path
    compression = True
    attributes = ['id', 'title', 'product_type', 'google_product_category',
                  'link', 'image_link', 'condition', 'availability',
                  'price', 'tax', 'shipping', 'sale_price',
                  'mpn', 'brand', 'item_group_id', 'gender', 'age_group',
                  'color', 'size', 'description']

    def __init__(self):
        self.categories = Category.objects.none()
        self.discounts = None
        self.category_paths = {}
        self.current_site = Site.objects.get_current()

    def get_full_category_name_path(self, category):
        if category.pk in self.category_paths:
            return self.category_paths[category.pk]
        ancestors = []
        for c in self.categories:
            if c.is_ancestor_of(category):
                ancestors.append(c)
        ancestors.append(category)
        ancestors = sorted(ancestors, key=lambda c: c.pk)
        ret = CATEGORY_SEPARATOR.join(
            [category.name for category in ancestors])
        self.category_paths[category.pk] = ret
        return ret

    def items(self):
        self.discounts = None
        self.categories = Category.objects.all()
        return ProductVariant.objects.all().select_related(
            'product'
        ).prefetch_related(
            'images', 'stock',
            'product__attributes', 'product__categories', 'product__images',
        )

    def item_id(self, item):
        return item.sku

    def item_mpn(self, item):
        return str(item.sku)

    def item_guid(self, item):
        return item.sku

    def item_link(self, item):
        return add_domain(self.current_site.domain,
                          item.get_absolute_url(),
                          settings.INTEGRATIONS_ENABLE_SSL)

    def item_title(self, item):
        return item.display_product()

    def item_description(self, item):
        return item.product.description[:100]

    def item_condition(self, item):
        """
        Allowed values: new, refurbished, or used
        Read more:
        https://support.google.com/merchants/answer/6324469
        """
        return 'new'

    def item_brand(self, item):
        """
        This field is required.
        Read more:
        https://support.google.com/merchants/answer/6324351?hl=en&ref_topic=6324338
        """
        return None

    def item_tax(self, item):
        """
        For some countries you need to set tax info
        Read more:
        https://support.google.com/merchants/answer/6324454
        """
        return None

    def item_group_id(self, item):
        return str(item.product.pk)

    def item_image_link(self, item):
        image = item.get_first_image()
        if image:
            return add_domain(self.current_site.domain, image.url, False)
        else:
            return None

    def item_availability(self, item):
        if item.get_stock_quantity():
            return 'in stock'
        else:
            return 'out of stock'

    def item_shipping(self, item):
        """
        You can set one shipping cost in feed settings or precise shipping cost for every item.
        Read more:
        https://support.google.com/merchants/answer/7050921
        """
        return None

    def item_google_product_category(self, item):
        """
        To have your categories accepted, please use names accepted by Google or
        write custom function which maps your category names into to Google codes.
        Read more:
        https://support.google.com/merchants/answer/6324436
        """
        category = item.product.get_first_category()
        if category:
            category_path = self.get_full_category_name_path(category)
            return category_path
        else:
            return ''

    def item_price(self, item):
        price = item.get_price_per_item(discounts=None)
        return '%s %s' % (price.gross, price.currency)

    def item_sale_price(self, item):
        sale_price = item.get_price_per_item(discounts=self.discounts)
        return '%s %s' % (sale_price.gross, sale_price.currency)

    def item_attributes(self, item):
        product_data = {
            'id': self.item_id(item),
            'title': self.item_title(item),
            'description': self.item_description(item),
            'condition': self.item_condition(item),
            'mpn': self.item_mpn(item),
            'item_group_id': self.item_group_id(item),
            'availability': self.item_availability(item),
            'google_product_category': self.item_google_product_category(item),
            'link': self.item_link(item),
            'tax': self.item_tax(item),
            'shipping': self.item_shipping(item)
        }

        image_link = self.item_image_link(item)
        if image_link:
            product_data['image_link'] = image_link

        price = self.item_price(item)
        product_data['price'] = price
        sale_price = self.item_sale_price(item)
        if sale_price != price:
            product_data['sale_price'] = sale_price

        tax = self.item_tax(item)
        if tax:
            product_data['tax'] = tax

        shipping = self.item_shipping(item)
        if shipping:
            product_data['shipping'] = shipping

        brand = self.item_brand(item)
        if brand:
            product_data['brand'] = brand

        return product_data


class SaleorFeed(GoogleProductFeed):
    """
    Example of using GoogleProductFeed.
    """
    file_path = path.join(settings.INTEGRATIONS_DIR, 'saleor-feed.csv.gz')
    file_url = settings.MEDIA_URL + file_path

    def item_shipping(self, item):
        """Flat shipping price"""
        price = Price(5, currency=settings.DEFAULT_CURRENCY)
        return 'US:::%s %s' % (price.gross, price.currency)

    def item_tax(self, item):
        """No taxes on products"""
        return 'US::0:y'

    def item_brand(self, item):
        return 'Saleor'
