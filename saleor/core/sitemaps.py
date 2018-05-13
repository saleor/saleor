from django.conf import settings
from django.contrib.sitemaps import Sitemap

from ..page.models import Page
from ..product.models import Category, Collection, Product


class I18nSitemap(Sitemap):
    protocol = 'https' if settings.ENABLE_SSL else 'http'
    i18n = True


class ProductSitemap(I18nSitemap):

    def items(self):
        return Product.objects.only('id', 'name').order_by('-id')


class CategorySitemap(I18nSitemap):

    def items(self):
        categories = Category.objects.all().order_by('id')
        return categories.only('id', 'name', 'slug')


class CollectionSitemap(I18nSitemap):

    def items(self):
        collections = Collection.objects.public().order_by('id')
        return collections.only('id', 'name', 'slug')


class PageSitemap(I18nSitemap):

    def items(self):
        posts = Page.objects.public()
        return posts.only('id', 'title', 'slug')


sitemaps = {
    'categories': CategorySitemap,
    'collections': CollectionSitemap,
    'products': ProductSitemap,
    'pages': PageSitemap}
