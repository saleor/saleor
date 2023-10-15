import graphene

from ....permission.enums import MenuPermissions, SitePermissions
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_MENU
from ...core.mutations import BaseMutation
from ...core.types import MenuError
from ...site.dataloaders import get_site_promise
from ..enums import NavigationType
from ..types import Menu


class AssignNavigation(BaseMutation):
    menu = graphene.Field(Menu, description="Assigned navigation menu.")

    class Arguments:
        menu = graphene.ID(description="ID of the menu.")
        navigation_type = NavigationType(
            description="Type of the navigation bar to assign the menu to.",
            required=True,
        )

    class Meta:
        description = "Assigns storefront's navigation menus."
        doc_category = DOC_CATEGORY_MENU
        permissions = (MenuPermissions.MANAGE_MENUS, SitePermissions.MANAGE_SETTINGS)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, menu=None, navigation_type
    ):
        site = get_site_promise(info.context).get()
        if menu is not None:
            menu = cls.get_node_or_error(info, menu, field="menu", only_type=Menu)

        if navigation_type == NavigationType.MAIN:
            site.settings.top_menu = menu
            site.settings.save(update_fields=["top_menu"])
        elif navigation_type == NavigationType.SECONDARY:
            site.settings.bottom_menu = menu
            site.settings.save(update_fields=["bottom_menu"])

        if menu is None:
            return AssignNavigation(menu=None)
        return AssignNavigation(menu=ChannelContext(node=menu, channel_slug=None))
