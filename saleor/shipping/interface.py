from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import graphene
import graphql
from measurement.measures import Weight
from prices import Money

from ..graphql.core.utils import from_global_id_or_error
from ..plugins.const import APP_ID_PREFIX

if TYPE_CHECKING:
    from ..tax.models import TaxClass


@dataclass
class ShippingMethodData:
    """Dataclass for storing information about a shipping method."""

    id: str
    price: Money
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    maximum_order_price: Optional[Money] = None
    minimum_order_price: Optional[Money] = None
    minimum_order_weight: Optional[Weight] = None
    maximum_order_weight: Optional[Weight] = None
    maximum_delivery_days: Optional[int] = None
    minimum_delivery_days: Optional[int] = None
    metadata: dict[str, str] = field(default_factory=dict)
    private_metadata: dict[str, str] = field(default_factory=dict)
    tax_class: Optional["TaxClass"] = None
    active: bool = True
    message: str = ""

    @property
    def is_external(self) -> bool:
        try:
            type_, _ = from_global_id_or_error(self.id)
            str_type = str(type_)
        except graphql.error.base.GraphQLError:
            pass
        else:
            return str_type == APP_ID_PREFIX

        return False

    @property
    def graphql_id(self):
        if self.is_external:
            return self.id
        return graphene.Node.to_global_id("ShippingMethod", self.id)
