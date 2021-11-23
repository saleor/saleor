import logging
from typing import Any, List

import graphene
from algoliasearch.search_client import SearchClient
from django.core.exceptions import ValidationError

from ...product.models import Product
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..models import PluginConfiguration
from . import constants
from .utils import UserAdminContext, get_product_data

logger = logging.getLogger(__name__)


class AlgoliaPlugin(BasePlugin):
    DEFAULT_ACTIVE = False
    PLUGIN_NAME = "Algolia"
    PLUGIN_ID = constants.PLUGIN_ID
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
        self.algolia_indices = {}
        self.context = UserAdminContext()
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = {
            "ALGOLIA_API_KEY": configuration["ALGOLIA_API_KEY"],
            "ALGOLIA_LOCALES": configuration["ALGOLIA_LOCALES"],
            "ALGOLIA_INDEX_PREFIX": configuration["ALGOLIA_INDEX_PREFIX"],
            "ALGOLIA_APPLICATION_ID": configuration["ALGOLIA_APPLICATION_ID"],
        }
        self.client = SearchClient.create(
            api_key=self.config["ALGOLIA_API_KEY"],
            app_id=self.config["ALGOLIA_APPLICATION_ID"],
        )

        self.algolia_index_prefix = self.config["ALGOLIA_INDEX_PREFIX"]
        for locale in self.get_locales():
            index = self.client.init_index(
                name=f"{self.algolia_index_prefix}_products_{locale}"
            )
            self.algolia_indices.update({locale: index})

            index.set_settings(
                settings={
                    "searchableAttributes": [
                        "sku",
                        "name",
                        "channels",
                        "description",
                        "translation",
                    ]
                }
            )

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

    def product_created(self, product: "Product", previous_value: Any):
        """Index product to Algolia."""
        return
        for locale in self.get_locales():
            product_data = get_product_data(product=product, locale=locale)
            if product_data:
                self.algolia_indices.get(locale).save_object(
                    obj=product_data,
                    request_options={"autoGenerateObjectIDIfNotExist": False},
                )

    def product_updated(self, product: "Product", previous_value: Any) -> Any:
        """Index product to Algolia."""
        for locale in self.get_locales():
            product_data = get_product_data(product=product, locale=locale)
            if product_data:
                self.algolia_indices.get(locale).partial_update_object(
                    obj=product_data, request_options={"createIfNotExists": True}
                )

    def product_deleted(
        self, product: "Product", variants: List[int], previous_value: Any
    ) -> Any:
        """Delete product from Algolia."""
        object_id = graphene.Node.to_global_id("Product", product.pk)
        for locale in self.get_locales():
            self.algolia_indices.get(locale).delete_object(object_id=object_id)
