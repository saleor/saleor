import graphene

from ....checkout.actions import call_checkout_info_event
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import invalidate_checkout
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import raise_validation_error
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout, CheckoutLine
from .utils import get_checkout, update_checkout_shipping_method_if_invalid


@doc(category=DOC_CATEGORY_CHECKOUT)
@webhook_events(async_events={WebhookEventAsyncType.CHECKOUT_UPDATED})
class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID.",
            required=False,
        )
        token = UUID(
            description="Checkout token.",
            deprecation_reason="Use `id` instead.",
            required=False,
        )
        checkout_id = graphene.ID(
            required=False,
            description="The ID of the checkout.",
            deprecation_reason="Use `id` instead.",
        )
        line_id = graphene.ID(description="ID of the checkout line to delete.")

    class Meta:
        description = "Deletes a CheckoutLine."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        checkout_id=None,
        id=None,
        line_id,
        token=None,
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        line = cls.get_node_or_error(
            info, line_id, only_type=CheckoutLine, field="line_id"
        )

        if line.is_gift:
            raise_validation_error(
                message="Checkout line marked as gift can't be deleted.",
                field="line_id",
                code=CheckoutErrorCode.NON_REMOVABLE_GIFT_LINE.value,
            )

        if line and line in checkout.lines.all():
            line.delete()

        manager = get_plugin_manager_promise(info.context).get()
        lines, _ = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(checkout, lines, manager)
        shipping_update_fields = update_checkout_shipping_method_if_invalid(
            checkout_info, lines
        )
        invalidate_update_fields = invalidate_checkout(
            checkout_info, lines, manager, save=False
        )
        checkout.save(update_fields=shipping_update_fields + invalidate_update_fields)
        call_checkout_info_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout_info=checkout_info,
            lines=lines,
        )

        return CheckoutLineDelete(checkout=SyncWebhookControlContext(node=checkout))
