import graphene

from ....app import models
from ....app.manifest_validations import clean_manifest_url
from ....app.tasks import install_app_task
from ....permission.enums import AppPermission, get_permissions
from ...core.enums import PermissionEnum
from ...core.mutations import ModelMutation
from ...core.types import AppError, NonNullList
from ...decorators import staff_member_required
from ...utils import get_user_or_app_from_context
from ..types import AppInstallation
from ..utils import ensure_can_manage_permissions


class AppInstallInput(graphene.InputObjectType):
    app_name = graphene.String(description="Name of the app to install.")
    manifest_url = graphene.String(description="Url to app's manifest in JSON format.")
    activate_after_installation = graphene.Boolean(
        default_value=True,
        required=False,
        description="Determine if app will be set active or not.",
    )
    permissions = NonNullList(
        PermissionEnum,
        description="List of permission code names to assign to this app.",
    )


class AppInstall(ModelMutation):
    class Arguments:
        input = AppInstallInput(
            required=True,
            description="Fields required to install a new app.",
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Install new app by using app manifest. Requires the following "
            "permissions: AUTHENTICATED_STAFF_USER and MANAGE_APPS."
        )
        model = models.AppInstallation
        object_type = AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_input(cls, info, instance, data, **kwargs):
        manifest_url = data.get("manifest_url")
        clean_manifest_url(manifest_url)

        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        # clean and prepare permissions
        if "permissions" in cleaned_input:
            requestor = get_user_or_app_from_context(info.context)
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
            ensure_can_manage_permissions(requestor, permissions)
        return cleaned_input

    @classmethod
    @staff_member_required
    def perform_mutation(cls, root, info, /, **data):
        return super().perform_mutation(root, info, **data)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        activate_after_installation = cleaned_input["activate_after_installation"]
        install_app_task.delay(instance.pk, activate_after_installation)
