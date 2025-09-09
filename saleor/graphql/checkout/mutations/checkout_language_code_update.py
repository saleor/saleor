import graphene

from saleor.checkout.actions import call_checkout_event
from saleor.webhook.event_types import WebhookEventAsyncType

from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.enums import LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout
from .utils import get_checkout


@doc(category=DOC_CATEGORY_CHECKOUT)
@webhook_events(async_events={WebhookEventAsyncType.CHECKOUT_UPDATED})
class CheckoutLanguageCodeUpdate(BaseMutation):
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
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="New language code."
        )

    class Meta:
        description = "Updates language code in the existing checkout."
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
        language_code,
        token=None,
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        checkout.language_code = language_code
        checkout.save(update_fields=["language_code", "last_change"])
        manager = get_plugin_manager_promise(info.context).get()
        call_checkout_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout=checkout,
        )
        return CheckoutLanguageCodeUpdate(
            checkout=SyncWebhookControlContext(node=checkout)
        )
