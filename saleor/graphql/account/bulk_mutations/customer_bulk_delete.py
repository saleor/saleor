import graphene

from ....account import models
from ....permission.enums import AccountPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_USERS
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import AccountError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations.base import CustomerDeleteMixin
from ..types import User


class UserBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of user IDs to delete."
        )

    class Meta:
        abstract = True


class CustomerBulkDelete(CustomerDeleteMixin, UserBulkDelete):
    class Meta:
        description = "Deletes customers."
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

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        count, errors = super().perform_mutation(root, info, **data)
        cls.post_process(info, count)
        return count, errors

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        instances = list(queryset)
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for instance in instances:
            manager.customer_deleted(instance)
