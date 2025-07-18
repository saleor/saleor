from django.db.models import QuerySet

from .models.base import AttributeValue


def attribute_value_qs_select_for_update() -> QuerySet[AttributeValue]:
    return AttributeValue.objects.order_by("sort_order", "pk").select_for_update(
        of=(["self"])
    )
