import graphene
from django.core.exceptions import ValidationError

from ....app import models
from ....app.error_codes import AppErrorCode
from ....core.permissions import AppPermission
from ...account.utils import can_manage_app
from ...core.mutations import ModelDeleteMutation
from ...core.types import AppError
from ...utils import get_user_or_app_from_context, requestor_is_superuser
from ..types import AppToken


class AppTokenDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of an auth token to delete.", required=True)

    class Meta:
        description = "Deletes an authentication token assigned to app."
        model = models.AppToken
        object_type = AppToken
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        app = instance.app
        requestor = get_user_or_app_from_context(info.context)
        if not requestor_is_superuser(requestor) and not can_manage_app(requestor, app):
            msg = "You can't delete this app token."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"id": ValidationError(msg, code=code)})
