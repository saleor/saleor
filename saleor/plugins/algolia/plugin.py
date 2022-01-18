import logging
from typing import Any, List

from django.core.exceptions import ValidationError

from ...graphql.core.enums import PluginErrorCode
from ...payment.gateways.utils import require_active_plugin
from ...product.models import Product
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..models import PluginConfiguration
from .client import AlgoliaApiClient
from .utils import UserAdminContext, get_product_data

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
        "ALGOLIA_LOCALES": {
            "label": "Algolia Locales",
            "help_text": "Algolia Locales",
            "type": ConfigurationTypeField.STRING,
        },
    }
    DEFAULT_CONFIGURATION = [
        {"name": "ALGOLIA_API_KEY", "value": None},
        {"name": "ALGOLIA_LOCALES", "value": "en,ar"},
        {"name": "ALGOLIA_APPLICATION_ID", "value": None},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = UserAdminContext()
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = {
            "ALGOLIA_API_KEY": configuration["ALGOLIA_API_KEY"],
            "ALGOLIA_LOCALES": configuration["ALGOLIA_LOCALES"],
            "ALGOLIA_APPLICATION_ID": configuration["ALGOLIA_APPLICATION_ID"],
        }

    def get_client(self):
        """Return Algolia client."""
        return AlgoliaApiClient(
            api_key=self.config["ALGOLIA_API_KEY"],
            app_id=self.config["ALGOLIA_APPLICATION_ID"],
            locales=self.config["ALGOLIA_LOCALES"].split(","),
        )

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""

        missing_fields = []
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if not configuration.get("ALGOLIA_API_KEY"):
            missing_fields.append("ALGOLIA_API_KEY")
        if not configuration.get("ALGOLIA_APPLICATION_ID"):
            missing_fields.append("ALGOLIA_APPLICATION_ID")

        if plugin_configuration.active and missing_fields:
            error_msg = (
                "To enable a plugin, you need to provide values for the "
                "following fields: {}"
            )
            raise ValidationError(
                {
                    f"{field}": ValidationError(
                        error_msg.format(field),
                        code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                    )
                    for field in missing_fields
                },
            )

    @require_active_plugin
    def product_created(self, product: "Product", previous_value: Any):
        """Index product to Algolia."""
        for locale, index in self.get_client().list_indexes().items():
            product_data = get_product_data(
                product_pk=product.pk,
                language_code=locale.upper(),
            )
            if product_data:
                index.save_object(
                    obj=product_data,
                    request_options={"autoGenerateObjectIDIfNotExist": False},
                )
                logger.info("Product %s indexed to Algolia", product.slug)

    @require_active_plugin
    def product_updated(self, product: "Product", previous_value: Any) -> Any:
        """Index product to Algolia."""
        for locale, index in self.get_client().list_indexes().items():
            product_data = get_product_data(
                product_pk=product.pk,
                language_code=locale.upper(),
            )
            if product_data:
                index.partial_update_object(
                    obj=product_data, request_options={"createIfNotExists": True}
                )
                logger.info("Product %s updated in Algolia", product.slug)

    @require_active_plugin
    def product_deleted(
        self, product: "Product", variants: List[int], previous_value: Any
    ) -> Any:
        """Delete product from Algolia."""
        for locale, index in self.get_client().list_indexes().items():
            index.delete_object(object_id=product.slug)
            logger.info("Product %s deleted from Algolia", product.slug)
