from collections.abc import Iterable, Mapping

import graphene
from django.core.exceptions import ValidationError
from graphene.utils.str_converters import to_camel_case

from .....discount import VoucherType
from .....discount.error_codes import DiscountErrorCode
from .....discount.interface import VOUCHER_CATALOGUE_RELATIONS
from ....core.mutations import BaseMutation
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
    f"Max {VOUCHER_CATALOGUE_ITEMS_LIMIT} items per call."
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

# `VoucherInput` and the deprecated `CatalogueInput` keep their include lists
# uncapped for backward compatibility; only fields added with exclusions are capped.
LIMITED_VOUCHER_INPUT_FIELDS = ("product_types",) + tuple(
    relation.excluded_field for relation in VOUCHER_CATALOGUE_RELATIONS
)


def validate_voucher_catalogue_items_limit(
    data: Mapping, fields: Iterable[str]
) -> None:
    errors = {
        field: ValidationError(
            f"Cannot provide more than {VOUCHER_CATALOGUE_ITEMS_LIMIT} items.",
            code=DiscountErrorCode.INVALID.value,
        )
        for field in fields
        if len(data.get(field) or ()) > VOUCHER_CATALOGUE_ITEMS_LIMIT
    }
    if errors:
        raise ValidationError(errors)


def resolve_voucher_catalogue_nodes(catalogue_ids: Mapping) -> dict[str, list]:
    """Resolve catalogue IDs to nodes, rejecting IDs of the wrong type."""
    return {
        field: BaseMutation.get_nodes_or_error(ids, field, only_type=node_type)
        for field, node_type in VOUCHER_CATALOGUE_NODE_TYPES.items()
        if (ids := catalogue_ids.get(field))
    }


def clean_voucher_catalogue(
    voucher_type: str,
    catalogue: Mapping[str, set[int]],
    input_pks: Mapping[str, set[int]],
) -> None:
    """Validate the catalogue the voucher would end up with.

    `catalogue` maps every Voucher catalogue M2M field name to the PKs it would
    hold after the mutation; `input_pks` holds the PKs the mutation's input
    provides. Exclusions are rejected, not ignored, outside SPECIFIC_PRODUCT
    vouchers, so an excluded line can never get discounted by a voucher type
    that spreads over all lines.
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
            # Report on the list the input adds the items to and ask to remove
            # them from the other one; exclusions win when the input sets both.
            error_field, other_field = (
                (relation.excluded_field, relation.included_field)
                if conflicting_pks & input_pks.get(relation.excluded_field, set())
                else (relation.included_field, relation.excluded_field)
            )
            type_name = VOUCHER_CATALOGUE_NODE_TYPES[relation.included_field]
            conflicting_ids = ", ".join(
                graphene.Node.to_global_id(type_name._meta.name, pk)
                for pk in sorted(conflicting_pks)
            )
            errors[error_field] = ValidationError(
                f"Cannot both include and exclude the same items: "
                f"{conflicting_ids}. Remove them from "
                f"`{to_camel_case(other_field)}` first.",
                code=DiscountErrorCode.INVALID.value,
            )
    if errors:
        raise ValidationError(errors)
