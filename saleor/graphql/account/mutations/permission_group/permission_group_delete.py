import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import PermissionGroupErrorCode
from .....core.exceptions import PermissionDenied
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.utils import (
    can_user_manage_group_channels,
    can_user_manage_group_permissions,
    get_not_manageable_permissions_after_group_deleting,
)
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import PermissionEnum
from ....core.mutations import ModelDeleteMutation
from ....core.types import PermissionGroupError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Group


class PermissionGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the group to delete.", required=True)

    class Meta:
        description = (
            "Delete permission group. Apps are not allowed to perform this mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.Group
        object_type = Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PERMISSION_GROUP_DELETED,
            )
        ]

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.permission_group_deleted, instance)

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        requestor = info.context.user
        if not requestor:
            raise PermissionDenied("You must be authenticated to perform this action.")
        if requestor.is_superuser:
            return
        if not can_user_manage_group_permissions(requestor, instance):
            error_msg = "You can't manage group with permissions out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            raise ValidationError(error_msg, code)
        if not can_user_manage_group_channels(info, requestor, instance):
            error_msg = "You can't manage group with channels out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.value
            raise ValidationError(error_msg, code)

        cls.check_if_group_can_be_removed(requestor, instance)

    @classmethod
    def check_permissions(cls, context, permissions=None, **data):
        app = get_app_promise(context).get()
        if app:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    def check_if_group_can_be_removed(cls, requestor, group):
        cls.ensure_deleting_not_left_not_manageable_permissions(group)
        cls.ensure_not_removing_requestor_last_group(group, requestor)

    @classmethod
    def ensure_deleting_not_left_not_manageable_permissions(cls, group):
        """Return true if management of all permissions is provided by other groups.

        After removing group, for each permission, there should be at least one staff
        member who can manage it (has both “manage staff” and this permission).
        """
        permissions = get_not_manageable_permissions_after_group_deleting(group)
        if permissions:
            permission_codes = [PermissionEnum.get(code) for code in permissions]
            msg = "Group cannot be removed, some of permissions will not be manageable."
            code = PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permission_codes}
            raise ValidationError(
                {"id": ValidationError(message=msg, code=code, params=params)}
            )

    @classmethod
    def ensure_not_removing_requestor_last_group(cls, group, requestor):
        """Ensure user doesn't remove user's last group."""
        if requestor in group.user_set.all() and requestor.groups.count() == 1:
            msg = "You cannot delete your last group."
            code = PermissionGroupErrorCode.CANNOT_REMOVE_FROM_LAST_GROUP.value
            raise ValidationError({"id": ValidationError(message=msg, code=code)})
