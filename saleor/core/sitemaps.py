from django.contrib.sitemaps import Sitemap

from ..page.models import Page
from ..product.models import Category, Product


class ProductSitemap(Sitemap):

    def items(self):
        return Product.objects.only('id', 'name').order_by('-id')


class CategorySitemap(Sitemap):

    def items(self):
        categories = Category.objects.all().order_by('id')
        return categories.only('id', 'name', 'slug')


class PageSitemap(Sitemap):

    def items(self):
        posts = Page.objects.public()
        return posts.only('id', 'title', 'url')


sitemaps = {
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'pages': PageSitemap}
