from typing import cast

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....core.tracing import traced_atomic_transaction
from .....giftcard.search import mark_gift_cards_search_index_as_dirty
from .....giftcard.utils import assign_user_gift_cards, get_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import NonNullList, StaffError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....utils.validators import check_for_duplicates
from ...utils import (
    get_not_manageable_permissions_when_deactivate_or_remove_users,
    get_out_of_scope_users,
)
from .staff_create import StaffCreate, StaffInput


class StaffUpdateInput(StaffInput):
    remove_groups = NonNullList(
        graphene.ID,
        description=(
            "List of permission group IDs from which user should be unassigned."
        ),
        required=False,
    )

    class Meta:
        description = "Fields required to update a staff user."
        doc_category = DOC_CATEGORY_USERS


class StaffUpdate(StaffCreate):
    class Arguments:
        id = graphene.ID(description="ID of a staff user to update.", required=True)
        input = StaffUpdateInput(
            description="Fields required to update a staff user.", required=True
        )

    class Meta:
        description = (
            "Updates an existing staff user. "
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
                type=WebhookEventAsyncType.STAFF_UPDATED,
                description="A staff account was updated.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        user = info.context.user
        user = cast(models.User, user)
        # check if user can manage this user
        if not user.is_superuser and get_out_of_scope_users(user, [instance]):
            msg = "You can't manage this user."
            code = AccountErrorCode.OUT_OF_SCOPE_USER.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

        error = check_for_duplicates(data, "add_groups", "remove_groups", "groups")
        if error:
            error.code = AccountErrorCode.DUPLICATED_INPUT_ITEM.value
            raise error

        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        return cleaned_input

    @classmethod
    def clean_groups(cls, requestor: models.User, cleaned_input: dict, errors: dict):
        if cleaned_input.get("add_groups"):
            cls.ensure_requestor_can_manage_groups(
                requestor, cleaned_input, "add_groups", errors
            )
        if cleaned_input.get("remove_groups"):
            cls.ensure_requestor_can_manage_groups(
                requestor, cleaned_input, "remove_groups", errors
            )

    @classmethod
    def clean_is_active(
        cls,
        cleaned_input: dict,
        instance: models.User,
        requestor: models.User,
        errors: dict,
    ):
        is_active = cleaned_input.get("is_active")
        if is_active is None:
            return
        if not is_active:
            cls.check_if_deactivating_superuser_or_own_account(
                instance, requestor, errors
            )
            cls.check_if_deactivating_left_not_manageable_permissions(
                instance, requestor, errors
            )

    @classmethod
    def check_if_deactivating_superuser_or_own_account(
        cls, instance: models.User, requestor: models.User, errors: dict
    ):
        """User cannot deactivate superuser or own account.

        Args:
            instance: user instance which is going to deactivated
            requestor: user who performs the mutation
            errors: a dictionary to accumulate mutation errors

        """
        if requestor == instance:
            error = ValidationError(
                "Cannot deactivate your own account.",
                code=AccountErrorCode.DEACTIVATE_OWN_ACCOUNT.value,
            )
            errors["is_active"].append(error)
        elif instance.is_superuser:
            error = ValidationError(
                "Cannot deactivate superuser's account.",
                code=AccountErrorCode.DEACTIVATE_SUPERUSER_ACCOUNT.value,
            )
            errors["is_active"].append(error)

    @classmethod
    def check_if_deactivating_left_not_manageable_permissions(
        cls, user: models.User, requestor: models.User, errors: dict
    ):
        """Check if after deactivating user all permissions will be manageable.

        After deactivating user, for each permission, there should be at least one
        active staff member who can manage it (has both “manage staff” and
        this permission).
        """
        if requestor.is_superuser:
            return
        permissions = get_not_manageable_permissions_when_deactivate_or_remove_users(
            [user]
        )
        if permissions:
            # add error
            msg = (
                "Users cannot be deactivated, some of permissions "
                "will not be manageable."
            )
            code = AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permissions}
            error = ValidationError(msg, code=code, params=params)
            errors["is_active"].append(error)

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            add_groups = cleaned_data.get("add_groups")
            if add_groups:
                instance.groups.add(*add_groups)
            remove_groups = cleaned_data.get("remove_groups")
            if remove_groups:
                instance.groups.remove(*remove_groups)

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        original_instance, _ = cls.get_instance(info, **data)
        response = super().perform_mutation(root, info, **data)
        user = response.user
        has_new_email = user.email != original_instance.email
        has_new_name = original_instance.get_full_name() != user.get_full_name()

        if has_new_email:
            assign_user_gift_cards(user)
            match_orders_with_new_user(user)

        if has_new_email or has_new_name:
            if gift_cards := get_user_gift_cards(user):
                mark_gift_cards_search_index_as_dirty(gift_cards)

        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.staff_updated, instance)
