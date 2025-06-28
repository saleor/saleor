from django.db import models
from django.db.models import QuerySet

from ...account.models import User
from ...core.models import SortableModel


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
    )

    class Meta:
        unique_together = (("value", "user"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self) -> QuerySet["AssignedUserAttributeValue"]:
        return self.user.attributevalues.all()
