import graphene
from django.contrib.auth import password_validation
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....account import events as account_events
from .....account import models
from .....account.error_codes import AccountErrorCode
from .....core.db.connection import allow_writer
from .....core.tokens import token_generator
from .....order.utils import match_orders_with_new_user
from ....core import ResolveInfo
from ....core.context import disallow_replica_in_context
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import validation_error_to_error_type
from ....core.types import AccountError
from ..base import INVALID_TOKEN
from . import CreateToken


class SetPassword(CreateToken):
    class Arguments:
        token = graphene.String(
            description="A one-time token required to set the password.", required=True
        )
        email = graphene.String(required=True, description="Email of a user.")
        password = graphene.String(required=True, description="Password of a user.")

    class Meta:
        description = (
            "Sets the user's password from the token sent by email "
            "using the RequestPasswordReset mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    @allow_writer()
    def mutate(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, email, password, token
    ):
        disallow_replica_in_context(info.context)

        try:
            cls._set_password_for_user(email, password, token)
        except ValidationError as e:
            errors = validation_error_to_error_type(e, AccountError)
            return cls.handle_typed_errors(errors)
        return super().mutate(root, info, email=email, password=password)

    @classmethod
    def _set_password_for_user(cls, email, password, token):
        error = False
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            # If user doesn't exists in the database we create fake user for calculation
            # purpose, as we don't want to indicate non existence of user in the system.
            error = True
            user = models.User()

        valid_token = token_generator.check_token(user, token)
        if not valid_token or error:
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )
        try:
            password_validation.validate_password(password, user)
        except ValidationError as e:
            raise ValidationError({"password": e}) from e
        fields_to_save = ["password", "updated_at"]
        user.set_password(password)
        # To reset the password user need to process the token sent separately by email,
        # so we can be sure that the user has access to email account and can be
        # confirmed.
        if not user.is_confirmed:
            user.is_confirmed = True
            match_orders_with_new_user(user)
            fields_to_save.append("is_confirmed")
        user.save(update_fields=fields_to_save)
        account_events.customer_password_reset_event(user=user)
