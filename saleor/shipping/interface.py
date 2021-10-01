from dataclasses import dataclass, field
from typing import Dict, List, Optional

from measurement.measures import Weight
from prices import Money


@dataclass
class ShippingMethodData:
    """Dataclass for storing information about a shipping method."""

    id: str
    name: str
    price: Optional[Money] = None
    description: Optional[str] = None
    type: Optional[str] = None
    maximum_order_price: Optional[Money] = None
    minimum_order_price: Optional[Money] = None
    excluded_products: Optional[List] = field(default_factory=list)
    minimum_order_weight: Optional[Weight] = None
    maximum_order_weight: Optional[Weight] = None
    maximum_delivery_days: Optional[int] = None
    minimum_delivery_days: Optional[int] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    private_metadata: Dict[str, str] = field(default_factory=dict)
    is_external: bool = False
