import graphene
from django.core.exceptions import ValidationError

from .....attribute import models as attribute_models
from .....product.error_codes import ProductErrorCode
from .....product.models import ProductType
from ....attribute.utils.shared import (
    AttrValuesInput,
)

T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]


def clean_weight(cleaned_input: dict):
    weight = cleaned_input.get("weight")
    if weight and weight.value < 0:
        raise ValidationError(
            {
                "weight": ValidationError(
                    "Product variant can't have negative weight.",
                    code=ProductErrorCode.INVALID.value,
                )
            }
        )


def clean_quantity_limit(cleaned_input: dict):
    quantity_limit_per_customer = cleaned_input.get("quantity_limit_per_customer")
    if quantity_limit_per_customer is not None and quantity_limit_per_customer < 1:
        raise ValidationError(
            {
                "quantity_limit_per_customer": ValidationError(
                    (
                        "Product variant can't have "
                        "quantity_limit_per_customer lower than 1."
                    ),
                    code=ProductErrorCode.INVALID.value,
                )
            }
        )


def clean_preorder_settings(cleaned_input: dict):
    preorder_settings = cleaned_input.get("preorder")
    if preorder_settings:
        cleaned_input["is_preorder"] = True
        cleaned_input["preorder_global_threshold"] = preorder_settings.get(
            "global_threshold"
        )
        cleaned_input["preorder_end_date"] = preorder_settings.get("end_date")


def clean_variant_attributes(product_type: "ProductType", attributes: list[dict]):
    variant_attributes_ids = set()
    variant_attributes_external_refs = set()
    for attr_id, external_ref in product_type.variant_attributes.values_list(
        "id", "external_reference"
    ):
        if external_ref:
            variant_attributes_external_refs.add(external_ref)
        variant_attributes_ids.add(graphene.Node.to_global_id("Attribute", attr_id))

    attributes_ids = {attr["id"] for attr in attributes if attr.get("id") or []}
    attrs_external_refs = {
        attr["external_reference"]
        for attr in attributes
        if attr.get("external_reference") or []
    }
    invalid_attributes = attributes_ids - variant_attributes_ids
    invalid_attributes |= attrs_external_refs - variant_attributes_external_refs
    if len(invalid_attributes) > 0:
        raise ValidationError(
            "Given attributes are not a variant attributes.",
            code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.value,
            params={"attributes": invalid_attributes},
        )
