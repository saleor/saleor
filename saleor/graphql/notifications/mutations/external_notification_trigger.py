import json

import graphene

from saleor.account.models import User
from saleor.checkout.models import Checkout
from saleor.core.exceptions import PermissionDenied
from saleor.core.permissions import (
    CheckoutPermissions,
    OrderPermissions,
    ProductPermissions,
)
from saleor.graphql.core.types.common import ExternalNotificationError
from saleor.invoice.models import Invoice
from saleor.order.models import Fulfillment, Order
from saleor.product.models import Product, ProductVariant

from ....core.permissions import AccountPermissions
from ....graphql.utils import resolve_global_ids_to_primary_keys
from ....webhook.payloads import (
    generate_checkout_payload,
    generate_customer_payload,
    generate_fulfillment_lines_payload,
    generate_invoice_payload,
    generate_order_payload,
    generate_product_payload,
    generate_product_variant_payload,
)
from ...core.mutations import BaseMutation
from ..inputs import ExternalNotificationTriggerInput


class ExternalNotificationTrigger(BaseMutation):
    PK__IN = "pk__in"
    PAYLOAD_MAPPING = {
        "Fulfillment": (
            Fulfillment,
            generate_fulfillment_lines_payload,
            None,
            PK__IN,
            OrderPermissions.MANAGE_ORDERS,
        ),
        "ProductVariant": (
            ProductVariant,
            generate_product_variant_payload,
            list,
            PK__IN,
            ProductPermissions.MANAGE_PRODUCTS,
        ),
        "Product": (
            Product,
            generate_product_payload,
            None,
            PK__IN,
            ProductPermissions.MANAGE_PRODUCTS,
        ),
        "User": (
            User,
            generate_customer_payload,
            None,
            PK__IN,
            AccountPermissions.MANAGE_USERS,
        ),
        "Checkout": (
            Checkout,
            generate_checkout_payload,
            None,
            "token__in",
            CheckoutPermissions.MANAGE_CHECKOUTS,
        ),
        "Invoice": (
            Invoice,
            generate_invoice_payload,
            None,
            PK__IN,
            OrderPermissions.MANAGE_ORDERS,
        ),
        "Order": (
            Order,
            generate_order_payload,
            None,
            PK__IN,
            OrderPermissions.MANAGE_ORDERS,
        ),
    }

    class Arguments:
        input = ExternalNotificationTriggerInput(
            required=True, description="Input for External Notification Trigger"
        )
        pluginId = graphene.String(description="The ID of notification plugin.")

    class Meta:
        description = "Send external notification to given customers."
        error_type_class = ExternalNotificationError

    @classmethod
    def perform_mutation(cls, root, info, **data):
        manager = info.context.plugins
        ids, extra_payloads, external_event_type = cls.get_cleaned_data(data)
        model_type, pks = resolve_global_ids_to_primary_keys(ids)
        if payload_params := cls.PAYLOAD_MAPPING.get(model_type):
            (
                model,
                payload_function,
                input_type,
                pk_lookup_type,
                permission_type,
            ) = payload_params
            if cls._is_user_contain_permission(info.context, permission_type):
                if input_type == list:
                    payload_input = model.objects.filter(**{pk_lookup_type: pks})
                    payloads = json.loads(payload_function(payload_input))
                    for payload in payloads:
                        payload.update(extra_payloads)
                        cls._notify(data, manager, external_event_type, payload)
                else:
                    payload_inputs = model.objects.filter(**{pk_lookup_type: pks})
                    for payload_input in payload_inputs:
                        payload = json.loads(payload_function(payload_input))
                        payload = payload[0] if type(payload) == list else payload
                        payload.update(extra_payloads)
                        cls._notify(data, manager, external_event_type, payload)
        return cls()

    @classmethod
    def _is_user_contain_permission(cls, context, permission_type):
        if cls.check_permissions(context, (permission_type,)):
            return True
        raise PermissionDenied()

    @classmethod
    def _notify(cls, data, manager, external_event_type, payload):
        if plugin_id := data.get("pluginId"):
            manager.notify_in_single_plugin(plugin_id, external_event_type, payload)
        else:
            manager.notify(event=external_event_type, payload=payload)

    @classmethod
    def get_cleaned_data(cls, data):
        if data_input := data.get("input"):
            return data_input.values()
