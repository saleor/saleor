from django.contrib.sitemaps import Sitemap

from ..product.models import Category, Product


class ProductSitemap(Sitemap):

    def items(self):
        return Product.objects.only('id', 'name').order_by('-id')


class CategorySitemap(Sitemap):

    def items(self):
        categories = Category.objects.all().order_by('id')
        return categories.only('id', 'name', 'slug')


sitemaps = {
    'categories': CategorySitemap,
    'products': ProductSitemap}
