import json
import logging
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse

from ...order.models import Fulfillment, Order
from ...payment.gateways.utils import require_active_plugin
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..models import PluginConfiguration
from . import constants
from .utils import send_oto_request

logger = logging.getLogger(__name__)


class OTOPlugin(BasePlugin):
    PLUGIN_NAME = "OTO"
    DEFAULT_ACTIVE = False
    PLUGIN_ID = constants.PLUGIN_ID
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
    }
    DEFAULT_CONFIGURATION = [
        {"name": "ACCESS_TOKEN", "value": None},
        {"name": "REFRESH_TOKEN", "value": None},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}

        self.config = {
            "ACCESS_TOKEN": configuration["ACCESS_TOKEN"],
            "REFRESH_TOKEN": configuration["REFRESH_TOKEN"],
        }

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

    @require_active_plugin
    def fulfillment_created(
        self, fulfillment: "Fulfillment", previous_value: Any
    ) -> Any:
        # Create an OTO order.
        response = send_oto_request(fulfillment, self.config, "createOrder")
        if response.get("success") is True:
            fulfillment.store_value_in_private_metadata(
                items=dict(oto_id=response.get("otoId"))
            )
            fulfillment.save(update_fields=["private_metadata"])
        else:
            msg = (
                response.get("errorMsg").capitalize()
                if response.get("errorMsg")
                else "Can not create an OTO order"
            )
            raise ValidationError(
                {"oto_id": ValidationError(msg, code="invalid")},
            )

    @require_active_plugin
    def fulfillment_canceled(
        self, fulfillment: "Fulfillment", previous_value: Any
    ) -> Any:
        # Cancel an OTO order.
        response = send_oto_request(fulfillment, self.config, "cancelOrder")
        if not response.get("success") is True:
            msg = (
                response.get("errorMsg").capitalize()
                if response.get("errorMsg")
                else "Can not cancel an OTO order {}".format(fulfillment.order.id)
            )
            raise ValidationError(
                {"order_id": ValidationError(msg, code="invalid")},
            )

    @require_active_plugin
    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        pass

    @require_active_plugin
    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        # In case order is cancelled, we need to cancel fulfillment on OTO.
        last_order_fulfillment = order.fulfillments.last()
        if last_order_fulfillment and last_order_fulfillment.status in [
            "returned",
            "refunded_and_returned",
        ]:
            # Create OTO return shipment.
            pass

    @staticmethod
    def check_oto_signature(data: Dict[str, Any]) -> bool:
        """Check OTO signature."""
        signature = data.pop("signature").decode("utf-8")
        string_to_sign = f"{data['otoId']}:{data['status']}:{data['timestamp']}"
        return signature == string_to_sign

    @require_active_plugin
    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        # Fired when a webhook is received from OTO. Example: OTO cancels an order.
        data = json.loads(request.body)
        # Check signatures and headers.
        if not self.check_oto_signature(data):
            if path == "/webhook/orders":
                fulfillment = Fulfillment.objects.filter(pk=data["orderId"]).first()
                if fulfillment:
                    fulfillment.tracking_number = data["trackingNumber"]
                    fulfillment.store_value_in_private_metadata(
                        items={
                            "otoStatus": data["status"],
                            "printAWBURL": data["printAWBURL"],
                            "shippingCompanyStatus": data["dcStatus"],
                        }
                    )
                    fulfillment.save(
                        update_fields=["tracking_number", "private_metadata"]
                    )
        return HttpResponse("OK")
