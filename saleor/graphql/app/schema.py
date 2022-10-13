import graphene

from ...core.exceptions import PermissionDenied
from ...core.permissions import AppPermission, AuthorizationFilters
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_31, PREVIEW_FEATURE
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.types import FilterInputObjectType, NonNullList
from ..core.utils import from_global_id_or_error
from .dataloaders import AppByIdLoader, AppExtensionByIdLoader, load_app
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
    apps_installations = PermissionsField(
        NonNullList(AppInstallation),
        description="List of all apps installations",
        required=True,
        permissions=[
            AppPermission.MANAGE_APPS,
        ],
    )
    apps = FilterConnectionField(
        AppCountableConnection,
        filter=AppFilterInput(description="Filtering options for apps."),
        sort_by=AppSortingInput(description="Sort apps."),
        description="List of the apps.",
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AppPermission.MANAGE_APPS,
        ],
    )
    app = PermissionsField(
        App,
        id=graphene.Argument(graphene.ID, description="ID of the app.", required=False),
        description=(
            "Look up an app by ID. If ID is not provided, return the currently "
            "authenticated app.\n\nRequires one of the following permissions: "
            f"{AuthorizationFilters.AUTHENTICATED_STAFF_USER.name} "
            f"{AuthorizationFilters.AUTHENTICATED_APP.name}. The authenticated app has "
            f"access to its resources. Fetching different apps requires "
            f"{AppPermission.MANAGE_APPS.name} permission."
        ),
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        auto_permission_message=False,
    )
    app_extensions = FilterConnectionField(
        AppExtensionCountableConnection,
        filter=AppExtensionFilterInput(
            description="Filtering options for apps extensions."
        ),
        description="List of all extensions." + ADDED_IN_31 + PREVIEW_FEATURE,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    app_extension = PermissionsField(
        AppExtension,
        id=graphene.Argument(
            graphene.ID, description="ID of the app extension.", required=True
        ),
        description="Look up an app extension by ID." + ADDED_IN_31 + PREVIEW_FEATURE,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )

    @staticmethod
    def resolve_apps_installations(_root, info, **kwargs):
        return resolve_apps_installations(info, **kwargs)

    @staticmethod
    def resolve_apps(_root, info, **kwargs):
        qs = resolve_apps(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, AppCountableConnection)

    @staticmethod
    def resolve_app(_root, info, *, id=None):
        if app := load_app(info.context):
            if not id:
                return app
            _, app_id = from_global_id_or_error(id, only_type="App")
            if int(app_id) == app.id:
                return app
            elif not app.has_perm(AppPermission.MANAGE_APPS):
                raise PermissionDenied(permissions=[AppPermission.MANAGE_APPS])
        return resolve_app(info, id)

    @staticmethod
    def resolve_app_extensions(_root, info, **kwargs):
        qs = resolve_app_extensions(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, AppExtensionCountableConnection
        )

    @staticmethod
    def resolve_app_extension(_root, info, *, id):
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
