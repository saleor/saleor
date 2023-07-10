import graphene

from .....account import models
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_310
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ..base import CustomerDeleteMixin
from .base import UserDelete


class CustomerDelete(CustomerDeleteMixin, UserDelete):
    class Meta:
        description = "Deletes a customer."
        doc_category = DOC_CATEGORY_USERS
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_DELETED,
                description="A customer account was deleted.",
            )
        ]

    class Arguments:
        id = graphene.ID(required=False, description="ID of a customer to delete.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a customer to update. {ADDED_IN_310}",
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
