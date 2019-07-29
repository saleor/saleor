import graphene

from ...menu import models
from ...menu.utils import update_menus
from ..core.mutations import ModelBulkDeleteMutation


class MenuBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of menu IDs to delete."
        )

    class Meta:
        description = "Deletes menus."
        model = models.Menu
        permissions = ("menu.manage_menus",)


class MenuItemBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of menu item IDs to delete."
        )

    class Meta:
        description = "Deletes menu items."
        model = models.MenuItem
        permissions = ("menu.manage_menus",)

    @classmethod
    def bulk_action(cls, queryset):
        menu_ids = {item.menu_id for item in queryset}
        queryset.delete()
        update_menus(menu_ids)
