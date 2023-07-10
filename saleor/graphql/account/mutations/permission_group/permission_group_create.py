from collections import defaultdict
from typing import Dict, List, cast

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import PermissionGroupErrorCode
from .....account.models import User
from .....channel.models import Channel
from .....core.exceptions import PermissionDenied
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import (
    AccountPermissions,
    ChannelPermissions,
    get_permissions,
)
from .....webhook.event_types import WebhookEventAsyncType
from ....account.utils import get_out_of_scope_permissions
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
        description="Determine if the group has restricted access to channels."
        + ADDED_IN_314
        + PREVIEW_FEATURE,
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
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)

        cls.clean_channels(info, instance, [], errors, cleaned_input)
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
        errors: Dict[str, List[ValidationError]],
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
        errors: Dict[str, List[ValidationError]],
        field: str,
        permission_items: List[str],
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
        errors: Dict[str, List[ValidationError]],
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
        user_accessible_channels: List["Channel"],
        errors: dict,
        cleaned_input: dict,
    ):
        """Clean adding channels when the group hasn't restricted access to channels."""
        user = info.context.user
        user = cast(User, user)

        if "restricted_access_to_channels" in cleaned_input:
            cls.ensure_can_manage_channels(
                user, errors, "restricted_access_to_channels"
            )
            if cleaned_input.get("restricted_access_to_channels") is False:
                cleaned_input["add_channels"] = []

        elif cleaned_input.get("add_channels"):
            cls.ensure_can_manage_channels(user, errors, "add_channels")

    @classmethod
    def ensure_can_manage_channels(cls, user: "User", errors: dict, field: str):
        if user.is_superuser:
            return

        if user.has_perm(ChannelPermissions.MANAGE_CHANNELS):
            return

        cls.update_errors(
            errors,
            "You can't manage channels.",
            field,
            PermissionGroupErrorCode.OUT_OF_SCOPE_CHANNEL.value,
            {},
        )

    @classmethod
    def update_errors(
        cls,
        errors: Dict[str, List[ValidationError]],
        msg: str,
        field: str,
        code: str,
        params: dict,
    ):
        """Create ValidationError and add it to error list."""
        error = ValidationError(message=msg, code=code, params=params)
        errors[field].append(error)
