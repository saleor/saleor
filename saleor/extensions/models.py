from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import pgettext_lazy

from saleor.core.utils.json_serializer import CustomJsonEncoder


class PluginConfiguration(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    configuration = JSONField(default=dict, encoder=CustomJsonEncoder)

    class Meta:
        permissions = (
            ("manage_plugins", pgettext_lazy("Plugin description", "Manage plugins")),
        )

    def __str__(self):
        return f"Configuration of {self.name}, active: {self.active}"
