from django.db.models.expressions import Exists, OuterRef

from ...page.models import Page
from ..models import (
    AssignedPageAttributeValue,
    Attribute,
    AttributePage,
    AttributeValue,
)


def get_page_attributes(page: Page):
    page_attributes = AttributePage.objects.filter(page_type_id=page.page_type_id)

    return Attribute.objects.filter(
        Exists(page_attributes.filter(attribute_id=OuterRef("id")))
    ).order_by("attributepage__sort_order")


def get_page_attribute_values(page: Page, attribute: Attribute):
    assigned_values = AssignedPageAttributeValue.objects.filter(page_id=page.pk)

    values = AttributeValue.objects.filter(attribute_id=attribute.pk)
    return values.filter(
        Exists(assigned_values.filter(value_id=OuterRef("id"))),
    ).order_by("pagevalueassignment__sort_order")
