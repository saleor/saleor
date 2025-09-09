from collections import defaultdict

from django.core.exceptions import ValidationError

from ....account import models
from ....permission.enums import AccountPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_USERS
from ...core.types import StaffError
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations.base import StaffDeleteMixin
from ..types import User
from .customer_bulk_delete import UserBulkDelete


@doc(category=DOC_CATEGORY_USERS)
@webhook_events(async_events={WebhookEventAsyncType.STAFF_DELETED})
class StaffBulkDelete(StaffDeleteMixin, UserBulkDelete):
    """Deletes staff users. Apps are not allowed to perform this mutation."""

    class Meta:
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, ids, **data
    ):
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
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.STAFF_DELETED)
        for instance in instances:
            cls.call_event(manager.staff_deleted, instance, webhooks=webhooks)
