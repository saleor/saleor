import graphene
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....giftcard.utils import assign_user_gift_cards
from .....order.utils import match_orders_with_new_user
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ...types import User

INVALID_TOKEN = "Invalid or expired token."


class ConfirmAccount(BaseMutation):
    user = graphene.Field(User, description="An activated user account.")

    class Arguments:
        token = graphene.String(
            description="A one-time token required to confirm the account.",
            required=True,
        )
        email = graphene.String(
            description="E-mail of the user performing account confirmation.",
            required=True,
        )

    class Meta:
        description = (
            "Confirm user account with token sent by email during registration."
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        try:
            user = models.User.objects.get(email=data["email"])
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this email doesn't exist",
                        code=AccountErrorCode.NOT_FOUND.value,
                    )
                }
            )

        if not default_token_generator.check_token(user, data["token"]):
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )

        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])

        match_orders_with_new_user(user)
        assign_user_gift_cards(user)

        return ConfirmAccount(user=user)
