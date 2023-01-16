import graphene

from ...menu import models
from ...permission.enums import MenuPermissions
from ..core import ResolveInfo
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types import MenuError, NonNullList
from ..plugins.dataloaders import get_plugin_manager_promise
from .types import Menu, MenuItem


class MenuBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of menu IDs to delete."
        )

    class Meta:
        description = "Deletes menus."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        menus = list(queryset)
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for menu in menus:
            manager.menu_deleted(menu)


class MenuItemBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of menu item IDs to delete."
        )

    class Meta:
        description = "Deletes menu items."
        model = models.MenuItem
        object_type = MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        menu_items = list(queryset)
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for menu_item in menu_items:
            manager.menu_item_deleted(menu_item)
