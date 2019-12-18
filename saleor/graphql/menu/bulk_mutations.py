import graphene

from ...core.permissions import MenuPermissions
from ...menu import models
from ...menu.utils import update_menus
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types.common import MenuError


class MenuBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of menu IDs to delete."
        )

    class Meta:
        description = "Deletes menus."
        model = models.Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"


class MenuItemBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of menu item IDs to delete."
        )

    class Meta:
        description = "Deletes menu items."
        model = models.MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def bulk_action(cls, queryset):
        menu_ids = {item.menu_id for item in queryset}
        queryset.delete()
        update_menus(menu_ids)
