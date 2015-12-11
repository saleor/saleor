import logging

from django.utils.translation import get_language

from . import analytics
from ..product.models import FixedProductDiscount

logger = logging.getLogger(__name__)


class GoogleAnalytics(object):
    def process_request(self, request):
        client_id = analytics.get_client_id(request)
        path = request.path
        language = get_language()
        headers = request.META
        # FIXME: on production you might want to run this in background
        try:
            analytics.report_view(client_id, path=path, language=language,
                                  headers=headers)
        except Exception:
            logger.exception('Unable to update analytics')


class DiscountMiddleware(object):
    def process_request(self, request):
        discounts = FixedProductDiscount.objects.all()
        discounts = discounts.prefetch_related('products')
        request.discounts = discounts
