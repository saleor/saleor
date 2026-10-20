from collections.abc import Mapping

import graphene
from django.core.exceptions import ValidationError
from graphene.utils.str_converters import to_camel_case

from .....discount import VoucherType
from .....discount.error_codes import DiscountErrorCode
from .....discount.interface import VOUCHER_CATALOGUE_RELATIONS
from ....core.types import ModelObjectType
from ....product.types import (
    Category,
    Collection,
    Product,
    ProductType,
    ProductVariant,
)

VOUCHER_CATALOGUE_ITEMS_LIMIT = 100

EXCLUSION_DESCRIPTION = (
    "{entity} excluded from the voucher discount, even when matched by the "
    "voucher's includes. Only allowed for vouchers of type SPECIFIC_PRODUCT. "
    f"Max {VOUCHER_CATALOGUE_ITEMS_LIMIT} items."
)

_NODE_TYPE_BY_INCLUDED_FIELD: dict[str, type[ModelObjectType]] = {
    "products": Product,
    "variants": ProductVariant,
    "collections": Collection,
    "categories": Category,
    "product_types": ProductType,
}
VOUCHER_CATALOGUE_NODE_TYPES: dict[str, type[ModelObjectType]] = {
    field: _NODE_TYPE_BY_INCLUDED_FIELD[relation.included_field]
    for relation in VOUCHER_CATALOGUE_RELATIONS
    for field in (relation.included_field, relation.excluded_field)
}

LIMITED_VOUCHER_CATALOGUE_FIELDS = ("product_types",) + tuple(
    relation.excluded_field for relation in VOUCHER_CATALOGUE_RELATIONS
)


def validate_voucher_catalogue_items_limit(data: Mapping) -> None:
    errors = {
        field: ValidationError(
            f"Cannot provide more than {VOUCHER_CATALOGUE_ITEMS_LIMIT} items.",
            code=DiscountErrorCode.INVALID.value,
        )
        for field in LIMITED_VOUCHER_CATALOGUE_FIELDS
        if len(data.get(field) or ()) > VOUCHER_CATALOGUE_ITEMS_LIMIT
    }
    if errors:
        raise ValidationError(errors)


def clean_voucher_catalogue(
    voucher_type: str, catalogue: Mapping[str, set[int]]
) -> None:
    """Validate the catalogue the voucher would end up with.

    `catalogue` maps every Voucher catalogue M2M field name to the PKs it would
    hold after the mutation. Exclusions are rejected, not ignored, outside
    SPECIFIC_PRODUCT vouchers, so an excluded line can never get discounted by
    a voucher type that spreads over all lines.
    """
    errors: dict[str, ValidationError] = {}
    for relation in VOUCHER_CATALOGUE_RELATIONS:
        included_pks = catalogue.get(relation.included_field, set())
        excluded_pks = catalogue.get(relation.excluded_field, set())
        if excluded_pks and voucher_type != VoucherType.SPECIFIC_PRODUCT:
            errors[relation.excluded_field] = ValidationError(
                "Exclusions are supported only by vouchers of type SPECIFIC_PRODUCT.",
                code=DiscountErrorCode.INVALID.value,
            )
        elif conflicting_pks := included_pks & excluded_pks:
            type_name = VOUCHER_CATALOGUE_NODE_TYPES[relation.included_field]
            conflicting_ids = ", ".join(
                graphene.Node.to_global_id(type_name._meta.name, pk)
                for pk in sorted(conflicting_pks)
            )
            errors[relation.excluded_field] = ValidationError(
                f"Cannot both include and exclude the same items: "
                f"{conflicting_ids}. Remove them from "
                f"`{to_camel_case(relation.included_field)}` or "
                f"`{to_camel_case(relation.excluded_field)}` first.",
                code=DiscountErrorCode.INVALID.value,
            )
    if errors:
        raise ValidationError(errors)
