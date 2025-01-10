import graphene

from ....checkout.actions import call_checkout_event
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_321
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout


class CheckoutCustomerNoteUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID.",
            required=True,
        )
        customer_note = graphene.String(
            required=True, description="New customer note content."
        )

    class Meta:
        description = (
            "Updates customer note in the existing checkout object." + ADDED_IN_321
        )
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        customer_note,
        id=None,
    ):
        checkout = cls.get_node_or_error(info, id, only_type=Checkout)
        checkout.note = customer_note
        cls.clean_instance(info, checkout)
        checkout.save(update_fields=["note", "last_change"])
        manager = get_plugin_manager_promise(info.context).get()
        call_checkout_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout=checkout,
        )
        return CheckoutCustomerNoteUpdate(checkout=checkout)
