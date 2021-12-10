from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional

import graphql
from measurement.measures import Weight
from prices import Money

from ..graphql.core.utils import from_global_id_or_error

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


@dataclass
class ShippingMethodData:
    """Dataclass for storing information about a shipping method."""

    id: str
    price: Optional[Money]
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    maximum_order_price: Optional[Money] = None
    minimum_order_price: Optional[Money] = None
    excluded_products: Optional["RelatedManager"] = None
    channel_listings: Optional["RelatedManager"] = None
    minimum_order_weight: Optional[Weight] = None
    maximum_order_weight: Optional[Weight] = None
    maximum_delivery_days: Optional[int] = None
    minimum_delivery_days: Optional[int] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    private_metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def is_external(self) -> bool:
        try:
            type_, _ = from_global_id_or_error(self.id)
            str_type = str(type_)
        except graphql.error.base.GraphQLError:
            pass
        else:
            return str_type == "app"

        return False
