import datetime
import logging
from collections import defaultdict
from functools import wraps
from typing import Callable

import django.contrib.auth.middleware
import django.contrib.messages.middleware
import django.contrib.sessions.middleware
import django.middleware.common
import django.middleware.csrf
import django.middleware.locale
import django.middleware.security
import django_babel.middleware
import impersonate.middleware
import social_django.middleware
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import MiddlewareNotUsed
from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from django.utils.translation import get_language
from django_countries.fields import Country

from ..discount import DiscountInfo
from ..discount.models import Sale
from ..product.models import Category
from . import analytics
from .utils import get_client_ip, get_country_by_ip, get_currency_for_country
from .utils.taxes import get_taxes_for_country

logger = logging.getLogger(__name__)


def django_only_request_handler(get_response: Callable, handler: Callable):
    api_path = reverse("api")

    @wraps(handler)
    def handle_request(request):
        if request.path == api_path:
            return get_response(request)
        return handler(request)

    return handle_request


def django_only_middleware(middleware):
    @wraps(middleware)
    def wrapped(get_response):
        handler = middleware(get_response)
        return django_only_request_handler(get_response, handler)

    return wrapped


social_auth_exception_middleware = django_only_middleware(
    social_django.middleware.SocialAuthExceptionMiddleware
)
impersonate_middleware = django_only_middleware(
    impersonate.middleware.ImpersonateMiddleware
)
babel_locale_middleware = django_only_middleware(
    django_babel.middleware.LocaleMiddleware
)
django_locale_middleware = django_only_middleware(
    django.middleware.locale.LocaleMiddleware
)
django_messages_middleware = django_only_middleware(
    django.contrib.messages.middleware.MessageMiddleware
)
django_auth_middleware = django_only_middleware(
    django.contrib.auth.middleware.AuthenticationMiddleware
)
django_csrf_view_middleware = django_only_middleware(
    django.middleware.csrf.CsrfViewMiddleware
)
django_security_middleware = django_only_middleware(
    django.middleware.security.SecurityMiddleware
)
django_session_middleware = django_only_middleware(
    django.contrib.sessions.middleware.SessionMiddleware
)


@django_only_middleware
def google_analytics(get_response):
    """Report a page view to Google Analytics."""

    if not settings.GOOGLE_ANALYTICS_TRACKING_ID:
        raise MiddlewareNotUsed()

    def middleware(request):
        client_id = analytics.get_client_id(request)
        path = request.path
        language = get_language()
        headers = request.META
        try:
            analytics.report_view(
                client_id, path=path, language=language, headers=headers
            )
        except Exception:
            logger.exception("Unable to update analytics")
        return get_response(request)

    return middleware


def discounts(get_response):
    """Assign active discounts to `request.discounts`."""

    def fetch_categories(sale_pks):
        categories = Sale.categories.through.objects.filter(
            sale_id__in=sale_pks
        ).values_list("sale_id", "category_id")
        category_map = defaultdict(set)
        for sale_pk, category_pk in categories:
            category_map[sale_pk].add(category_pk)
        subcategory_map = defaultdict(set)
        for sale_pk, category_pks in category_map.items():
            subcategory_map[sale_pk] = set(
                Category.tree.filter(pk__in=category_pks)
                .get_descendants(include_self=True)
                .values_list("pk", flat=True)
            )
        return subcategory_map

    def fetch_collections(sale_pks):
        collections = Sale.collections.through.objects.filter(
            sale_id__in=sale_pks
        ).values_list("sale_id", "collection_id")
        collection_map = defaultdict(set)
        for sale_pk, collection_pk in collections:
            collection_map[sale_pk].add(collection_pk)
        return collection_map

    def fetch_products(sale_pks):
        products = Sale.products.through.objects.filter(
            sale_id__in=sale_pks
        ).values_list("sale_id", "product_id")
        product_map = defaultdict(set)
        for sale_pk, product_pk in products:
            product_map[sale_pk].add(product_pk)
        return product_map

    def get_discounts():
        sales = list(Sale.objects.active(datetime.date.today()))
        pks = {s.pk for s in sales}
        collections = fetch_collections(pks)
        products = fetch_products(pks)
        categories = fetch_categories(pks)

        return [
            DiscountInfo(
                sale=sale,
                category_ids=categories[sale.pk],
                collection_ids=collections[sale.pk],
                product_ids=products[sale.pk],
            )
            for sale in sales
        ]

    def middleware(request):
        request.discounts = SimpleLazyObject(get_discounts)
        return get_response(request)

    return middleware


def country(get_response):
    """Detect the user's country and assign it to `request.country`."""

    def middleware(request):
        client_ip = get_client_ip(request)
        if client_ip:
            request.country = get_country_by_ip(client_ip)
        if not request.country:
            request.country = Country(settings.DEFAULT_COUNTRY)
        return get_response(request)

    return middleware


def currency(get_response):
    """Take a country and assign a matching currency to `request.currency`."""

    def middleware(request):
        if hasattr(request, "country") and request.country is not None:
            request.currency = get_currency_for_country(request.country)
        else:
            request.currency = settings.DEFAULT_CURRENCY
        return get_response(request)

    return middleware


def site(get_response):
    """Clear the Sites cache and assign the current site to `request.site`.

    By default django.contrib.sites caches Site instances at the module
    level. This leads to problems when updating Site instances, as it's
    required to restart all application servers in order to invalidate
    the cache. Using this middleware solves this problem.
    """

    def _get_site():
        Site.objects.clear_cache()
        return Site.objects.get_current()

    def middleware(request):
        request.site = SimpleLazyObject(_get_site)
        return get_response(request)

    return middleware


def taxes(get_response):
    """Assign tax rates for default country to `request.taxes`."""

    def middleware(request):
        if settings.VATLAYER_ACCESS_KEY:
            request.taxes = SimpleLazyObject(
                lambda: get_taxes_for_country(request.country)
            )
        else:
            request.taxes = None
        return get_response(request)

    return middleware
