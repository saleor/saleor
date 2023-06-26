from typing import cast

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....core.tokens import account_delete_token_generator
from .....permission.auth_filters import AuthorizationFilters
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelDeleteMutation
from ....core.types import AccountError
from ...types import User
from ..base import INVALID_TOKEN


class AccountDelete(ModelDeleteMutation):
    class Arguments:
        token = graphene.String(
            description=(
                "A one-time token required to remove account. "
                "Sent by email using AccountRequestDeletion mutation."
            ),
            required=True,
        )

    class Meta:
        description = "Remove user account."
        doc_category = DOC_CATEGORY_USERS
        model = models.User
        object_type = User
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError(
                "Cannot delete a staff account.",
                code=AccountErrorCode.DELETE_STAFF_ACCOUNT.value,
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, token
    ):
        user = info.context.user
        user = cast(models.User, user)
        cls.clean_instance(info, user)

        if not account_delete_token_generator.check_token(user, token):
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )

        db_id = user.id

        user.delete()
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        user.id = db_id
        return cls.success_response(user)
