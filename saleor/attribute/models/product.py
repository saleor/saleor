from django.contrib.postgres.indexes import BTreeIndex
from django.db import models

from ...core.models import SortableModel
from ...product.models import Product, ProductType
from .base import AssociatedAttributeManager, BaseAssignedAttribute


class AssignedProductAttributeValue(SortableModel):
    value = models.ForeignKey(
        "AttributeValue",
        on_delete=models.CASCADE,
        related_name="productvalueassignment",
    )
    assignment = models.ForeignKey(
        "AssignedProductAttribute",
        on_delete=models.CASCADE,
        related_name="productvalueassignment",
    )

    product = models.ForeignKey(
        Product,
        related_name="attributevalues",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=False,
    )

    class Meta:
        unique_together = (("value", "assignment"),)
        ordering = ("sort_order", "pk")
        indexes = [
            BTreeIndex(fields=["product"], name="assignedprodattrval_product_idx")
        ]

    def get_ordering_queryset(self):
        return self.assignment.productvalueassignment.all()


class AssignedProductAttribute(BaseAssignedAttribute):
    """Associate a product type attribute and selected values to a given product."""

    product = models.ForeignKey(
        Product, related_name="attributes", on_delete=models.CASCADE
    )
    assignment = models.ForeignKey(
        "AttributeProduct", on_delete=models.CASCADE, related_name="productassignments"
    )
    values = models.ManyToManyField(
        "AttributeValue",
        blank=True,
        related_name="productassignments",
        through=AssignedProductAttributeValue,
    )

    class Meta:
        unique_together = (("product", "assignment"),)


class AttributeProduct(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributeproduct", on_delete=models.CASCADE
    )
    product_type = models.ForeignKey(
        ProductType, related_name="attributeproduct", on_delete=models.CASCADE
    )
    assigned_products = models.ManyToManyField(
        Product,
        blank=True,
        through=AssignedProductAttribute,
        through_fields=("assignment", "product"),
        related_name="attributesrelated",
    )

    objects = AssociatedAttributeManager()

    class Meta:
        unique_together = (("attribute", "product_type"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.product_type.attributeproduct.all()
