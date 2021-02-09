from django.db import models

from ...core.models import SortableModel
from ...product.models import Collection
from ...site.models import SiteSettings
from .base import AssociatedAttributeQuerySet, BaseAssignedAttribute


class AssignedCollectionAttributeValue(SortableModel):
    value = models.ForeignKey(
        "AttributeValue",
        on_delete=models.CASCADE,
        related_name="collectionvalueassignment",
    )
    assignment = models.ForeignKey(
        "AssignedCollectionAttribute",
        on_delete=models.CASCADE,
        related_name="collectionvalueassignment",
    )

    class Meta:
        unique_together = (("value", "assignment"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.assignment.collectionvalueassignment.all()


class AssignedCollectionAttribute(BaseAssignedAttribute):
    """Associate an attribute and selected values to a given collection."""

    collection = models.ForeignKey(
        Collection, related_name="attributes", on_delete=models.CASCADE
    )
    assignment = models.ForeignKey(
        "AttributeCollection",
        on_delete=models.CASCADE,
        related_name="collectionassignments",
    )
    values = models.ManyToManyField(
        "AttributeValue",
        blank=True,
        related_name="collectionassignments",
        through=AssignedCollectionAttributeValue,
    )

    class Meta:
        unique_together = (("collection", "assignment"),)


class AttributeCollection(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="collection_attributes", on_delete=models.CASCADE
    )
    site_settings = models.ForeignKey(
        SiteSettings, related_name="collection_attributes", on_delete=models.CASCADE
    )

    objects = AssociatedAttributeQuerySet.as_manager()

    class Meta:
        unique_together = (("attribute", "site_settings"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.site_settings.collection_attributes.all()
