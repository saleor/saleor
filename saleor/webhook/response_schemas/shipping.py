import logging
from decimal import Decimal
from typing import Annotated, Any, TypeVar

from graphql.error import GraphQLError
from prices import Money
from pydantic import (
    BaseModel,
    Field,
    RootModel,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    field_validator,
)
from pydantic_core import PydanticOmit

from ...graphql.core.utils import from_global_id_or_error
from ...shipping.models import ShippingMethod
from ..const import APP_ID_PREFIX
from .annotations import DefaultIfNone, Metadata

logger = logging.getLogger(__name__)

name_max_length = ShippingMethod._meta.get_field("name").max_length

T = TypeVar("T")


def skip_invalid_shipping_method(
    value: Any, handler: ValidatorFunctionWrapHandler
) -> Any:
    try:
        return handler(value)
    except ValidationError as err:
        logger.warning("Skipping invalid shipping method: %s", err)
        raise PydanticOmit() from err


OnErrorSkipShippingMethod = Annotated[T, WrapValidator(skip_invalid_shipping_method)]


class ShippingMethodSchema(BaseModel):
    id: str = Field(coerce_numbers_to_str=True)
    name: str = Field(max_length=name_max_length)
    amount: Decimal = Field(ge=0)
    currency: str
    maximum_delivery_days: Annotated[int, Field(ge=0)] | None = None
    minimum_delivery_days: Annotated[int, Field(ge=0)] | None = None
    description: str | None = None
    metadata: DefaultIfNone[Metadata] = {}

    @property
    def price(self) -> Money:
        return Money(self.amount, self.currency)


class ListShippingMethodsSchema(RootModel):
    root: DefaultIfNone[list[OnErrorSkipShippingMethod[ShippingMethodSchema]]] = []


class ExcludedShippingMethodSchema(BaseModel):
    id: str
    reason: DefaultIfNone[str] = ""

    @field_validator("id", mode="after")
    @classmethod
    def clean_id(cls, value: str) -> str:
        try:
            type_name, method_id = from_global_id_or_error(value)
        except (KeyError, ValueError, TypeError, GraphQLError) as e:
            error_msg = "Malformed ShippingMethod id was provided: %s"
            logger.warning(error_msg, value)
            raise ValueError(error_msg, e) from e

        if type_name not in (APP_ID_PREFIX, "ShippingMethod"):
            error_msg = "Invalid type received. Expected ShippingMethod, got %s"
            logger.warning(error_msg, type_name)
            raise ValueError(error_msg, type_name)
        return method_id


class FilterShippingMethodsSchema(BaseModel):
    excluded_methods: DefaultIfNone[
        list[OnErrorSkipShippingMethod[ExcludedShippingMethodSchema]]
    ] = []
