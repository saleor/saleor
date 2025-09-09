import graphene
from django.core.exceptions import ValidationError

from ....checkout.actions import call_checkout_event
from ....checkout.error_codes import CheckoutErrorCode
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout
from .utils import get_checkout


@doc(category=DOC_CATEGORY_CHECKOUT)
@webhook_events(async_events={WebhookEventAsyncType.CHECKOUT_UPDATED})
class CheckoutEmailUpdate(BaseMutation):
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
        email = graphene.String(required=True, description="email.")

    class Meta:
        description = "Updates email address in the existing checkout object."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @staticmethod
    def clean_email(email):
        if not email:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "This field cannot be blank.",
                        code=CheckoutErrorCode.REQUIRED.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        checkout_id=None,
        email,
        id=None,
        token=None,
    ):
        cls.clean_email(email)

        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        checkout.email = email
        cls.clean_instance(info, checkout)
        checkout.save(update_fields=["email", "last_change"])
        manager = get_plugin_manager_promise(info.context).get()
        call_checkout_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout=checkout,
        )
        return CheckoutEmailUpdate(checkout=SyncWebhookControlContext(node=checkout))
