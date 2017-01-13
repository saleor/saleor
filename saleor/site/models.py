from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class SiteSetting(models.Model):
    name = models.CharField(
        pgettext_lazy('Settings field', 'name'), max_length=128)
    value = models.CharField(
        pgettext_lazy('Settings field', 'value'), max_length=256)

    def __str__(self):
        return '%s: %s' % (self.name, self.value)
