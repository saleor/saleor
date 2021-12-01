from typing import TYPE_CHECKING, Union

from django.db.models import prefetch_related_objects

from ..attribute import AttributeInputType
from ..core.utils.editorjs import clean_editor_js

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ..attribute.models import AssignedProductAttribute, AssignedVariantAttribute
    from .models import Product

ASSIGNED_ATTRIBUTE_TYPE = Union["AssignedProductAttribute", "AssignedVariantAttribute"]

PRODUCT_SEARCH_FIELDS = ["name", "description_plaintext"]


def prepare_product_search_document_value(product: "Product"):
    prefetch_related_objects(
        [product],
        "variants__attributes__values",
        "variants__attributes__assignment__attribute",
        "attributes__values",
        "attributes__assignment__attribute",
    )
    search_document = generate_product_fields_search_document_value(product)
    search_document += generate_attributes_search_document_value(
        product.attributes.all()
    )
    search_document += generate_variants_search_document_value(product)

    return search_document.lower()


def generate_product_fields_search_document_value(product: "Product"):
    value = "\n".join(
        [
            getattr(product, field)
            for field in PRODUCT_SEARCH_FIELDS
            if getattr(product, field)
        ]
    )
    if value:
        value += "\n"
    return value.lower()


def generate_variants_search_document_value(product: "Product"):
    variants = product.variants.all()
    variants_data = "\n".join([variant.sku for variant in variants if variant.sku])
    if variants_data:
        variants_data += "\n"

    for variant in variants:
        variant_attribute_data = generate_attributes_search_document_value(
            variant.attributes.all()
        )
        if variant_attribute_data:
            variants_data += variant_attribute_data

    return variants_data.lower()


def generate_attributes_search_document_value(
    assigned_attributes: "QuerySet",
):
    """Prepare `search_document` value for assigned attributes.

    Method should received assigned attributes with prefetched `values`
    and `assignment__attribute`.
    """
    attribute_data = ""
    for assigned_attribute in assigned_attributes:
        attribute = assigned_attribute.assignment.attribute

        input_type = attribute.input_type
        values = assigned_attribute.values.all()
        if input_type in [AttributeInputType.DROPDOWN, AttributeInputType.MULTISELECT]:
            values_list = [value.name for value in values]
        elif input_type == AttributeInputType.RICH_TEXT:
            values_list = [
                clean_editor_js(value.rich_text, to_string=True) for value in values
            ]
        elif input_type == AttributeInputType.NUMERIC:
            unit = attribute.unit
            values_list = [value.name + unit for value in values]
        elif input_type in [AttributeInputType.DATE, AttributeInputType.DATE_TIME]:
            values_list = [value.date_time.isoformat() for value in values]

        values_data = "\n".join(values_list)
        if values_data:
            attribute_data += values_data + "\n"
    return attribute_data.lower()
