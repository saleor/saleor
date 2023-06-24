import graphene

from ....menu import models
from ....permission.enums import MenuPermissions
from ...core import ResolveInfo
from ...core.types import MenuError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import MenuItem
from .menu_item_create import MenuItemCreate, MenuItemInput


class MenuItemUpdate(MenuItemCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu item to update.")
        input = MenuItemInput(
            required=True,
            description=(
                "Fields required to update a menu item. Only one of `url`, `category`, "
                "`page`, `collection` is allowed per item."
            ),
        )

    class Meta:
        description = "Updates a menu item."
        model = models.MenuItem
        object_type = MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # Only one item can be assigned per menu item
        instance.page = None
        instance.collection = None
        instance.category = None
        instance.url = None
        return super().construct_instance(instance, cleaned_data)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.menu_item_updated, instance)
