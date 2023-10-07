import graphene
from django.core.exceptions import ValidationError

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import invalidate_checkout_prices
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import resolve_global_ids_to_primary_keys
from ..types import Checkout
from .utils import get_checkout, update_checkout_shipping_method_if_invalid


class CheckoutLinesDelete(BaseMutation):
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
        lines_ids = NonNullList(
            graphene.ID,
            required=True,
            description="A list of checkout lines.",
        )

    class Meta:
        description = "Deletes checkout lines."
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            )
        ]

    @classmethod
    def validate_lines(cls, checkout, lines_to_delete):
        lines = checkout.lines.all()
        all_lines_ids = [str(line.id) for line in lines]
        invalid_line_ids = list()
        for line_to_delete in lines_to_delete:
            if line_to_delete not in all_lines_ids:
                line_to_delete = graphene.Node.to_global_id(
                    "CheckoutLine", line_to_delete
                )
                invalid_line_ids.append(line_to_delete)

        if invalid_line_ids:
            raise ValidationError(
                {
                    "line_id": ValidationError(
                        "Provided line_ids aren't part of checkout.",
                        params={"lines": invalid_line_ids},
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id=None, lines_ids, token=None
    ):
        checkout = get_checkout(cls, info, checkout_id=None, token=token, id=id)

        _, lines_to_delete = resolve_global_ids_to_primary_keys(
            lines_ids, graphene_type="CheckoutLine", raise_error=True
        )
        cls.validate_lines(checkout, lines_to_delete)
        checkout.lines.filter(id__in=lines_to_delete).delete()

        lines, _ = fetch_checkout_lines(checkout)

        manager = get_plugin_manager_promise(info.context).get()
        checkout_info = fetch_checkout_info(checkout, lines, manager)
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        invalidate_checkout_prices(checkout_info, lines, manager, save=True)
        cls.call_event(manager.checkout_updated, checkout)

        return CheckoutLinesDelete(checkout=checkout)
