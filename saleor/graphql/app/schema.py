import graphene

from ...core.permissions import AppPermission
from ..core.fields import FilterInputConnectionField, PrefetchingConnectionField
from ..core.types import FilterInputObjectType
from ..decorators import permission_required
from .filters import AppFilter
from .mutations import (
    AppCreate,
    AppDelete,
    AppTokenCreate,
    AppTokenDelete,
    AppUpdate,
    DropFailedInstallation,
    InstallApp,
    RetryInstallApp,
)
from .resolvers import resolve_apps
from .sorters import AppSortingInput
from .types import App, OngoingAppInstallation


class AppFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AppFilter


class AppQueries(graphene.ObjectType):
    ongoing_apps_installations = PrefetchingConnectionField(
        OngoingAppInstallation, description="List of all ongoing apps installations"
    )
    apps = FilterInputConnectionField(
        App,
        filter=AppFilterInput(description="Filtering options for apps."),
        sort_by=AppSortingInput(description="Sort apps."),
        description="List of the apps.",
    )
    app = graphene.Field(
        App,
        id=graphene.Argument(graphene.ID, description="ID of the app.", required=True),
        description="Look up a app by ID.",
    )

    @permission_required(AppPermission.MANAGE_APPS)
    def resolve_apps(self, info, **kwargs):
        return resolve_apps(info, **kwargs)

    @permission_required(AppPermission.MANAGE_APPS)
    def resolve_app(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, App)


class AppMutations(graphene.ObjectType):
    app_create = AppCreate.Field()
    app_update = AppUpdate.Field()
    app_delete = AppDelete.Field()

    app_token_create = AppTokenCreate.Field()
    app_token_delete = AppTokenDelete.Field()

    install_app = InstallApp.Field()
    retry_install_app = RetryInstallApp.Field()
    drop_failed_installation = DropFailedInstallation.Field()
