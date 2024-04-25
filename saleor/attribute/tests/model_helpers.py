from django.db.models.expressions import Exists, OuterRef

from ...page.models import Page
from ...product.models import Product
from ..models import (
    AssignedPageAttributeValue,
    AssignedProductAttributeValue,
    Attribute,
    AttributePage,
    AttributeProduct,
    AttributeValue,
)


def get_page_attributes(page: Page):
    page_attributes = AttributePage.objects.filter(page_type_id=page.page_type_id)

    return Attribute.objects.filter(
        Exists(page_attributes.filter(attribute_id=OuterRef("id")))
    ).order_by("attributepage__sort_order", "attributepage__pk")


def get_page_attribute_values(page: Page, attribute: Attribute):
    assigned_values = AssignedPageAttributeValue.objects.filter(page_id=page.pk)

    values = AttributeValue.objects.filter(attribute_id=attribute.pk)
    return values.filter(
        Exists(assigned_values.filter(value_id=OuterRef("id"))),
    ).order_by("pagevalueassignment__sort_order", "pagevalueassignment__pk")


def get_product_attributes(product: Product):
    """Get product attributes filtered by product_type.

    ProductType defines which attributes can be assigned to a product and
    we have to filter out the attributes on the instance by the ones attached to the
    product_type.
    """
    product_attributes = AttributeProduct.objects.filter(
        product_type_id=product.product_type_id
    )
    return Attribute.objects.filter(
        Exists(product_attributes.filter(attribute_id=OuterRef("id")))
    ).order_by("storefront_search_position", "slug")


def get_product_attribute_values(product: Product, attribute: Attribute):
    """Get values assigned to a product.

    Note: this doesn't filter out attributes that might have been unassigned from the
    product type.
    """
    assigned_values = AssignedProductAttributeValue.objects.filter(
        product_id=product.pk
    )

    return AttributeValue.objects.filter(
        Exists(
            assigned_values.filter(value_id=OuterRef("id")),
        ),
        attribute_id=attribute.pk,
    ).order_by("productvalueassignment__sort_order")
