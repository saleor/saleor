from collections import defaultdict
from typing import cast

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....account.notifications import send_set_password_notification
from .....account.search import USER_SEARCH_FIELDS, prepare_user_search_document_value
from .....core.exceptions import PermissionDenied
from .....core.tracing import traced_atomic_transaction
from .....core.utils.url import validate_storefront_url
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelMutation
from ....core.types import NonNullList, StaffError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_groups_which_user_can_manage
from ..base import UserInput


class StaffInput(UserInput):
    add_groups = NonNullList(
        graphene.ID,
        description="List of permission group IDs to which user should be assigned.",
        required=False,
    )


class StaffCreateInput(StaffInput):
    redirect_url = graphene.String(
        description=(
            "URL of a view where users should be redirected to "
            "set the password. URL in RFC 1808 format."
        )
    )

    class Meta:
        description = "Fields required to create a staff user."
        doc_category = DOC_CATEGORY_USERS


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffCreateInput(
            description="Fields required to create a staff user.", required=True
        )

    class Meta:
        description = (
            "Creates a new staff user. "
            "Apps are not allowed to perform this mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"
        support_meta_field = True
        support_private_meta_field = True
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.STAFF_CREATED,
                description="A new staff account was created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for setting the password.",
            ),
        ]

    @classmethod
    def check_permissions(cls, context, permissions=None, **data):
        app = get_app_promise(context).get()
        if app:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        errors = defaultdict(list)
        if cleaned_input.get("redirect_url"):
            try:
                validate_storefront_url(cleaned_input.get("redirect_url"))
            except ValidationError as error:
                error.code = AccountErrorCode.INVALID.value
                errors["redirect_url"].append(error)

        user = info.context.user
        user = cast(models.User, user)
        # set is_staff to True to create a staff user
        cleaned_input["is_staff"] = True
        cls.clean_groups(user, cleaned_input, errors)
        cls.clean_is_active(cleaned_input, instance, info.context.user, errors)

        email = cleaned_input.get("email")
        if email:
            cleaned_input["email"] = email.lower()

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_groups(cls, requestor: models.User, cleaned_input: dict, errors: dict):
        if cleaned_input.get("add_groups"):
            cls.ensure_requestor_can_manage_groups(
                requestor, cleaned_input, "add_groups", errors
            )

    @classmethod
    def ensure_requestor_can_manage_groups(
        cls, requestor: models.User, cleaned_input: dict, field: str, errors: dict
    ):
        """Check if requestor can manage group.

        Requestor cannot manage group with wider scope of permissions.
        """
        if requestor.is_superuser:
            return
        groups = cleaned_input[field]
        user_editable_groups = get_groups_which_user_can_manage(requestor)
        out_of_scope_groups = set(groups) - set(user_editable_groups)
        if out_of_scope_groups:
            # add error
            ids = [
                graphene.Node.to_global_id("Group", group.pk)
                for group in out_of_scope_groups
            ]
            error_msg = "You can't manage these groups."
            code = AccountErrorCode.OUT_OF_SCOPE_GROUP.value
            params = {"groups": ids}
            error = ValidationError(message=error_msg, code=code, params=params)
            errors[field].append(error)

    @classmethod
    def clean_is_active(cls, cleaned_input, instance, request, errors):
        pass

    @classmethod
    def save(cls, info: ResolveInfo, user, cleaned_input, send_notification=True):
        if any([field in cleaned_input for field in USER_SEARCH_FIELDS]):
            user.search_document = prepare_user_search_document_value(
                user, attach_addresses_data=False
            )
        user.save()
        if cleaned_input.get("redirect_url") and send_notification:
            manager = get_plugin_manager_promise(info.context).get()
            send_set_password_notification(
                redirect_url=cleaned_input.get("redirect_url"),
                user=user,
                manager=manager,
                channel_slug=None,
                staff=True,
            )

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            groups = cleaned_data.get("add_groups")
            if groups:
                instance.groups.add(*groups)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.staff_created, instance)

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        object_id = data.get("id")
        email = data.get("input", {}).get("email")
        send_notification = True

        if (
            not object_id
            and email
            and (
                user := models.User.objects.filter(email=email, is_staff=False).first()
            )
        ):
            send_notification = False
            return user, send_notification
        return super().get_instance(info, **data), send_notification

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance, send_notification = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)
        instance = cls.construct_instance(instance, cleaned_input)

        cls.validate_and_update_metadata(instance, metadata_list, private_metadata_list)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input, send_notification)
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)
