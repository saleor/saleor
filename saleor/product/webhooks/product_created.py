from ...permission.enums import ProductPermissions
from ...webhook.base import WebhookBase, register


class ProductCreated(WebhookBase):
    description = "A new product is created."
    event_type = "product_created"
    name = "Product Created"
    permission = ProductPermissions.MANAGE_PRODUCTS
    subscription_type = "saleor.graphql.product.subscriptions.ProductCreated"


register(ProductCreated)
