from django.db import models

from saleor.core.models import ModelWithMetadata


class TransferRequest(ModelWithMetadata):
    warehouse_origin = models.IntegerField(default=0)
    warehouse_destinate = models.IntegerField(default=0)
    product_variant_id = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



