from django.db import models

from ...core.models import SortableModel
from ...page.models import Page, PageType
from .base import AssociatedAttributeManager, BaseAssignedAttribute


class AssignedPageAttributeValue(SortableModel):
    value = models.ForeignKey(
        "AttributeValue",
        on_delete=models.CASCADE,
        related_name="pagevalueassignment",
    )
    assignment = models.ForeignKey(
        "AssignedPageAttribute",
        on_delete=models.CASCADE,
        related_name="pagevalueassignment",
    )

    class Meta:
        unique_together = (("value", "assignment"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.assignment.pagevalueassignment.all()


class AssignedPageAttribute(BaseAssignedAttribute):
    """Associate a page type attribute and selected values to a given page."""

    page = models.ForeignKey(Page, related_name="attributes", on_delete=models.CASCADE)
    assignment = models.ForeignKey(
        "AttributePage", on_delete=models.CASCADE, related_name="pageassignments"
    )
    values = models.ManyToManyField(
        "AttributeValue",
        blank=True,
        related_name="pageassignments",
        through=AssignedPageAttributeValue,
    )

    class Meta:
        unique_together = (("page", "assignment"),)


class AttributePage(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributepage", on_delete=models.CASCADE
    )
    page_type = models.ForeignKey(
        PageType, related_name="attributepage", on_delete=models.CASCADE
    )
    assigned_pages = models.ManyToManyField(
        Page,
        blank=True,
        through=AssignedPageAttribute,
        through_fields=("assignment", "page"),
        related_name="attributesrelated",
    )

    objects = AssociatedAttributeManager()

    class Meta:
        unique_together = (("attribute", "page_type"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.page_type.attributepage.all()
