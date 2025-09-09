import graphene

from .....account import models
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ....directives import doc, webhook_events
from ....plugins.dataloaders import get_plugin_manager_promise
from ..base import CustomerDeleteMixin
from .base import UserDelete


@doc(category=DOC_CATEGORY_USERS)
@webhook_events(async_events={WebhookEventAsyncType.CUSTOMER_DELETED})
class CustomerDelete(CustomerDeleteMixin, UserDelete):
    """Deletes a customer."""

    class Meta:
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    class Arguments:
        id = graphene.ID(required=False, description="ID of a customer to delete.")
        external_reference = graphene.String(
            required=False,
            description="External ID of a customer to update.",
        )

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        results = super().perform_mutation(root, info, **data)
        cls.post_process(info)
        return results

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_deleted, instance)
