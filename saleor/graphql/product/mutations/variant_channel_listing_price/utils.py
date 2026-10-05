from decimal import Decimal

import graphene
from django.core.exceptions import ValidationError

from .....product.utils.scoped_price_rows import get_ineligible_attribute_value_ids
from ....account.types import CustomerType
from ....attribute.types import AttributeValue
from ....core.enums import VariantChannelListingPriceErrorCode
from ....core.mutations import BaseMutation
from ....core.scalars import DateTime
from ....core.types import BaseInputObjectType, Error, NonNullList
from ....core.validators import validate_price_precision

MAX_CONDITIONS_PER_DIMENSION = 100


class VariantChannelListingPriceScopeInput(BaseInputObjectType):
    customer_types = NonNullList(
        graphene.ID,
        description=(
            "Customer types the buyer must belong to. The number of items is "
            f"limited to {MAX_CONDITIONS_PER_DIMENSION}."
        ),
    )
    attribute_values = NonNullList(
        graphene.ID,
        description=(
            "Values of customer attributes the buyer must hold, one per attribute "
            "is enough. Only values of customer attributes with a fixed set of "
            "choices are accepted. The number of items is limited to "
            f"{MAX_CONDITIONS_PER_DIMENSION}."
        ),
    )
    valid_from = DateTime(
        description="The start of the validity window, inclusive. Null means no start."
    )
    valid_to = DateTime(
        description=(
            "The end of the validity window, exclusive. Null means no end. Must be "
            "after `validFrom` when both are set."
        )
    )

    class Meta:
        abstract = True


class VariantChannelListingPriceErrorBase(Error):
    code = VariantChannelListingPriceErrorCode(
        description="The error code.", required=True
    )
    customer_types = NonNullList(
        graphene.ID,
        description="List of customer type IDs which cause the error.",
        required=False,
    )
    attribute_values = NonNullList(
        graphene.ID,
        description="List of attribute value IDs which cause the error.",
        required=False,
    )

    class Meta:
        abstract = True


def clean_price(price: Decimal, currency: str) -> Decimal:
    try:
        validate_price_precision(price, currency)
    except ValidationError as error:
        raise ValidationError(
            {
                "price": ValidationError(
                    error.message,
                    code=VariantChannelListingPriceErrorCode.INVALID.value,
                )
            }
        ) from error
    return price


def clean_customer_type_ids(
    mutation: type[BaseMutation], ids: list[str]
) -> frozenset[int]:
    if not ids:
        return frozenset()
    _validate_list_size(ids, "customer_types")
    customer_types = mutation.get_nodes_or_error(ids, "customer_types", CustomerType)
    return frozenset(customer_type.pk for customer_type in customer_types)


def clean_attribute_value_ids(
    mutation: type[BaseMutation], ids: list[str]
) -> frozenset[int]:
    if not ids:
        return frozenset()
    _validate_list_size(ids, "attribute_values")
    values = mutation.get_nodes_or_error(ids, "attribute_values", AttributeValue)
    value_ids = frozenset(value.pk for value in values)
    if ineligible_ids := get_ineligible_attribute_value_ids(value_ids):
        raise ValidationError(
            {
                "attribute_values": ValidationError(
                    "Only values of customer attributes with a fixed set of choices "
                    "can scope a price.",
                    code=VariantChannelListingPriceErrorCode.INVALID.value,
                    params={
                        "attribute_values": [
                            graphene.Node.to_global_id("AttributeValue", value_id)
                            for value_id in sorted(ineligible_ids)
                        ]
                    },
                )
            }
        )
    return value_ids


def _validate_list_size(ids: list[str], field: str) -> None:
    if len(ids) > MAX_CONDITIONS_PER_DIMENSION:
        raise ValidationError(
            {
                field: ValidationError(
                    f"Provide at most {MAX_CONDITIONS_PER_DIMENSION} items.",
                    code=VariantChannelListingPriceErrorCode.INVALID.value,
                )
            }
        )
