from django.conf import settings
from django.db import models


class CustomerGroup(models.Model):
    name = models.CharField(max_length=256, db_index=True)
    customers = models.ManyToManyField(settings.AUTH_USER_MODEL)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    variants = models.ManyToManyField("product.ProductVariant")
