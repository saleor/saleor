from ...permission.enums import ProductPermissions
from ...webhook.base import WebhookSpec, register


class ProductCreated(WebhookSpec):
    description = "A new product is created."
    event_type = "product_created"
    name = "Product Created"
    permission = ProductPermissions.MANAGE_PRODUCTS
    subscription_type = "saleor.graphql.product.subscriptions.ProductCreated"

    @staticmethod
    def legacy_payload(product):
        return {}


register(ProductCreated)
