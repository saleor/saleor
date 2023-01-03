import graphene
from django.core.exceptions import ValidationError

from ....app import models
from ....app.error_codes import AppErrorCode
from ....core import JobStatus
from ....core.permissions import AppPermission
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import AppError
from ..types import AppInstallation


class AppDeleteFailedInstallation(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            description="ID of failed installation to delete.", required=True
        )

    class Meta:
        description = "Delete failed installation."
        model = models.AppInstallation
        object_type = AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_instance(cls, _info: ResolveInfo, instance):
        if instance.status != JobStatus.FAILED:
            msg = "Cannot delete installation with different status than failed."
            code = AppErrorCode.INVALID_STATUS.value
            raise ValidationError({"id": ValidationError(msg, code=code)})
