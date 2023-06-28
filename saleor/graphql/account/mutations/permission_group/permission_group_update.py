from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple, cast

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import PermissionGroupErrorCode
from .....account.models import User
from .....channel.models import Channel
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import AccountPermissions, get_permissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.utils import (
    can_user_manage_group_channels,
    can_user_manage_group_permissions,
    get_not_manageable_permissions_after_removing_perms_from_group,
    get_not_manageable_permissions_after_removing_users_from_group,
    get_out_of_scope_users,
)
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_314, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import PermissionEnum
from ....core.types import NonNullList, PermissionGroupError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....utils.validators import check_for_duplicates
from ...dataloaders import AccessibleChannelsByGroupIdLoader
from ...types import Group
from .permission_group_create import PermissionGroupCreate, PermissionGroupInput


class PermissionGroupUpdateInput(PermissionGroupInput):
    name = graphene.String(description="Group name.", required=False)
    remove_permissions = NonNullList(
        PermissionEnum,
        description="List of permission code names to unassign from this group.",
        required=False,
    )
    remove_users = NonNullList(
        graphene.ID,
        description="List of users to unassign from this group.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels to unassign from this group."
        + ADDED_IN_314
        + PREVIEW_FEATURE,
    )
    restricted_access_to_channels = graphene.Boolean(
        description="Determine if the group has restricted access to channels."
        + ADDED_IN_314
        + PREVIEW_FEATURE,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class PermissionGroupUpdate(PermissionGroupCreate):
    class Arguments:
        id = graphene.ID(description="ID of the group to update.", required=True)
        input = PermissionGroupUpdateInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = (
            "Update permission group. Apps are not allowed to perform this mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.Group
        object_type = Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PERMISSION_GROUP_UPDATED,
            )
        ]

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            if remove_users := cleaned_data.get("remove_users"):
                instance.user_set.remove(*remove_users)
            if remove_permissions := cleaned_data.get("remove_permissions"):
                instance.permissions.remove(*remove_permissions)
            if remove_channels := cleaned_data.get("remove_channels"):
                instance.channels.remove(*remove_channels)
        # Invalidate dataloader for group channels
        AccessibleChannelsByGroupIdLoader(info.context).clear(instance.id)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.permission_group_updated, instance)

    @classmethod
    def clean_input(
        cls,
        info,
        instance,
        data,
    ):
        requestor = info.context.user
        cls.ensure_requestor_can_manage_group(info, requestor, instance)

        errors: DefaultDict[str, List[ValidationError]] = defaultdict(list)
        permission_fields = ("add_permissions", "remove_permissions", "permissions")
        user_fields = ("add_users", "remove_users", "users")
        channel_fields = ("add_channels", "remove_channels", "channels")

        cls.check_duplicates(errors, data, permission_fields)
        cls.check_duplicates(errors, data, user_fields)
        cls.check_duplicates(errors, data, channel_fields)

        if errors:
            raise ValidationError(errors)

        cleaned_input = super().clean_input(info, instance, data)

        return cleaned_input

    @classmethod
    def ensure_requestor_can_manage_group(
        cls, info: ResolveInfo, requestor: "User", group: models.Group
    ):
        """Check if requestor can manage group.

        Requestor cannot manage group with wider scope of permissions or channels.
        """
        if requestor.is_superuser:
            return
        if not can_user_manage_group_permissions(requestor, group):
            error_msg = "You can't manage group with permissions out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            raise ValidationError(error_msg, code)
        if not can_user_manage_group_channels(info, requestor, group):
            error_msg = "You can't manage group with channels out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.value
            raise ValidationError(error_msg, code)

    @classmethod
    def clean_channels(
        cls,
        info: ResolveInfo,
        group: models.Group,
        user_accessible_channels: List["Channel"],
        errors: dict,
        cleaned_input: dict,
    ):
        """Clean channels when the group hasn't restricted access to channels."""
        super().clean_channels(
            info, group, user_accessible_channels, errors, cleaned_input
        )
        if remove_channels := cleaned_input.get("remove_channels"):
            user = info.context.user
            user = cast(User, user)
            cls.ensure_can_manage_channels(
                user, user_accessible_channels, errors, remove_channels
            )

        restricted_access = cleaned_input.get("restricted_access_to_channels")
        if restricted_access is False or (
            restricted_access is None and group.restricted_access_to_channels is False
        ):
            cleaned_input["add_channels"] = []
            cleaned_input["remove_channels"] = []

    @classmethod
    def clean_permissions(
        cls,
        requestor: "User",
        group: models.Group,
        errors: Dict[str, List[ValidationError]],
        cleaned_input: dict,
    ):
        super().clean_permissions(requestor, group, errors, cleaned_input)
        field = "remove_permissions"
        permission_items = cleaned_input.get(field)
        if permission_items:
            cleaned_input[field] = get_permissions(permission_items)
            if not requestor.is_superuser:
                cls.ensure_can_manage_permissions(
                    requestor, errors, field, permission_items
                )
                cls.ensure_permissions_can_be_removed(errors, group, permission_items)

    @classmethod
    def ensure_permissions_can_be_removed(
        cls,
        errors: dict,
        group: models.Group,
        permissions: List["str"],
    ):
        missing_perms = get_not_manageable_permissions_after_removing_perms_from_group(
            group, permissions
        )
        if missing_perms:
            # add error
            permission_codes = [PermissionEnum.get(code) for code in permissions]
            msg = (
                "Permissions cannot be removed, "
                "some of permissions will not be manageable."
            )
            code = PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permission_codes}
            cls.update_errors(errors, msg, "remove_permissions", code, params)

    @classmethod
    def clean_users(
        cls,
        requestor: "User",
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        super().clean_users(requestor, errors, cleaned_input, group)
        remove_users = cleaned_input.get("remove_users")
        if remove_users:
            cls.ensure_can_manage_users(
                requestor, errors, "remove_users", cleaned_input
            )
            cls.clean_remove_users(requestor, errors, cleaned_input, group)

    @classmethod
    def ensure_can_manage_users(
        cls,
        requestor: "User",
        errors: Dict[str, List[ValidationError]],
        field: str,
        cleaned_input: dict,
    ):
        """Check if requestor can manage users from input.

        Requestor cannot manage users with wider scope of permissions.
        """
        if requestor.is_superuser:
            return
        users = cleaned_input[field]
        out_of_scope_users = get_out_of_scope_users(requestor, users)
        if out_of_scope_users:
            # add error
            ids = [
                graphene.Node.to_global_id("User", user_instance.pk)
                for user_instance in out_of_scope_users
            ]
            error_msg = "You can't manage these users."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_USER.value
            params = {"users": ids}
            cls.update_errors(errors, error_msg, field, code, params)

    @classmethod
    def clean_remove_users(
        cls,
        requestor: "User",
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        cls.check_if_removing_user_last_group(requestor, errors, cleaned_input)
        cls.check_if_users_can_be_removed(requestor, errors, cleaned_input, group)

    @classmethod
    def check_if_removing_user_last_group(
        cls, requestor: "User", errors: dict, cleaned_input: dict
    ):
        """Ensure user doesn't remove user's last group."""
        remove_users = cleaned_input["remove_users"]
        if requestor in remove_users and requestor.groups.count() == 1:
            # add error
            error_msg = "You cannot remove yourself from your last group."
            code = PermissionGroupErrorCode.CANNOT_REMOVE_FROM_LAST_GROUP.value
            params = {"users": [graphene.Node.to_global_id("User", requestor.pk)]}
            cls.update_errors(errors, error_msg, "remove_users", code, params)

    @classmethod
    def check_if_users_can_be_removed(
        cls,
        requestor: "User",
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        """Check if after removing users from group all permissions will be manageable.

        After removing users from group, for each permission, there should be
        at least one staff member who can manage it (has both “manage staff”
        and this permission).
        """
        if requestor.is_superuser:
            return

        remove_users = cleaned_input["remove_users"]
        add_users = cleaned_input.get("add_users")
        manage_staff_permission = AccountPermissions.MANAGE_STAFF.value

        # check if user with manage staff will be added to the group
        if add_users:
            if any([user.has_perm(manage_staff_permission) for user in add_users]):
                return True

        permissions = get_not_manageable_permissions_after_removing_users_from_group(
            group, remove_users
        )
        if permissions:
            # add error
            permission_codes = [PermissionEnum.get(code) for code in permissions]
            msg = "Users cannot be removed, some of permissions will not be manageable."
            code = PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permission_codes}
            cls.update_errors(errors, msg, "remove_users", code, params)

    @classmethod
    def check_duplicates(
        cls,
        errors: dict,
        input_data: dict,
        fields: Tuple[str, str, str],
    ):
        """Check if any items are on both input field.

        Raise error if some of items are duplicated.
        """
        error = check_for_duplicates(input_data, *fields)
        if error:
            error.code = PermissionGroupErrorCode.DUPLICATED_INPUT_ITEM.value
            error_field = fields[2]
            errors[error_field].append(error)
