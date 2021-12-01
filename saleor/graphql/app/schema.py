import graphene

from ...core.permissions import AppPermission
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_31
from ..core.fields import FilterConnectionField
from ..core.types import FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..decorators import permission_required, staff_member_or_app_required
from .dataloaders import AppByIdLoader, AppExtensionByIdLoader
from .filters import AppExtensionFilter, AppFilter
from .mutations import (
    AppActivate,
    AppCreate,
    AppDeactivate,
    AppDelete,
    AppDeleteFailedInstallation,
    AppFetchManifest,
    AppInstall,
    AppRetryInstall,
    AppTokenCreate,
    AppTokenDelete,
    AppTokenVerify,
    AppUpdate,
)
from .resolvers import (
    resolve_app,
    resolve_app_extensions,
    resolve_apps,
    resolve_apps_installations,
)
from .sorters import AppSortingInput
from .types import (
    App,
    AppCountableConnection,
    AppExtension,
    AppExtensionCountableConnection,
    AppInstallation,
)


class AppFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AppFilter


class AppExtensionFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AppExtensionFilter


class AppQueries(graphene.ObjectType):
    apps_installations = graphene.List(
        graphene.NonNull(AppInstallation),
        description="List of all apps installations",
        required=True,
    )
    apps = FilterConnectionField(
        AppCountableConnection,
        filter=AppFilterInput(description="Filtering options for apps."),
        sort_by=AppSortingInput(description="Sort apps."),
        description="List of the apps.",
    )
    app = graphene.Field(
        App,
        id=graphene.Argument(graphene.ID, description="ID of the app.", required=False),
        description=(
            "Look up an app by ID. "
            "If ID is not provided, return the currently authenticated app."
        ),
    )

    app_extensions = FilterConnectionField(
        AppExtensionCountableConnection,
        filter=AppExtensionFilterInput(
            description="Filtering options for apps extensions."
        ),
        description=f"{ADDED_IN_31} List of all extensions",
    )
    app_extension = graphene.Field(
        AppExtension,
        id=graphene.Argument(
            graphene.ID, description="ID of the app extension.", required=True
        ),
        description=f"{ADDED_IN_31} Look up an app extension by ID.",
    )

    @permission_required(AppPermission.MANAGE_APPS)
    def resolve_apps_installations(self, info, **kwargs):
        return resolve_apps_installations(info, **kwargs)

    @permission_required(AppPermission.MANAGE_APPS)
    def resolve_apps(self, info, **kwargs):
        qs = resolve_apps(info, **kwargs)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, AppCountableConnection)

    def resolve_app(self, info, id=None):
        app = info.context.app
        if not id and app:
            return app
        return resolve_app(info, id)

    @staff_member_or_app_required
    def resolve_app_extensions(self, info, **kwargs):
        qs = resolve_app_extensions(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, AppExtensionCountableConnection
        )

    @staff_member_or_app_required
    def resolve_app_extension(self, info, id):
        def app_is_active(app_extension):
            def is_active(app):
                if app.is_active:
                    return app_extension
                return None

            if not app_extension:
                return None

            return (
                AppByIdLoader(info.context).load(app_extension.app_id).then(is_active)
            )

        _, id = from_global_id_or_error(id, "AppExtension")
        return AppExtensionByIdLoader(info.context).load(int(id)).then(app_is_active)


class AppMutations(graphene.ObjectType):
    app_create = AppCreate.Field()
    app_update = AppUpdate.Field()
    app_delete = AppDelete.Field()

    app_token_create = AppTokenCreate.Field()
    app_token_delete = AppTokenDelete.Field()
    app_token_verify = AppTokenVerify.Field()

    app_install = AppInstall.Field()
    app_retry_install = AppRetryInstall.Field()
    app_delete_failed_installation = AppDeleteFailedInstallation.Field()

    app_fetch_manifest = AppFetchManifest.Field()

    app_activate = AppActivate.Field()
    app_deactivate = AppDeactivate.Field()
