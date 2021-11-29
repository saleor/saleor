import logging
from typing import Any, List

import graphene
from django.core.exceptions import ValidationError

from ...payment.gateways.utils import require_active_plugin
from ...product.models import Product
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..models import PluginConfiguration
from .utils import UserAdminContext, index_product_data_to_algolia

logger = logging.getLogger(__name__)


class AlgoliaPlugin(BasePlugin):
    DEFAULT_ACTIVE = False
    PLUGIN_NAME = "Algolia"
    PLUGIN_ID = "wecre8.algolia"
    CONFIGURATION_PER_CHANNEL = False
    PLUGIN_DESCRIPTION = "Plugin responsible for indexing data to Algolia."

    CONFIG_STRUCTURE = {
        "ALGOLIA_API_KEY": {
            "label": "Algolia API key",
            "help_text": "Algolia API key",
            "type": ConfigurationTypeField.SECRET,
        },
        "ALGOLIA_APPLICATION_ID": {
            "label": "Algolia application id",
            "help_text": "Algolia application id",
            "type": ConfigurationTypeField.SECRET,
        },
        "ALGOLIA_INDEX_PREFIX": {
            "label": "Algolia index prefix",
            "help_text": "Algolia index prefix",
            "type": ConfigurationTypeField.STRING,
        },
        "ALGOLIA_LOCALES": {
            "label": "Algolia Locales",
            "help_text": "Algolia Locales",
            "type": ConfigurationTypeField.STRING,
        },
    }
    DEFAULT_CONFIGURATION = [
        {"name": "ALGOLIA_API_KEY", "value": None},
        {"name": "ALGOLIA_LOCALES", "value": "EN,"},
        {"name": "ALGOLIA_INDEX_PREFIX", "value": None},
        {"name": "ALGOLIA_APPLICATION_ID", "value": None},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = UserAdminContext()
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = {
            "ALGOLIA_API_KEY": configuration["ALGOLIA_API_KEY"],
            "ALGOLIA_LOCALES": configuration["ALGOLIA_LOCALES"],
            "ALGOLIA_INDEX_PREFIX": configuration["ALGOLIA_INDEX_PREFIX"],
            "ALGOLIA_APPLICATION_ID": configuration["ALGOLIA_APPLICATION_ID"],
        }

    def get_locales(self):
        """Return OTO plugin locales."""
        return self.config["ALGOLIA_LOCALES"].split(",")

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""

        missing_fields = []
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if not configuration["ALGOLIA_API_KEY"]:
            missing_fields.append("ALGOLIA_API_KEY")
        if not configuration["ALGOLIA_APPLICATION_ID"]:
            missing_fields.append("ALGOLIA_APPLICATION_ID")

        if plugin_configuration.active and missing_fields:
            error_msg = (
                "To enable a plugin, you need to provide values for the "
                "following fields: "
            )
            raise ValidationError(
                {
                    missing_fields[0]: ValidationError(
                        error_msg + ", ".join(missing_fields), code="invalid"
                    )
                }
            )

    @staticmethod
    def get_product_global_id(product: "Product"):
        return graphene.Node.to_global_id("Product", product.id)

    @require_active_plugin
    def product_created(self, product: "Product", previous_value: Any):
        """Index product to Algolia."""
        index_product_data_to_algolia.delay(
            config=self.config,
            sender="product_created",
            locales=self.get_locales(),
            product_global_id=self.get_product_global_id(product=product),
        )

    @require_active_plugin
    def product_updated(self, product: "Product", previous_value: Any) -> Any:
        """Index product to Algolia."""
        index_product_data_to_algolia.delay(
            config=self.config,
            sender="product_updated",
            locales=self.get_locales(),
            product_global_id=self.get_product_global_id(product=product),
        )

    @require_active_plugin
    def product_deleted(
        self, product: "Product", variants: List[int], previous_value: Any
    ) -> Any:
        """Delete product from Algolia."""
        index_product_data_to_algolia.delay(
            config=self.config,
            sender="product_deleted",
            locales=self.get_locales(),
            product_global_id=self.get_product_global_id(product=product),
        )
