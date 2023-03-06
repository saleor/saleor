from collections import defaultdict
from typing import List

import graphene
from django.core.exceptions import ValidationError

from ...account import models
from ...account.error_codes import AccountErrorCode
from ...permission.enums import AccountPermissions
from ..core import ResolveInfo
from ..core.mutations import BaseBulkMutation, ModelBulkDeleteMutation
from ..core.types import AccountError, NonNullList, StaffError
from ..plugins.dataloaders import get_plugin_manager_promise
from .types import User
from .utils import CustomerDeleteMixin, StaffDeleteMixin


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
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

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


class StaffBulkDelete(StaffDeleteMixin, UserBulkDelete):
    class Meta:
        description = (
            "Deletes staff users. Apps are not allowed to perform this mutation."
        )
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
            qs = models.User.objects.filter(pk__in=clean_instance_ids)
            cls.bulk_action(info, qs, **data)
        else:
            count = 0
        return count, errors

    @classmethod
    def clean_instances(cls, info: ResolveInfo, users):
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)

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
        for instance in instances:
            manager.staff_deleted(instance)


class UserBulkSetActive(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of user IDs to (de)activate)."
        )
        is_active = graphene.Boolean(
            required=True, description="Determine if users will be set active or not."
        )

    class Meta:
        description = "Activate or deactivate users."
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        if info.context.user == instance:
            raise ValidationError(
                {
                    "is_active": ValidationError(
                        "Cannot activate or deactivate your own account.",
                        code=AccountErrorCode.ACTIVATE_OWN_ACCOUNT.value,
                    )
                }
            )
        elif instance.is_superuser:
            raise ValidationError(
                {
                    "is_active": ValidationError(
                        "Cannot activate or deactivate superuser's account.",
                        code=AccountErrorCode.ACTIVATE_SUPERUSER_ACCOUNT.value,
                    )
                }
            )

    @classmethod
    def bulk_action(  # type: ignore[override]
        cls, _info: ResolveInfo, queryset, /, *, is_active
    ):
        queryset.update(is_active=is_active)
