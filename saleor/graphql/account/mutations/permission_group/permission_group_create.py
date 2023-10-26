from collections import defaultdict
from typing import cast

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import PermissionGroupErrorCode
from .....account.models import User
from .....channel.models import Channel
from .....core.exceptions import PermissionDenied
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import AccountPermissions, get_permissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.utils import get_out_of_scope_permissions, get_user_accessible_channels
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_314, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import PermissionEnum
from ....core.mutations import ModelMutation
from ....core.types import BaseInputObjectType, NonNullList, PermissionGroupError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Group


class PermissionGroupInput(BaseInputObjectType):
    add_permissions = NonNullList(
        PermissionEnum,
        description="List of permission code names to assign to this group.",
        required=False,
    )
    add_users = NonNullList(
        graphene.ID,
        description="List of users to assign to this group.",
        required=False,
    )
    add_channels = NonNullList(
        graphene.ID,
        description="List of channels to assign to this group."
        + ADDED_IN_314
        + PREVIEW_FEATURE,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class PermissionGroupCreateInput(PermissionGroupInput):
    name = graphene.String(description="Group name.", required=True)
    restricted_access_to_channels = graphene.Boolean(
        description=(
            "Determine if the group has restricted access to channels.  DEFAULT: False"
        )
        + ADDED_IN_314
        + PREVIEW_FEATURE,
        default_value=False,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class PermissionGroupCreate(ModelMutation):
    class Arguments:
        input = PermissionGroupCreateInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = (
            "Create new permission group. "
            "Apps are not allowed to perform this mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.Group
        object_type = Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PERMISSION_GROUP_CREATED,
            )
        ]

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            if add_permissions := cleaned_data.get("add_permissions"):
                instance.permissions.add(*add_permissions)

            if users := cleaned_data.get("add_users"):
                instance.user_set.add(*users)

            if cleaned_data.get("restricted_access_to_channels") is False:
                instance.channels.clear()

            if channels := cleaned_data.get("add_channels"):
                instance.channels.add(*channels)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.permission_group_created, instance)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        user = info.context.user
        user = cast(User, user)
        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)
        user_accessible_channels = get_user_accessible_channels(info, info.context.user)
        cls.clean_channels(
            info, instance, user_accessible_channels, errors, cleaned_input
        )
        cls.clean_permissions(user, instance, errors, cleaned_input)
        cls.clean_users(user, errors, cleaned_input, instance)

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_permissions(
        cls,
        requestor: "User",
        group: models.Group,
        errors: dict[str, list[ValidationError]],
        cleaned_input: dict,
    ):
        field = "add_permissions"
        permission_items = cleaned_input.get(field)
        if permission_items:
            cleaned_input[field] = get_permissions(permission_items)
            if not requestor.is_superuser:
                cls.ensure_can_manage_permissions(
                    requestor, errors, field, permission_items
                )

    @classmethod
    def check_permissions(cls, context, permissions=None, **data):
        app = get_app_promise(context).get()
        if app:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    def ensure_can_manage_permissions(
        cls,
        requestor: "User",
        errors: dict[str, list[ValidationError]],
        field: str,
        permission_items: list[str],
    ):
        """Check if requestor can manage permissions from input.

        Requestor cannot manage permissions witch he doesn't have.
        """
        missing_permissions = get_out_of_scope_permissions(requestor, permission_items)
        if missing_permissions:
            # add error
            error_msg = "You can't add permission that you don't have."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            params = {"permissions": missing_permissions}
            cls.update_errors(errors, error_msg, field, code, params)

    @classmethod
    def clean_users(
        cls,
        requestor: User,
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        user_items = cleaned_input.get("add_users")
        if user_items:
            cls.ensure_users_are_staff(errors, "add_users", cleaned_input)

    @classmethod
    def ensure_users_are_staff(
        cls,
        errors: dict[str, list[ValidationError]],
        field: str,
        cleaned_input: dict,
    ):
        """Ensure all of the users are staff members, raise error if not."""
        users = cleaned_input[field]
        non_staff_users = [user.pk for user in users if not user.is_staff]
        if non_staff_users:
            # add error
            ids = [graphene.Node.to_global_id("User", pk) for pk in non_staff_users]
            error_msg = "User must be staff member."
            code = PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.value
            params = {"users": ids}
            cls.update_errors(errors, error_msg, field, code, params)

    @classmethod
    def clean_channels(
        cls,
        info: ResolveInfo,
        group: models.Group,
        user_accessible_channels: list["Channel"],
        errors: dict,
        cleaned_input: dict,
    ):
        """Clean adding channels when the group hasn't restricted access to channels."""
        user = info.context.user
        user = cast(User, user)
        if cleaned_input.get("restricted_access_to_channels") is False:
            if not user.is_superuser:
                channel_ids = set(Channel.objects.values_list("id", flat=True))
                accessible_channel_ids = {
                    channel.id for channel in user_accessible_channels
                }
                not_accessible_channels = set(channel_ids - accessible_channel_ids)
                error_code = PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.value
                if not_accessible_channels:
                    raise ValidationError(
                        {
                            "restricted_access_to_channels": ValidationError(
                                "You can't manage group with channels out of "
                                "your scope.",
                                code=error_code,
                            )
                        }
                    )
            cleaned_input["add_channels"] = []
        elif add_channels := cleaned_input.get("add_channels"):
            cls.ensure_can_manage_channels(
                user, user_accessible_channels, errors, add_channels
            )

    @classmethod
    def ensure_can_manage_channels(
        cls,
        user: "User",
        user_accessible_channels: list["Channel"],
        errors: dict,
        channels: list["Channel"],
    ):
        # user must have access to all channels from `add_channels` list
        if user.is_superuser:
            return
        channel_ids = {str(channel.id) for channel in channels}
        accessible_channel_ids = {
            str(channel.id) for channel in user_accessible_channels
        }
        invalid_channel_ids = channel_ids - accessible_channel_ids
        if invalid_channel_ids:
            ids = [
                graphene.Node.to_global_id("Channel", pk) for pk in invalid_channel_ids
            ]
            error_msg = "You can't add channel that you don't have access to."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.value
            params = {"channels": ids}
            cls.update_errors(errors, error_msg, "add_channels", code, params)

    @classmethod
    def update_errors(
        cls,
        errors: dict[str, list[ValidationError]],
        msg: str,
        field: str,
        code: str,
        params: dict,
    ):
        """Create ValidationError and add it to error list."""
        error = ValidationError(message=msg, code=code, params=params)
        errors[field].append(error)
