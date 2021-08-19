import json

from ...account.models import User
from ...core.permissions import AccountPermissions
from ...core.permissions import OrderPermissions, ProductPermissions
from ...order.models import Order
from ...product.models import ProductVariant
from ...webhook.payloads import (
    generate_customer_payload,
    generate_order_payload,
    generate_product_variant_payload,
)

PAYLOAD_MAPPING = {
    "ProductVariant": (
        ProductVariant,
        generate_product_variant_payload,
        list,
        ProductPermissions.MANAGE_PRODUCTS,
    ),
    "User": (
        User,
        generate_customer_payload,
        None,
        AccountPermissions.MANAGE_USERS,
    ),
    "Order": (
        Order,
        generate_order_payload,
        None,
        OrderPermissions.MANAGE_ORDERS,
    ),
}


def get_payload_params(model_type):
    if payload_params := PAYLOAD_MAPPING.get(model_type):
        return payload_params


def send_notification(manager, external_event_type, payloads, plugin_id=None):
    if isinstance(payloads, list):
        for payload in payloads:
            trigger_notifications(manager, external_event_type, payload, plugin_id)
    else:
        trigger_notifications(manager, external_event_type, payloads, plugin_id)


def trigger_notifications(manager, external_event_type, payload, plugin_id=None):
    if plugin_id:
        manager.notify_in_single_plugin(plugin_id, external_event_type, payload)
    else:
        manager.notify(event=external_event_type, payload=payload)


class ExternalNotificationTriggerPayload:
    def __init__(self, model, payload_function, input_type=None):
        self.model = model
        self.payload_function = payload_function
        self.input_type = input_type

    def as_dict(self, pks, extra_payload):
        if self.input_type == list:
            return self._get_payload_for_list_input_type(pks, extra_payload)
        return self._get_default_payload(pks, extra_payload)

    def _get_payload_for_list_input_type(self, pks, extra_payload):
        payload_input = self.model.objects.filter(pk__in=pks)
        payloads = json.loads(self.payload_function(payload_input))

        for payload in payloads:
            payload.update({"extra_payload": extra_payload})
        return payloads

    def _get_default_payload(self, pks, extra_payload):
        payload_inputs = self.model.objects.filter(pk__in=pks)
        return [
            self._get_extracted_payload_input(payload_input, extra_payload)
            for payload_input in payload_inputs
        ]

    def _get_extracted_payload_input(self, payload_input, extra_payload):
        payload = json.loads(self.payload_function(payload_input))
        payload = payload[0] if type(payload) == list else payload
        payload.update({"extra_payload": extra_payload})
        return payload
