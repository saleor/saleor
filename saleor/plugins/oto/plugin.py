import logging
from typing import Any

from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound

from ...graphql.core.enums import PluginErrorCode
from ...order.models import Fulfillment, Order
from ...payment.gateways.utils import require_active_plugin
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..models import PluginConfiguration
from .client import OTOApiClient
from .constants import PLUGIN_ID
from .utils import generate_create_order_data, handle_webhook

logger = logging.getLogger(__name__)


class OTOPlugin(BasePlugin):
    PLUGIN_NAME = "OTO"
    PLUGIN_ID = PLUGIN_ID
    DEFAULT_ACTIVE = False
    CONFIGURATION_PER_CHANNEL = False
    PLUGIN_DESCRIPTION = "Plugin responsible for ship orders using OTO."

    CONFIG_STRUCTURE = {
        "REFRESH_TOKEN": {
            "label": "Refresh Token",
            "help_text": "Refresh Token",
            "type": ConfigurationTypeField.SECRET,
        },
        "ACCESS_TOKEN": {
            "label": "Access Token",
            "help_text": "Access Token",
            "type": ConfigurationTypeField.SECRET,
        },
        "PUBLIC_KEY_FOR_SIGNATURE": {
            "label": "Public Key for Signature",
            "help_text": "The public key for signature",
            "type": ConfigurationTypeField.SECRET,
        },
    }
    DEFAULT_CONFIGURATION = [
        {"name": "ACCESS_TOKEN", "value": None},
        {"name": "REFRESH_TOKEN", "value": None},
        {"name": "PUBLIC_KEY_FOR_SIGNATURE", "value": None},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = {item["name"]: item["value"] for item in self.configuration}

    def get_client(self):
        return OTOApiClient(
            access_token=self.config["ACCESS_TOKEN"],
        )

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""

        missing_fields = []
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if not configuration["ACCESS_TOKEN"]:
            missing_fields.append("ACCESS_TOKEN")

        if not configuration["REFRESH_TOKEN"]:
            missing_fields.append("REFRESH_TOKEN")

        if not configuration["PUBLIC_KEY_FOR_SIGNATURE"]:
            missing_fields.append("PUBLIC_KEY_FOR_SIGNATURE")

        if plugin_configuration.active and missing_fields:
            error_msg = (
                "To enable a plugin, you need to provide values for the "
                "following fields: "
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

    @staticmethod
    def get_oto_order_id(fulfillment: Fulfillment) -> str:
        return str(f"#{fulfillment.composed_id}")

    @require_active_plugin
    def fulfillment_created(
        self, fulfillment: "Fulfillment", previous_value: Any
    ) -> Any:
        # Create an OTO order.
        order_data = generate_create_order_data(fulfillment=fulfillment)
        response = self.get_client().create_order(order_data=order_data)
        if response.get("success") is True:
            fulfillment_ids = fulfillment.order.get_value_from_private_metadata(
                "oto_fulfillment_ids", []
            )
            fulfillment_ids.extend([self.get_oto_order_id(fulfillment=fulfillment)])
            fulfillment.order.store_value_in_private_metadata(
                items=dict(oto_fulfillment_ids=fulfillment_ids)
            )
            fulfillment.order.save(update_fields=["private_metadata"])
            logger.info(
                msg=f"OTO order {response.get('otoId')} created",
                extra={"order_id": fulfillment.order.id},
            )
        else:
            msg = (
                response.get("errorMsg").capitalize()
                if response.get("errorMsg")
                else f"Can not create an OTO order because {response.get('errorMsg')}"
            )
            logger.error(msg=msg, extra={"order_id": fulfillment.order.id})
            raise ValidationError({"oto_id": ValidationError(msg, code="invalid")})

    @require_active_plugin
    def fulfillment_canceled(
        self, fulfillment: "Fulfillment", previous_value: Any
    ) -> Any:
        # Cancel an OTO order.
        order_data = dict(
            orderId=self.get_oto_order_id(fulfillment=fulfillment),
        )
        response = self.get_client().cancel_order(order_data=order_data)
        if not response.get("success") is True:
            msg = (
                response.get("errorMsg").capitalize()
                if response.get("errorMsg")
                else "Can not cancel an OTO order {}".format(fulfillment.order.id)
            )
            raise ValidationError(
                {"order_id": ValidationError(msg, code="invalid")},
            )
        else:
            logger.info(
                msg=f"OTO order {fulfillment.composed_id} canceled",
                extra={"order_id": fulfillment.composed_id},
            )

    @require_active_plugin
    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        # In case order is returned, we need to return fulfillment on OTO.
        returned_fulfillment = order.fulfillments.last()
        if returned_fulfillment and returned_fulfillment.status in [
            "returned",
            "refunded_and_returned",
        ]:
            if returned_fulfillment:
                oto_fulfillment_ids = order.get_value_from_private_metadata(
                    "oto_fulfillment_ids", []
                )
                for oto_order_id in oto_fulfillment_ids:
                    order_data = {
                        "orderId": oto_order_id,
                    }
                    response = self.get_client().get_order_return_link(
                        order_data=order_data
                    )
                    if response.get("success") is True:
                        returned_fulfillment.store_value_in_private_metadata(
                            items=dict(oto_return_link=response.get("returnLink"))
                        )
                        returned_fulfillment.save(update_fields=["private_metadata"])
                        returned_fulfillment.order.store_value_in_private_metadata(
                            items=dict(oto_return_link=response.get("returnLink"))
                        )
                        returned_fulfillment.order.save(
                            update_fields=["private_metadata"]
                        )
                    else:
                        msg = (
                            response.get("errorMsg").capitalize()
                            if response.get("errorMsg")
                            else "Can not create an OTO order"
                        )
                        raise ValidationError(
                            {"order_id": ValidationError(msg, code="invalid")},
                        )

    @require_active_plugin
    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        # Fired when a webhook is received from OTO. Example: OTO cancels an order.
        if path == "/track/" and request.method == "POST":
            response = handle_webhook(
                request=request,
                config=self.config,
            )
            logger.info(msg="Finish handling webhook from OTO!")
            return response
        else:
            logger.info(msg="Invalid webhook path from OTO!")
            return HttpResponseNotFound("This OTO path is not valid!")
