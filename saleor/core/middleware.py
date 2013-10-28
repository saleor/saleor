import logging
from subprocess import Popen, PIPE

from django.conf import settings

from . import analytics

logger = logging.getLogger('saleor')


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
        # FIXME: on production you might want to run this in background
        analytics.report_view(client_id, request.path)
