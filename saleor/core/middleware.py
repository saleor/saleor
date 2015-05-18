import logging
from subprocess import Popen, PIPE

from django.conf import settings
from django.utils.translation import get_language

from . import analytics
from ..product.models import FixedProductDiscount

logger = logging.getLogger(__name__)


class CheckHTML(object):

    def process_response(self, request, response):
        if (settings.DEBUG and
                settings.WARN_ABOUT_INVALID_HTML5_OUTPUT and
                200 <= response.status_code < 300):
            proc = Popen(["tidy"], stdout=PIPE, stderr=PIPE, stdin=PIPE)
            _out, err = proc.communicate(response.content)
            for l in err.split('\n\n')[0].split('\n')[:-2]:
                logger.warning(l)
        return response


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
