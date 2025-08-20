from django.db.models import QuerySet

from .models.base import Attribute, AttributeValue


def attribute_value_qs_select_for_update() -> QuerySet[AttributeValue]:
    return AttributeValue.objects.order_by("sort_order", "pk").select_for_update(
        of=(["self"])
    )


def attribute_reference_product_types_qs_select_for_update() -> QuerySet:
    return Attribute.reference_product_types.through.objects.order_by(
        "pk"
    ).select_for_update(of=["self"])


def attribute_reference_page_types_qs_select_for_update() -> QuerySet:
    return Attribute.reference_page_types.through.objects.order_by(
        "pk"
    ).select_for_update(of=["self"])
