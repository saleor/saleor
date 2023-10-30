from django.contrib.postgres.indexes import BTreeIndex
from django.db import models

from ...core.models import SortableModel
from ...page.models import Page, PageType
from .base import AssociatedAttributeManager


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
        return self.page.attributevalues.all()


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
