from django.contrib.postgres.indexes import BTreeIndex
from django.db import models

from ...core.models import SortableModel
from ...page.models import Page, PageType
<<<<<<< HEAD
from .base import AssociatedAttributeManager, AttributeValue, BaseAssignedAttribute
=======
from .base import AssociatedAttributeManager
>>>>>>> daa98bf1f3 (Simplify Page <> Attribute relation)


class AssignedPageAttributeValue(SortableModel):
    value = models.ForeignKey(
        "AttributeValue",
        on_delete=models.CASCADE,
        related_name="pagevalueassignment",
    )
    page = models.ForeignKey(
        Page,
        related_name="attributevalues",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_index=False,
    )

    class Meta:
        unique_together = (("value", "page"),)
        ordering = ("sort_order", "pk")
        indexes = [BTreeIndex(fields=["page"], name="assignedpageattrvalue_page_idx")]

    def get_ordering_queryset(self):
<<<<<<< HEAD
        return self.assignment.pagevalueassignment.all()


class AssignedPageAttribute(BaseAssignedAttribute):
    """Associate a page type attribute and selected values to a given page."""

    page = models.ForeignKey(Page, related_name="attributes", on_delete=models.CASCADE)
    assignment = models.ForeignKey(
        "AttributePage", on_delete=models.CASCADE, related_name="pageassignments"
    )
    values = models.ManyToManyField(
        AttributeValue,
        blank=True,
        related_name="pageassignments",
        through=AssignedPageAttributeValue,
    )

    class Meta:
        unique_together = (("page", "assignment"),)
=======
        return self.page.attributevalues.all()
>>>>>>> daa98bf1f3 (Simplify Page <> Attribute relation)


class AttributePage(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributepage", on_delete=models.CASCADE
    )
    page_type = models.ForeignKey(
        PageType, related_name="attributepage", on_delete=models.CASCADE
    )

    objects = AssociatedAttributeManager()

    class Meta:
        unique_together = (("attribute", "page_type"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.page_type.attributepage.all()
