from django.db import models

from ...core.models import SortableModel
from ...product.models import Category
from ...site.models import SiteSettings
from .base import AssociatedAttributeQuerySet, BaseAssignedAttribute


class AssignedCategoryAttributeValue(SortableModel):
    value = models.ForeignKey(
        "AttributeValue",
        on_delete=models.CASCADE,
        related_name="categoryvalueassignment",
    )
    assignment = models.ForeignKey(
        "AssignedCategoryAttribute",
        on_delete=models.CASCADE,
        related_name="categoryvalueassignment",
    )

    class Meta:
        unique_together = (("value", "assignment"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.assignment.categoryvalueassignment.all()


class AssignedCategoryAttribute(BaseAssignedAttribute):
    """Associate an attribute and selected values to a given category."""

    category = models.ForeignKey(
        Category, related_name="attributes", on_delete=models.CASCADE
    )
    assignment = models.ForeignKey(
        "AttributeCategory",
        on_delete=models.CASCADE,
        related_name="categoryassignments",
    )
    values = models.ManyToManyField(
        "AttributeValue",
        blank=True,
        related_name="categoryassignments",
        through=AssignedCategoryAttributeValue,
    )

    class Meta:
        unique_together = (("category", "assignment"),)


class AttributeCategory(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="category_attributes", on_delete=models.CASCADE
    )
    site_settings = models.ForeignKey(
        SiteSettings, related_name="category_attributes", on_delete=models.CASCADE
    )

    objects = AssociatedAttributeQuerySet.as_manager()

    class Meta:
        unique_together = (("attribute", "site_settings"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.site_settings.category_attributes.all()
