from typing import Callable, Optional

from ...permission.enums import ProductPermissions
from ...webhook.base import AsyncWebhookBase
from ...webhook.payloads import generate_product_payload


class ProductCreated(AsyncWebhookBase):
    description = "A new product is created."
    event_type = "product_created"
    name = "Product Created"
    permission = ProductPermissions.MANAGE_PRODUCTS
    subscription_type = "saleor.graphql.product.subscriptions.ProductCreated"

    @classmethod
    def legacy_payload_func(cls) -> Optional[Callable]:
        return generate_product_payload
