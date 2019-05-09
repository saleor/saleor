from __future__ import absolute_import, unicode_literals

from django.template.response import SimpleTemplateResponse
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import Panel


class RedirectsPanel(Panel):
    """
    Panel that intercepts redirects and displays a page with debug info.
    """

    has_content = False

    nav_title = _("Intercept redirects")

    def process_response(self, request, response):
        if 300 <= int(response.status_code) < 400:
            redirect_to = response.get("Location", None)
            if redirect_to:
                status_line = "%s %s" % (response.status_code, response.reason_phrase)
                cookies = response.cookies
                context = {"redirect_to": redirect_to, "status_line": status_line}
                # Using SimpleTemplateResponse avoids running global context processors.
                response = SimpleTemplateResponse(
                    "debug_toolbar/redirect.html", context
                )
                response.cookies = cookies
                response.render()
        return response
