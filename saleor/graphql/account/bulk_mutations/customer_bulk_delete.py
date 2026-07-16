import graphene
from django.conf import settings

from ....account import models
from ....core.tracing import traced_atomic_transaction
from ....giftcard.utils import deactivate_assigned_gift_cards
from ....permission.enums import AccountPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
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
            graphene.ID,
            required=True,
            description=(
                f"List of user IDs to delete. The number of items is limited to {settings.BULK_DELETE_LIMIT} by default. "
                "Exceeding the limit returns an `INVALID` error."
            ),
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
        max_input_size = settings.BULK_DELETE_LIMIT

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        count, errors = super().perform_mutation(root, info, **data)
        cls.post_process(info, count)
        return count, errors

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        instances = list(queryset)
        with traced_atomic_transaction():
            # Required before deleting the users: GiftCard.assigned_to is
            # on_delete=PROTECT, so restricted cards must be detached and
            # deactivated first, atomically with the deletion.
            deactivate_assigned_gift_cards(queryset)
            queryset.delete()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.CUSTOMER_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for instance in instances:
            cls.call_event(manager.customer_deleted, instance, webhooks=webhooks)
