import threading
from django.contrib.sites.models import SiteManager, Site
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http.request import split_domain_port
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import pgettext_lazy

from . import AuthenticationBackends


lock = threading.Lock()
with lock:
    THREADED_SITE_CACHE = {}


def new_get_current(self, request=None):
    from django.conf import settings
    if getattr(settings, 'SITE_ID', ''):
        site_id = settings.SITE_ID
        if site_id not in THREADED_SITE_CACHE:
            site = self.get(pk=site_id)
            THREADED_SITE_CACHE[site_id] = site
        return THREADED_SITE_CACHE[site_id]
    elif request:
        host = request.get_host()
        try:
            # First attempt to look up the site by host with or without port.
            if host not in THREADED_SITE_CACHE:
                THREADED_SITE_CACHE[host] = self.get(domain__iexact=host)
            return THREADED_SITE_CACHE[host]
        except Site.DoesNotExist:
            # Fallback to looking up site after stripping port from the host.
            domain, port = split_domain_port(host)
            if domain not in THREADED_SITE_CACHE:
                THREADED_SITE_CACHE[domain] = self.get(domain__iexact=domain)
        return THREADED_SITE_CACHE[domain]

    raise ImproperlyConfigured(
        "You're using the Django \"sites framework\" without having "
        "set the SITE_ID setting. Create a site in your database and "
        "set the SITE_ID setting or pass a request to "
        "Site.objects.get_current() to fix this error."
    )


SiteManager.get_current = new_get_current


@python_2_unicode_compatible
class SiteSettings(models.Model):
    site = models.OneToOneField(Site, related_name='settings')
    header_text = models.CharField(
        pgettext_lazy('Site field', 'header text'), max_length=200, blank=True)
    description = models.CharField(
        pgettext_lazy('Site field', 'site description'), max_length=500,
        blank=True)

    def __str__(self):
        return self.site.name

    def available_backends(self):
        return self.authorizationkey_set.values_list('name', flat=True)


@python_2_unicode_compatible
class AuthorizationKey(models.Model):
    site_settings = models.ForeignKey(SiteSettings)
    name = models.CharField(
        pgettext_lazy('Authentiaction field', 'name'), max_length=20,
        choices=AuthenticationBackends.BACKENDS)
    key = models.TextField(pgettext_lazy('Authentication field', 'key'))
    password = models.TextField(
        pgettext_lazy('Authentication field', 'password'))

    class Meta:
        unique_together = (('site_settings', 'name'),)

    def __str__(self):
        return self.name

    def key_and_secret(self):
        return self.key, self.password
