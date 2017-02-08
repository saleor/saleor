from django.contrib.sites.models import _simple_domain_name_validator
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class SiteSettings(models.Model):
    domain = models.CharField(
        pgettext_lazy('Site field', 'domain'), max_length=100,
        validators=[_simple_domain_name_validator], unique=True)

    name = models.CharField(pgettext_lazy('Site field', 'name'), max_length=50)
    header_text = models.CharField(
        pgettext_lazy('Site field', 'header text'), max_length=200, blank=True)
    description = models.CharField(
        pgettext_lazy('Site field', 'site description'), max_length=500,
        blank=True)

    def __str__(self):
        return self.name
