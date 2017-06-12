from datetime import timedelta
from django.contrib import sitemaps
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from saleor_oye.models import Chart
from saleor_oye.utils import visible_products, get_month_condition

from ..product.models import Product


class NewReleasesSitemap(Sitemap):

    changefreq = "never"

    priority = "0.5"

    def items(self):
        return visible_products().filter(get_month_condition(months=2))


class UpcomingReleasesSitemap(Sitemap):

    changefreq = "never"

    priority = "0.5"

    def items(self):
        return visible_products().filter(get_month_condition(months=2))


class ChartsSitemap(Sitemap):

    changefreq = "daily"
    priority = 0.5

    def items(self):
        x_month_ago = timezone.now() - timedelta(month=12)
        return Chart.objects.filter(created_at__gte=x_month_ago)


class StaticViewSitemap(sitemaps.Sitemap):

    STATIC_PAGES_DICT = {
        'main': '/',
        'new': '/releases/new/',
        'upcoming': '/releases/upcoming/',
        'used': '/releases/used/',
        'charts': '/charts/',
        'genres': '/genres/'
    }

    priority = 0.7
    changefreq = 'daily'

    def items(self):
        return ['main', 'new', 'upcoming', 'used', 'charts', 'genres']

    def location(self, item):
        return self.STATIC_PAGES_DICT.get(item, '/')


sitemaps = {
    'new': NewReleasesSitemap,
    'pre': UpcomingReleasesSitemap,
    'static': StaticViewSitemap,
}
