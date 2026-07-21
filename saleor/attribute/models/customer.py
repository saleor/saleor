from django.contrib.postgres.indexes import BTreeIndex
from django.db import models

from ...account.models import CustomerType, User
from ...core.models import SortableModel
from .base import AssociatedAttributeManager


class AssignedUserAttributeValue(SortableModel):
    value = models.ForeignKey(
        "AttributeValue",
        on_delete=models.CASCADE,
        related_name="uservalueassignment",
    )
    user = models.ForeignKey(
        User,
        related_name="attributevalues",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_index=False,
    )

    class Meta:
        unique_together = (("value", "user"),)
        ordering = ("sort_order", "pk")
        indexes = [BTreeIndex(fields=["user"], name="assigneduserattrvalue_user_idx")]

    def get_ordering_queryset(self):
        return self.user.attributevalues.all()


class AttributeCustomerType(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributecustomertype", on_delete=models.CASCADE
    )
    customer_type = models.ForeignKey(
        CustomerType, related_name="attributecustomertype", on_delete=models.CASCADE
    )

    objects = AssociatedAttributeManager()

    class Meta:
        unique_together = (("attribute", "customer_type"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.customer_type.attributecustomertype.all()
