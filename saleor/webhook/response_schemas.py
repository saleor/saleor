import logging
from decimal import Decimal
from typing import Any

from graphql.error import GraphQLError
from prices import Money
from pydantic import BaseModel, field_validator

from ..app.models import App
from ..graphql.core.utils import from_global_id_or_error
from ..shipping.interface import ShippingMethodData
from .const import APP_ID_PREFIX
from .transport.shipping_helpers import to_shipping_app_id

logger = logging.getLogger(__name__)


class ShippingMethodSchema(BaseModel):
    id: str | int
    name: str
    amount: Decimal
    currency: str
    maximum_delivery_days: int | None = None
    minimum_delivery_days: int | None = None
    description: str | None = None
    metadata: dict[str, str] | None = None

    @field_validator("metadata", mode="before")
    @classmethod
    def clean_metadata(cls, value: Any) -> dict[str, str]:
        metadata = value
        if metadata:
            metadata = metadata if cls.method_metadata_is_valid(metadata) else {}
        return metadata or {}

    @classmethod
    def method_metadata_is_valid(cls, metadata: Any) -> bool:
        if not isinstance(metadata, dict):
            return False
        for key, value in metadata.items():
            if (
                not isinstance(key, str)
                or not isinstance(value, str)
                or not key.strip()
            ):
                return False
        return True

    @property
    def price(self) -> Money:
        return Money(self.amount, self.currency)

    def get_shipping_method_data(self, app: "App"):
        # metadata might be `None` in case it was not provided in the input
        # in such case the `field_validator` is not called and the self.metadata
        # is `None` instead of an empty dict
        metadata = self.metadata or {}
        return ShippingMethodData(
            id=to_shipping_app_id(app, str(self.id)),
            name=self.name,
            price=self.price,
            maximum_delivery_days=self.maximum_delivery_days,
            minimum_delivery_days=self.minimum_delivery_days,
            description=self.description,
            metadata=metadata,
        )


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
