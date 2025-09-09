import graphene
from django.core.exceptions import ValidationError
from graphene_directives import directive

from ....account import models
from ....account.error_codes import AccountErrorCode
from ....permission.enums import AccountPermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_USERS
from ...core.mutations import BaseBulkMutation
from ...core.types import AccountError, NonNullList
from ...directives import doc
from ..types import User


@doc(category=DOC_CATEGORY_USERS)
class UserBulkSetActive(BaseBulkMutation):
    """Activate or deactivate users."""

    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of user IDs to activate/deactivate.",
        )
        is_active = graphene.Boolean(
            required=True, description="Determine if users will be set active or not."
        )

    class Meta:
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
        if instance.is_superuser:
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
