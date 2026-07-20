from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ValidationError

from ....account import models
from ....core.tracing import traced_atomic_transaction
from ....giftcard.utils import deactivate_assigned_gift_cards
from ....permission.enums import AccountPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_USERS
from ...core.types import StaffError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations.base import StaffDeleteMixin
from ..types import User
from .customer_bulk_delete import UserBulkDelete


class StaffBulkDelete(StaffDeleteMixin, UserBulkDelete):
    class Meta:
        description = (
            "Deletes staff users. Apps are not allowed to perform this mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.STAFF_DELETED,
                description="A staff account was deleted.",
            ),
        ]
        max_input_size = settings.BULK_DELETE_LIMIT

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, ids, **data
    ):
        if size_error := cls.validate_input_size(ids):
            return 0, size_error

        instances = cls.get_nodes_or_error(ids, "id", User)
        errors = cls.clean_instances(info, instances)
        count = len(instances)
        if not errors and count:
            clean_instance_ids = [instance.pk for instance in instances]
            qs = models.User.objects.filter(pk__in=clean_instance_ids, is_staff=True)
            cls.bulk_action(info, qs, **data)
        else:
            count = 0
        return count, errors

    @classmethod
    def clean_instances(cls, info: ResolveInfo, users):
        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)

        requestor = info.context.user
        cls.check_if_users_can_be_deleted(info, users, "ids", errors)
        cls.check_if_requestor_can_manage_users(requestor, users, "ids", errors)
        cls.check_if_removing_left_not_manageable_permissions(
            requestor, users, "ids", errors
        )
        return ValidationError(errors) if errors else {}

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        instances = list(queryset)
        with traced_atomic_transaction():
            # Required before deleting the users: GiftCard.assigned_to is
            # on_delete=PROTECT, so restricted cards must be detached and
            # deactivated first, atomically with the deletion.
            deactivate_assigned_gift_cards(queryset)
            queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.STAFF_DELETED)
        for instance in instances:
            cls.call_event(manager.staff_deleted, instance, webhooks=webhooks)
