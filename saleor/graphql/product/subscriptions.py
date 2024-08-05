from ..core.descriptions import ADDED_IN_32
from ..webhook.subscription_types import Event, ProductBase, SubscriptionObjectType


class ProductCreated(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new product is created." + ADDED_IN_32
