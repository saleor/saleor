import graphene
from django.core.exceptions import ValidationError
from oauthlib.common import generate_token

from ....app import models
from ....app.error_codes import AppErrorCode
from ....permission.enums import AppPermission
from ...account.utils import can_manage_app
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import DeprecatedModelMutation
from ...core.types import AppError, BaseInputObjectType
from ...utils import get_user_or_app_from_context, requestor_is_superuser
from ..types import AppToken
from ..utils import validate_app_is_not_removed


class AppTokenInput(BaseInputObjectType):
    name = graphene.String(description="Name of the token.", required=False)
    app = graphene.ID(description="ID of app.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AppTokenCreate(DeprecatedModelMutation):
    auth_token = graphene.types.String(
        description="The newly created authentication token."
    )

    class Arguments:
        input = AppTokenInput(
            required=True, description="Fields required to create a new auth token."
        )

    class Meta:
        description = "Creates a new token."
        model = models.AppToken
        object_type = AppToken
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        input_data = data.get("input", {})
        instance = cls.get_instance(info, **data)
        cleaned_input = cls.clean_input(info, instance, input_data)
        instance = cls.construct_instance(instance, cleaned_input)
        auth_token = generate_token()
        instance.set_auth_token(auth_token)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        response = cls.success_response(instance)
        response.auth_token = auth_token
        return response

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        app = cleaned_input.get("app")
        validate_app_is_not_removed(app, data.get("app"), "app")
        requestor = get_user_or_app_from_context(info.context)
        if not requestor_is_superuser(requestor) and not can_manage_app(requestor, app):
            msg = "You can't manage this app."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"app": ValidationError(msg, code=code)})
        return cleaned_input
