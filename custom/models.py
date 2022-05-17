from django.db import models
from saleor.core.models import ModelWithMetadata


# Create your models here.
class Custom(ModelWithMetadata):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250)
    attribute = models.CharField(max_length=250)
    description = models.CharField(max_length=250)

    class Meta(ModelWithMetadata.Meta):
        ordering = ("name", )
