import graphene
from django.core.exceptions import ValidationError

from ....app import models
from ....app.error_codes import AppErrorCode
from ....app.tasks import install_app_task
from ....core import JobStatus
from ....core.permissions import AppPermission
from ...core.mutations import ModelMutation
from ...core.types import AppError
from ..types import AppInstallation


class AppRetryInstall(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of failed installation.", required=True)
        activate_after_installation = graphene.Boolean(
            default_value=True,
            required=False,
            description="Determine if app will be set active or not.",
        )

    class Meta:
        description = "Retry failed installation of new app."
        model = models.AppInstallation
        object_type = AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.status = JobStatus.PENDING
        instance.save()

    @classmethod
    def clean_instance(cls, info, instance):
        if instance.status != JobStatus.FAILED:
            msg = "Cannot retry installation with different status than failed."
            code = AppErrorCode.INVALID_STATUS.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        activate_after_installation = data.get("activate_after_installation")
        app_installation = cls.get_instance(info, **data)
        cls.clean_instance(info, app_installation)

        cls.save(info, app_installation, cleaned_input=None)
        install_app_task.delay(app_installation.pk, activate_after_installation)
        return cls.success_response(app_installation)
