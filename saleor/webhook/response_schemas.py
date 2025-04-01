import logging
from decimal import Decimal
from typing import Any, cast

from graphql.error import GraphQLError
from prices import Money
from pydantic import BaseModel, Field, RootModel, ValidationError, field_validator

from ..app.models import App
from ..core.utils.metadata_manager import method_metadata_is_valid
from ..graphql.core.utils import from_global_id_or_error
from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethod
from .const import APP_ID_PREFIX
from .transport.shipping_helpers import to_shipping_app_id

logger = logging.getLogger(__name__)

name_max_length = ShippingMethod._meta.get_field("name").max_length


class ShippingMethodSchema(BaseModel):
    id: str | int
    name: str = Field(..., max_length=name_max_length)
    amount: Decimal = Field(..., ge=0)
    currency: str
    maximum_delivery_days: int | None = Field(None, ge=0)
    minimum_delivery_days: int | None = Field(None, ge=0)
    description: str | None = None
    metadata: dict[str, str] | None = {}

    @field_validator("metadata", mode="before")
    @classmethod
    def clean_metadata(cls, value: Any) -> dict[str, str]:
        metadata = value
        if metadata:
            metadata = metadata if method_metadata_is_valid(metadata) else {}
        return metadata or {}

    @property
    def price(self) -> Money:
        return Money(self.amount, self.currency)

    def get_shipping_method_data(self, app: "App"):
        metadata = cast(
            dict[str, str],
            self.metadata,
        )
        return ShippingMethodData(
            id=to_shipping_app_id(app, str(self.id)),
            name=self.name,
            price=self.price,
            maximum_delivery_days=self.maximum_delivery_days,
            minimum_delivery_days=self.minimum_delivery_days,
            description=self.description,
            metadata=metadata,
        )


class ListShippingMethodsSchema(RootModel):
    root: list[ShippingMethodSchema]

    @field_validator("root", mode="before")
    @classmethod
    def check_valid_list(cls, value: Any):
        # return the empty list for None to ensure the backward compatibility;
        if value is None:
            return []

        # in case the data are not list, handle validation by pydantic
        if not isinstance(value, list):
            return value

        methods = []
        for method_data in value:
            try:
                methods.append(ShippingMethodSchema.model_validate(method_data))
            except ValidationError as e:
                logger.warning("Skipping invalid shipping method: %s", e)
        return methods

    def get_shipping_methods_data(self, app: "App") -> list[ShippingMethodData]:
        return [
            shipping_method.get_shipping_method_data(app)
            for shipping_method in self.root
        ]


class ExcludedShippingMethodSchema(BaseModel):
    id: str
    reason: str | None = ""

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

    @field_validator("reason", mode="after")
    @classmethod
    def clean_reason(cls, value: str | None) -> str:
        return value or ""


class FilterShippingMethodsSchema(BaseModel):
    excluded_methods: list[ExcludedShippingMethodSchema]

    @field_validator("excluded_methods", mode="before")
    @classmethod
    def clean_excluded_methods(cls, value: Any):
        # return the empty list for None to ensure the backward compatibility;
        if value is None:
            return []

        # in case the data are not list, handle validation by pydantic
        if not isinstance(value, list):
            return value

        excluded_methods = []
        for method_data in value:
            try:
                excluded_methods.append(
                    ExcludedShippingMethodSchema.model_validate(method_data)
                )
            except ValidationError:
                continue
        return excluded_methods
