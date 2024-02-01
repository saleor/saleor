import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import invalidate_checkout
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo, raise_validation_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout, CheckoutLine
from .utils import get_checkout, update_checkout_shipping_method_if_invalid


class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )
        line_id = graphene.ID(description="ID of the checkout line to delete.")

    class Meta:
        description = "Deletes a CheckoutLine."
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
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        invalidate_checkout(checkout_info, lines, manager, save=True)
        cls.call_event(manager.checkout_updated, checkout)

        return CheckoutLineDelete(checkout=checkout)
