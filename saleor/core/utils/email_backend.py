from premailer import transform
from templated_email.backends.vanilla_django import TemplateBackend

from django.conf import settings
from django.contrib.sites.models import Site


class CustomTemplateBackend(TemplateBackend):
    def _render_email(self, *args, **kwargs):
        result = super()._render_email(*args, **kwargs)
        html = result.get('html')
        if html:
            site = Site.objects.get_current()
            protocol = 'https' if settings.ENABLE_SSL else 'http'
            base_url = '{}://{}'.format(protocol, site.domain)
            transformed_html = transform(html, base_url=base_url)
            result.update({'html': transformed_html})
        return result
