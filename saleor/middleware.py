import logging
from subprocess import Popen, PIPE

from django.conf import settings

logger = logging.getLogger('saleor')


class CheckHTML(object):
    def process_response(self, request, response):
        if settings.DEBUG and settings.WARN_ABOUT_INVALID_HTML5_OUTPUT:
            proc = Popen(["tidy"], stdout=PIPE, stderr=PIPE, stdin=PIPE)
            out, err = proc.communicate(response.content)
            for l in err.split('\n\n')[0].split('\n')[:-2]:
                logger.warning(l)
        return response
