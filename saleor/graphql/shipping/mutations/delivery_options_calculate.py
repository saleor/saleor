import graphene

from ....checkout.delivery_context import fetch_shipping_methods_for_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....webhook.event_types import WebhookEventSyncType
from ...checkout import types as checkout_types
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_SHIPPING
from ...core.mutations import BaseMutation
from ...core.types.common import DeliveryOptionsCalculateError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context


class DeliveryOptionsCalculate(BaseMutation):
    deliveries = NonNullList(
        checkout_types.Delivery,
        required=True,
        default_value=[],
        description="List of the available deliveries.",
    )

    class Arguments:
        id = graphene.ID(
            description="The ID of the checkout.",
            required=True,
        )

    class Meta:
        description = (
            "Calculates available delivery options for a checkout." + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_SHIPPING
        error_type_class = DeliveryOptionsCalculateError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description="Triggered to fetch external shipping methods.",
            ),
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                description="Triggered to filter shipping methods.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info, /, *, id):  # type: ignore[override]
        manager = get_plugin_manager_promise(info.context).get()
        requestor = get_user_or_app_from_context(info.context)
        checkout = cls.get_node_or_error(
            info=info, node_id=id, field="id", only_type=checkout_types.Checkout
        )
        checkout_lines, _ = fetch_checkout_lines(checkout=checkout)
        checkout_info = fetch_checkout_info(
            checkout=checkout,
            lines=checkout_lines,
            manager=manager,
        )
        return cls(
            deliveries=fetch_shipping_methods_for_checkout(
                checkout_info,
                requestor=requestor,
                # Using mutation means, that we use new approach for fetching
                # delivery. In new flow we never modify anything for assigned
                # delivery
                overwrite_assigned_delivery=False,
            )
        )
