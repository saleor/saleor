import graphene

from ...core.permissions import AccountPermissions, AppPermission, AuthorizationFilters
from ...core.utils import build_absolute_uri
from ...csv import models
from ..account.types import User
from ..account.utils import check_is_owner_or_has_one_of_perms
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..core.connection import CountableConnection
from ..core.types import Job, ModelObjectType, NonNullList
from ..utils import get_user_or_app_from_context
from .enums import ExportEventEnum


class ExportEvent(ModelObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format.",
        required=True,
    )
    type = ExportEventEnum(description="Export event type.", required=True)
    user = graphene.Field(
        User,
        description=(
            "User who performed the action. Requires one of the following "
            f"permissions: {AuthorizationFilters.OWNER.name}, "
            f"{AccountPermissions.MANAGE_STAFF.name}."
        ),
        required=False,
    )
    app = graphene.Field(
        App,
        description=(
            "App which performed the action. Requires one of the following "
            f"permissions: {AuthorizationFilters.OWNER.name}, "
            f"{AppPermission.MANAGE_APPS.name}."
        ),
        required=False,
    )
    message = graphene.String(
        description="Content of the event.",
        required=True,
    )

    class Meta:
        description = "History log of export file."
        model = models.ExportEvent
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_user(root: models.ExportEvent, info):
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor, root.user, AccountPermissions.MANAGE_STAFF
        )
        return root.user

    @staticmethod
    def resolve_app(root: models.ExportEvent, info):
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor, root.user, AppPermission.MANAGE_APPS
        )
        return root.app

    @staticmethod
    def resolve_message(root: models.ExportEvent, _info):
        return root.parameters.get("message", None)


class ExportFile(ModelObjectType):
    id = graphene.GlobalID(required=True)
    url = graphene.String(description="The URL of field to download.")
    events = NonNullList(
        ExportEvent,
        description="List of events associated with the export.",
    )
    user = graphene.Field(User)
    app = graphene.Field(App)

    class Meta:
        description = "Represents a job data of exported file."
        interfaces = [graphene.relay.Node, Job]
        model = models.ExportFile

    @staticmethod
    def resolve_url(root: models.ExportFile, info):
        content_file = root.content_file
        if not content_file:
            return None
        return build_absolute_uri(content_file.url)

    @staticmethod
    def resolve_user(root: models.ExportFile, info):
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor, root.user, AccountPermissions.MANAGE_STAFF
        )
        return root.user

    @staticmethod
    def resolve_app(root: models.ExportFile, info):
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor, root.user, AppPermission.MANAGE_APPS
        )
        return AppByIdLoader(info.context).load(root.app_id) if root.app_id else None

    @staticmethod
    def resolve_events(root: models.ExportFile, _info):
        return root.events.all().order_by("pk")


class ExportFileCountableConnection(CountableConnection):
    class Meta:
        node = ExportFile
