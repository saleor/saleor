from decimal import Decimal

from prices import Money
from pydantic import BaseModel

from ...app.models import App
from ...shipping.interface import ShippingMethodData
from .shipping_common import to_shipping_app_id


def method_metadata_is_valid(metadata) -> bool:
    if not isinstance(metadata, dict):
        return False
    for key, value in metadata.items():
        if not isinstance(key, str) or not isinstance(value, str) or not key.strip():
            return False
    return True


class ShippingMethodSchema(BaseModel):
    id: str
    name: str
    amount: Decimal
    currency: str
    maximum_delivery_days: int | None = None
    minimum_delivery_days: int | None = None
    description: str | None = None
    metadata: dict[str, str] | None = None

    @property
    def price(self) -> Money:
        return Money(self.amount, self.currency)

    def get_shipping_method_data(self, app: "App"):
        return ShippingMethodData(
            id=to_shipping_app_id(app, self.id),
            name=self.name,
            price=self.price,
            maximum_delivery_days=self.maximum_delivery_days,
            minimum_delivery_days=self.minimum_delivery_days,
            description=self.description,
            metadata=self.get_cleaned_metadata(),
        )

    def get_cleaned_metadata(self) -> dict[str, str]:
        metadata = self.metadata
        if metadata:
            metadata = metadata if method_metadata_is_valid(metadata) else {}
        return metadata or {}
