from django.db import models

# Create your models here.
from saleor.warehouse.models import Warehouse, Stock
from saleor.product.models import ProductVariant
from saleor.account.models import User

from saleor.core.models import ModelWithMetadata


class StockNotify(ModelWithMetadata):
    user = models.ForeignKey(User, related_name='user_request', on_delete=models.CASCADE)
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, \
                                         related_name="source_warehouse")
    next_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, \
                                       related_name="next_warehouse")
    quantity_request = models.IntegerField(null=True, blank=True, default=0)

    product_variant = models.ForeignKey(ProductVariant,
                                             related_name="product_variant", on_delete=models.CASCADE)
    status = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.user.name
