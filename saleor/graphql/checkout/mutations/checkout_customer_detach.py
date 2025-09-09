import graphene

from ....checkout.actions import call_checkout_event
from ....core.exceptions import PermissionDenied
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AccountPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context
from ..types import Checkout
from .utils import get_checkout


@doc(category=DOC_CATEGORY_CHECKOUT)
@webhook_events(async_events={WebhookEventAsyncType.CHECKOUT_UPDATED})
class CheckoutCustomerDetach(BaseMutation):
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

    class Meta:
        description = "Removes the user assigned as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        permissions = (
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_USER,
        )

    @classmethod
    def perform_mutation(
        cls, _root, info: ResolveInfo, /, checkout_id=None, token=None, id=None
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)
        requestor = get_user_or_app_from_context(info.context)
        if not requestor or not requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
            # Raise error if the current user doesn't own the checkout of the given ID.
            if checkout.user and checkout.user != info.context.user:
                raise PermissionDenied(
                    permissions=[AccountPermissions.IMPERSONATE_USER]
                )

        checkout.user = None
        checkout.save(update_fields=["user", "last_change"])
        manager = get_plugin_manager_promise(info.context).get()

        call_checkout_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout=checkout,
        )
        return CheckoutCustomerDetach(checkout=SyncWebhookControlContext(node=checkout))
