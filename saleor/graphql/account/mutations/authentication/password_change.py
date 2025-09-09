from typing import cast

import graphene
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from .....account import events as account_events
from .....account import models
from .....account.error_codes import AccountErrorCode
from .....permission.auth_filters import AuthorizationFilters
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....directives import doc
from ...types import User


@doc(category=DOC_CATEGORY_USERS)
class PasswordChange(BaseMutation):
    """Change the password of the logged in user."""

    user = graphene.Field(User, description="A user instance with a new password.")

    class Arguments:
        old_password = graphene.String(
            required=False, description="Current user password."
        )
        new_password = graphene.String(required=True, description="New user password.")

    class Meta:
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @staticmethod
    def raise_invalid_credentials():
        raise ValidationError(
            {
                "old_password": ValidationError(
                    "Old password isn't valid.",
                    code=AccountErrorCode.INVALID_CREDENTIALS.value,
                )
            }
        )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        user = info.context.user
        user = cast(models.User, user)
        old_password = data.get("old_password")
        new_password = data["new_password"]

        if old_password is None:
            # Spend time hashing useless password
            # This prevents the outside actors from telling if user has
            # unusable password set or not by measuring API's response time
            make_password("waste-time")

            if user.has_usable_password():
                cls.raise_invalid_credentials()
        elif not user.check_password(old_password):
            cls.raise_invalid_credentials()
        try:
            password_validation.validate_password(new_password, user)
        except ValidationError as e:
            raise ValidationError({"new_password": e}) from e

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        account_events.customer_password_changed_event(user=user)
        return PasswordChange(user=user)
