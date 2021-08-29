from dataclasses import dataclass
from prices import Money


@dataclass
class ShippingMethod:
    """Dataclass for storing information about a shipping method."""

    id: str
    name: str
    price: Money
