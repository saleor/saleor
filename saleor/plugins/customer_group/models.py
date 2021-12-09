from django.db import models
from django.conf import settings


class CustomerGroup(models.Model):
    name = models.CharField(max_length=256, blank=True)
    customers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    date = models.DateTimeField(db_index=True, auto_now_add=True)
