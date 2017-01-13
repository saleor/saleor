from django.contrib.sites.models import _simple_domain_name_validator
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class SiteSetting(models.Model):
    domain = models.CharField(
        pgettext_lazy('Site field', 'domain'), max_length=100,
        validators=[_simple_domain_name_validator], unique=True)

    name = models.CharField(pgettext_lazy('Site field', 'name'), max_length=50)

    def __str__(self):
        return self.name
