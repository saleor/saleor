from django.contrib.postgres.indexes import BTreeIndex
from django.db import models

from ...core.models import SortableModel
from ...product.models import Product, ProductType
from .base import AssociatedAttributeManager


class AssignedProductAttributeValue(SortableModel):
    value = models.ForeignKey(
        "AttributeValue",
        on_delete=models.CASCADE,
        related_name="productvalueassignment",
    )
    product = models.ForeignKey(
        Product,
        related_name="attributevalues",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_index=False,
    )

    class Meta:
        unique_together = (("value", "product"),)
        ordering = ("sort_order", "pk")
        indexes = [
            BTreeIndex(fields=["product"], name="assignedprodattrval_product_idx")
        ]

    def get_ordering_queryset(self):
        return self.product.attributevalues.all()


class AttributeProduct(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributeproduct", on_delete=models.CASCADE
    )
    product_type = models.ForeignKey(
        ProductType, related_name="attributeproduct", on_delete=models.CASCADE
    )

    objects = AssociatedAttributeManager()

    class Meta:
        unique_together = (("attribute", "product_type"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.product_type.attributeproduct.all()
