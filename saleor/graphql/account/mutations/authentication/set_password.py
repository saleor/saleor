import graphene
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....account import events as account_events
from .....account import models
from .....account.error_codes import AccountErrorCode
from ....core import ResolveInfo
from ....core.context import disallow_replica_in_context
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import validation_error_to_error_type
from ....core.types import AccountError
from ....plugins.dataloaders import get_plugin_manager_promise
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
    def mutate(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, email, password, token
    ):
        disallow_replica_in_context(info.context)
        manager = get_plugin_manager_promise(info.context).get()
        result = manager.perform_mutation(
            mutation_cls=cls,
            root=root,
            info=info,
            data={"email": email, "password": password, "token": token},
        )
        if result is not None:
            return result

        try:
            cls._set_password_for_user(email, password, token)
        except ValidationError as e:
            errors = validation_error_to_error_type(e, AccountError)
            return cls.handle_typed_errors(errors)
        return super().mutate(root, info, email=email, password=password)

    @classmethod
    def _set_password_for_user(cls, email, password, token):
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User doesn't exist", code=AccountErrorCode.NOT_FOUND.value
                    )
                }
            )
        if not default_token_generator.check_token(user, token):
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )
        try:
            password_validation.validate_password(password, user)
        except ValidationError as error:
            raise ValidationError({"password": error})
        user.set_password(password)
        user.save(update_fields=["password", "updated_at"])
        account_events.customer_password_reset_event(user=user)
