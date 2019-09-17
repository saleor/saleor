import graphene
from django.core.exceptions import ValidationError

from ...account import models
from ...account.error_codes import AccountErrorCode
from ..core.mutations import BaseBulkMutation, ModelBulkDeleteMutation
from ..core.types.common import AccountError
from .utils import CustomerDeleteMixin, StaffDeleteMixin


class UserBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of sale IDs to delete."
        )

    class Meta:
        abstract = True


class CustomerBulkDelete(CustomerDeleteMixin, UserBulkDelete):
    class Meta:
        description = "Deletes customers."
        model = models.User
        permissions = ("account.manage_users",)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        count, errors = super().perform_mutation(root, info, **data)
        cls.post_process(info, count)
        return count, errors


class StaffBulkDelete(StaffDeleteMixin, UserBulkDelete):
    class Meta:
        description = "Deletes staff users."
        model = models.User
        permissions = ("account.manage_staff",)
        error_type_class = AccountError
        error_type_field = "account_errors"


class UserBulkSetActive(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of user IDs to (de)activate)."
        )
        is_active = graphene.Boolean(
            required=True, description="Determine if users will be set active or not."
        )

    class Meta:
        description = "Activate or deactivate users."
        model = models.User
        permissions = ("account.manage_users",)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        if info.context.user == instance:
            raise ValidationError(
                {
                    "is_active": ValidationError(
                        "Cannot activate or deactivate your own account.",
                        code=AccountErrorCode.ACTIVATE_OWN_ACCOUNT,
                    )
                }
            )
        elif instance.is_superuser:
            raise ValidationError(
                {
                    "is_active": ValidationError(
                        "Cannot activate or deactivate superuser's account.",
                        code=AccountErrorCode.ACTIVATE_SUPERUSER_ACCOUNT,
                    )
                }
            )

    @classmethod
    def bulk_action(cls, queryset, is_active):
        queryset.update(is_active=is_active)
