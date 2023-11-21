from django.conf import settings
from django.db import models


class SiteSettings(models.Model):
    class Meta:
        app_label = 'pharmacy'
        ordering = ['name']

    name = models.CharField(max_length=25)
    slug = models.SlugField(max_length=255, unique=True)
    pharmacy_name = models.CharField(max_length=255)
    npi = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=25)
    fax_number = models.CharField(max_length=25)
    image = models.FileField(upload_to='site/images', max_length=255)
    css = models.FileField(upload_to='site/css')
    cookies_src = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    fill_fee_regular = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    fill_fee_cold_chain = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    margin_regular = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    margin_cold_chain = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
