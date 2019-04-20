from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import pgettext_lazy

from ..core.utils.translations import TranslationProxy
from ..core.weight import WeightUnits
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
    homepage_collection = models.ForeignKey(
        'product.Collection', on_delete=models.SET_NULL, related_name='+',
        blank=True, null=True)
    default_weight_unit = models.CharField(
        max_length=10, choices=WeightUnits.CHOICES,
        default=WeightUnits.KILOGRAM)
    automatic_fulfillment_digital_products = models.BooleanField(default=False)
    default_digital_max_downloads = models.IntegerField(blank=True, null=True)
    default_digital_url_valid_days = models.IntegerField(blank=True, null=True)
    translated = TranslationProxy()

    class Meta:
        permissions = (
            ('manage_settings', pgettext_lazy(
                'Permission description', 'Manage settings.')),
            ('manage_translations', pgettext_lazy(
                'Permission description', 'Manage translations.')),)

    def __str__(self):
        return self.site.name

    def available_backends(self):
        return self.authorizationkey_set.values_list('name', flat=True)


class SiteSettingsTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    site_settings = models.ForeignKey(
        SiteSettings, related_name='translations', on_delete=models.CASCADE)
    header_text = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = (('language_code', 'site_settings'),)

    def __repr__(self):
        class_ = type(self)
        return '%s(pk=%r, site_settings_pk=%r)' % (
            class_.__name__, self.pk, self.site_settings_id)

    def __str__(self):
        return self.site_settings.site.name


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
