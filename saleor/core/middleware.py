import logging
import random
import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import MiddlewareNotUsed
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.translation import get_language, ugettext_lazy as _
from django_countries.fields import Country

from ..discount.utils import fetch_discounts
from ..extensions.manager import get_extensions_manager
from ..graphql.views import GraphQLView
from . import analytics
from .exceptions import ReadOnlyException
from .utils import get_client_ip, get_country_by_ip, get_currency_for_country

logger = logging.getLogger(__name__)


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

    def middleware(request):
        request.discounts = SimpleLazyObject(lambda: fetch_discounts(timezone.now()))
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


def extensions(get_response):
    """Assign extensions manager."""

    def _get_manager():
        return get_extensions_manager(plugins=settings.PLUGINS)

    def middleware(request):
        request.extensions = SimpleLazyObject(lambda: _get_manager())
        return get_response(request)

    return middleware


class ReadOnlyMiddleware:
    ALLOWED_MUTATIONS = [
        "checkoutAddPromoCode",
        "checkoutBillingAddressUpdate",
        "checkoutComplete",
        "checkoutCreate",
        "checkoutCustomerAttach",
        "checkoutCustomerDetach",
        "checkoutEmailUpdate",
        "checkoutLineDelete",
        "checkoutLinesAdd",
        "checkoutLinesUpdate",
        "checkoutRemovePromoCode",
        "checkoutPaymentCreate",
        "checkoutShippingAddressUpdate",
        "checkoutShippingMethodUpdate",
        "checkoutUpdateVoucher",
        "checkoutUpdateMetadata",
        "checkoutClearMetadata",
        "checkoutUpdatePrivateMetadata",
        "checkoutClearPrivateMetadata",
        "tokenCreate",
        "tokenVerify",
    ]
    BLOCKED_URL_PATTERNS = [
        re.compile(r"^/dashboard"),
        re.compile(r"^/([\w-]+/)?account/$"),
        re.compile(r"^/([\w-]+/)?account/signup/$"),
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, *_args, **_kwargs):
        if request.path == reverse("api"):
            if not self._is_graphql_request_blocked(request):
                return None
            error = GraphQLView.format_error(
                ReadOnlyException(
                    _("Be aware admin pirate! API runs in read-only mode!")
                )
            )
            data = {"errors": [error], "data": None}
            response = JsonResponse(data=data, safe=False)
            response["Access-Control-Allow-Origin"] = settings.ALLOWED_GRAPHQL_ORIGINS
            response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response[
                "Access-Control-Allow-Headers"
            ] = "Origin, Content-Type, Accept, Authorization"
            return response

        if self._is_django_request_blocked(request):
            image = random.randrange(1, 6)
            domain = Site.objects.get_current().domain
            url = f"http://{domain}"
            ctx = {
                "image_path": "read_only/images/pirate-%s.svg" % image,
                "image_class": "img%s" % image,
                "back_url": request.headers.get("referer", url),
            }

            return TemplateResponse(request, "read_only/read_only_splash.html", ctx)

    def _is_url_blocked(self, url):
        for pattern in self.BLOCKED_URL_PATTERNS:
            yield pattern.match(url)

    def _is_django_request_blocked(self, request):
        is_post = request.method == "POST"
        request_url = request.path_info
        return is_post and any(self._is_url_blocked(request_url))

    def _is_graphql_request_blocked(self, request):

        body = GraphQLView.parse_body(request)
        if not isinstance(body, list):
            body = [body]
        for data in body:
            query, _, _ = GraphQLView.get_graphql_params(request, data)
            document, _ = GraphQLView().parse_query(query)
            if not document:
                return False

            definitions = document.document_ast.definitions

            for definition in definitions:
                operation = getattr(definition, "operation", None)
                if not operation or operation != "mutation":
                    continue

                for selection in definition.selection_set.selections:
                    selection_name = str(selection.name.value)
                    blocked = selection_name not in self.ALLOWED_MUTATIONS
                    if blocked:
                        return True
        return False
