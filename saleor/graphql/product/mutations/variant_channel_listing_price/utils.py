from decimal import Decimal

import graphene
from django.core.exceptions import ValidationError

from ....core.enums import VariantChannelListingPriceErrorCode
from ....core.scalars import DateTime
from ....core.types import BaseInputObjectType, Error, NonNullList
from ....core.validators import validate_price_precision
from ....core.validators.buyer_conditions import (
    MAX_CONDITIONS_PER_DIMENSION,
)
from ....core.validators.buyer_conditions import (
    clean_attribute_value_ids as clean_attribute_value_ids_or_error,
)
from ....core.validators.buyer_conditions import (
    clean_customer_type_ids as clean_customer_type_ids_or_error,
)


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


def clean_customer_type_ids(ids: list[str]) -> frozenset[int]:
    try:
        return clean_customer_type_ids_or_error(
            ids, VariantChannelListingPriceErrorCode.INVALID.value
        )
    except ValidationError as error:
        raise ValidationError({"customer_types": error}) from error


def clean_attribute_value_ids(ids: list[str]) -> frozenset[int]:
    try:
        return clean_attribute_value_ids_or_error(
            ids,
            VariantChannelListingPriceErrorCode.INVALID.value,
            purpose="scope a price",
        )
    except ValidationError as error:
        raise ValidationError({"attribute_values": error}) from error
