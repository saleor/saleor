from django.core.exceptions import ValidationError
from django.db.models import Q

from ....product.models import ProductVariant as ProductVariantModel
from ....tax.models import TaxClass
from ...core import ResolveInfo
from ...core.validators import validate_one_of_args_is_in_mutation
from ..types import ProductVariant

PRODUCT_VARIANT_UPDATE_FIELDS = {
    "external_reference",
    "is_preorder",
    "metadata",
    "name",
    "preorder_end_date",
    "preorder_global_threshold",
    "private_metadata",
    "quantity_limit_per_customer",
    "sku",
    "track_inventory",
    "weight",
}


def clean_tax_code(cleaned_input: dict):
    """Clean deprecated `taxCode` field.

    This function provides backwards compatibility for the `taxCode` input field. If the
    `taxClass` is not provided but the `taxCode` is, try to find a tax class with given
    tax code and assign it to the product type.
    """
    tax_code = cleaned_input.get("tax_code")
    if tax_code and "tax_class" not in cleaned_input:
        tax_class = TaxClass.objects.filter(
            Q(name=tax_code)
            | Q(metadata__contains={"avatax.code": tax_code})
            | Q(metadata__contains={"vatlayer.code": tax_code})
        ).first()
        cleaned_input["tax_class"] = tax_class


class VariantLookupMixin:
    """Resolve the product variant a mutation operates on.

    The variant is identified by exactly one of: global ID, SKU or external reference.
    """

    @classmethod
    def get_variant(
        cls,
        info: ResolveInfo,
        *,
        id: str | None,
        sku: str | None,
        external_reference: str | None,
        id_field: str = "id",
        external_reference_field: str = "external_reference",
    ) -> ProductVariantModel:
        validate_one_of_args_is_in_mutation(
            id_field,
            id,
            "sku",
            sku,
            external_reference_field,
            external_reference,
            use_camel_case=True,
        )
        if sku:
            variant = ProductVariantModel.objects.filter(sku=sku).first()
            if not variant:
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            f"Couldn't resolve to a node: {sku}", code="not_found"
                        )
                    }
                )
            return variant
        return cls.get_node_by_id_or_external_reference(  # type: ignore[attr-defined]
            info,
            node_id=id,
            external_reference=external_reference,
            only_type=ProductVariant,
            id_field=id_field,
            external_reference_field=external_reference_field,
            qs=ProductVariantModel.objects.all(),
        )
