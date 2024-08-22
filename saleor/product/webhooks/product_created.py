from ...permission.enums import ProductPermissions
from ...plugins.manager import PluginsManager
from ...webhook.base import AsyncWebhookBase


class ProductCreated(AsyncWebhookBase):
    description = "A new product is created."
    event_type = "product_created"
    legacy_manager_func = PluginsManager.product_created.__name__
    name = "Product Created"
    permission = ProductPermissions.MANAGE_PRODUCTS
    subscription_type = "saleor.graphql.product.subscriptions.ProductCreated"
