import threading
from django.contrib.sites import models as sites
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
    print('in new get current')
    from django.conf import settings
    if getattr(settings, 'SITE_ID', ''):
        site_id = settings.SITE_ID
        print 'SITE_ID in settings'
        site = self.prefetch_related('settings').filter(pk=site_id)
        print site
        return site[0]
    elif request:
        # print 'SITE_ID not in settings'
        host = request.get_host()
        try:
            return self.get(domain__iexact=host)
        except sites.Site.DoesNotExist:
            domain, port = split_domain_port(host)
            return self.get(domain__iexact=domain)

    raise ImproperlyConfigured(
        "You're using the Django \"sites framework\" without having "
        "set the SITE_ID setting. Create a site in your database and "
        "set the SITE_ID setting or pass a request to "
        "Site.objects.get_current() to fix this error."
    )


sites.SITE_CACHE = THREADED_SITE_CACHE
sites.SiteManager.get_current = new_get_current


@python_2_unicode_compatible
class SiteSettings(models.Model):
    site = models.OneToOneField(sites.Site, related_name='settings')
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
