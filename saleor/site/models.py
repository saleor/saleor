from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import pgettext_lazy

from . import AuthenticationBackends
from .patch_sites import patch_contrib_sites

patch_contrib_sites()


class SiteSettings(models.Model):
    site = models.OneToOneField(
        Site, related_name='settings', on_delete=models.CASCADE)
    header_text = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    top_menu = models.ForeignKey(
        'menu.Menu', on_delete=models.SET_NULL, related_name='+', blank=True,
        null=True)
    bottom_menu = models.ForeignKey(
        'menu.Menu', on_delete=models.SET_NULL, related_name='+', blank=True,
        null=True)
    include_taxes_in_prices = models.BooleanField(default=True)
    display_gross_prices = models.BooleanField(default=True)
    charge_taxes_on_shipping = models.BooleanField(default=True)
    track_inventory_by_default = models.BooleanField(default=True)

    class Meta:
        permissions = ((
            'manage_settings', pgettext_lazy(
                'Permission description', 'Manage settings.')),)

    def __str__(self):
        return self.site.name

    def available_backends(self):
        return self.authorizationkey_set.values_list('name', flat=True)


class AuthorizationKey(models.Model):
    site_settings = models.ForeignKey(SiteSettings, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=20, choices=AuthenticationBackends.BACKENDS)
    key = models.TextField()
    password = models.TextField()

    class Meta:
        unique_together = (('site_settings', 'name'),)

    def __str__(self):
        return self.name

    def key_and_secret(self):
        return self.key, self.password
