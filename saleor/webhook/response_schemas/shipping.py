import logging
from decimal import Decimal
from typing import Annotated, TypeVar

from graphql.error import GraphQLError
from prices import Money
from pydantic import (
    BaseModel,
    Field,
    RootModel,
    ValidationInfo,
    field_validator,
)

from ...app.models import App
from ...graphql.core.utils import from_global_id_or_error
from ...shipping.models import ShippingMethod
from ..const import APP_ID_PREFIX
from ..transport.shipping_helpers import to_shipping_app_id
from .utils.annotations import DefaultIfNone, Metadata, OnErrorSkip

logger = logging.getLogger(__name__)

name_max_length = ShippingMethod._meta.get_field("name").max_length

T = TypeVar("T")


class ShippingMethodSchema(BaseModel):
    id: Annotated[
        str, Field(coerce_numbers_to_str=True, description="ID of the shipping method.")
    ]
    name: Annotated[
        str,
        Field(max_length=name_max_length, description="Name of the shipping method."),
    ]
    amount: Annotated[
        Decimal,
        Field(
            ge=Decimal(0),
            description="Non-negative price the customer pays for delivery using this shipping method.",
            examples=[Decimal("10.00")],
        ),
    ]
    currency: Annotated[
        str,
        Field(
            description="Currency code for amount. Must match the currency of object for which the methods are defined."
        ),
    ]
    maximum_delivery_days: (
        Annotated[
            int,
            Field(
                ge=0,
                description="Maximum delivery days for delivery promise of shipping carrier.",
            ),
        ]
        | None
    ) = None
    minimum_delivery_days: (
        Annotated[
            int,
            Field(
                ge=0,
                description="Minimum delivery days for delivery promise of shipping carrier.",
            ),
        ]
        | None
    ) = None
    description: (
        Annotated[
            str,
            Field(max_length=255, description="Description of the shipping method."),
        ]
        | None
    ) = None
    metadata: DefaultIfNone[Metadata] = {}

    @property
    def price(self) -> Money:
        return Money(self.amount, self.currency)

    @field_validator("id", mode="after")
    @classmethod
    def clean_id(cls, shipping_method_id: str, info: ValidationInfo) -> str:
        app: App | None = info.context.get("app", None) if info.context else None
        if not app:
            raise RuntimeError("Missing app in context")
        return to_shipping_app_id(app, shipping_method_id)

    @field_validator("currency", mode="before")
    @classmethod
    def clean_currency(cls, value: str, info: ValidationInfo) -> str:
        currency: str | None = (
            info.context.get("currency", None) if info.context else None
        )
        if not currency:
            raise ValueError("Missing currency in context")
        if value != currency:
            error_msg = "ShippingMethod currency mismatch: expected %s, got %s"
            logger.warning(error_msg, currency, value, extra={"value": value})
            raise ValueError(error_msg % (currency, value))
        return value.upper()


class ListShippingMethodsSchema(RootModel):
    root: DefaultIfNone[list[OnErrorSkip[ShippingMethodSchema]]] = []


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
        list[OnErrorSkip[ExcludedShippingMethodSchema]]
    ] = []
