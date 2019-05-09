import graphene

from ...menu import models
from ..core.mutations import ModelBulkDeleteMutation


class MenuBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of menu IDs to delete."
        )

    class Meta:
        description = "Deletes menus."
        model = models.Menu

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm("menu.manage_menus")


class MenuItemBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of menu item IDs to delete."
        )

    class Meta:
        description = "Deletes menu items."
        model = models.MenuItem

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm("menu.manage_menus")
