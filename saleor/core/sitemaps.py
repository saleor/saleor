from django.contrib.sitemaps import Sitemap

from ..product.models import Product
from ..site.utils import get_domain


class ProductSitemap(Sitemap):
    def _urls(self, page, protocol, domain):
        domain = get_domain()
        return super(ProductSitemap, self)._urls(page, protocol, domain)

    def items(self):
        return Product.objects.only('id', 'name').order_by('-id')


sitemaps = {'products': ProductSitemap}
