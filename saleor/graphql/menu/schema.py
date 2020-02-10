import graphene

from ..core.fields import FilterInputConnectionField
from ..translations.mutations import MenuItemTranslate
from .bulk_mutations import MenuBulkDelete, MenuItemBulkDelete
from .filters import MenuFilterInput, MenuItemFilterInput
from .mutations import (
    AssignNavigation,
    MenuCreate,
    MenuDelete,
    MenuItemCreate,
    MenuItemDelete,
    MenuItemMove,
    MenuItemUpdate,
    MenuUpdate,
)
from .resolvers import resolve_menu, resolve_menu_items, resolve_menus
from .sorters import MenuItemSortingInput, MenuSortingInput
from .types import Menu, MenuItem


class MenuQueries(graphene.ObjectType):
    menu = graphene.Field(
        Menu,
        id=graphene.Argument(graphene.ID, description="ID of the menu."),
        name=graphene.Argument(graphene.String, description="The menu's name."),
        description="Look up a navigation menu by ID or name.",
    )
    menus = FilterInputConnectionField(
        Menu,
        sort_by=MenuSortingInput(description="Sort menus."),
        filter=MenuFilterInput(description="Filtering options for menus."),
        description="List of the storefront's menus.",
    )
    menu_item = graphene.Field(
        MenuItem,
        id=graphene.Argument(
            graphene.ID, description="ID of the menu item.", required=True
        ),
        description="Look up a menu item by ID.",
    )
    menu_items = FilterInputConnectionField(
        MenuItem,
        sort_by=MenuItemSortingInput(description="Sort menus items."),
        filter=MenuItemFilterInput(description="Filtering options for menu items."),
        description="List of the storefronts's menu items.",
    )

    def resolve_menu(self, info, **data):
        return resolve_menu(info, data.get("id"), data.get("name"))

    def resolve_menus(self, info, query=None, **kwargs):
        return resolve_menus(info, query, **kwargs)

    def resolve_menu_item(self, info, **data):
        return graphene.Node.get_node_from_global_id(info, data.get("id"), MenuItem)

    def resolve_menu_items(self, info, query=None, **kwargs):
        return resolve_menu_items(info, query, **kwargs)


class MenuMutations(graphene.ObjectType):
    assign_navigation = AssignNavigation.Field()

    menu_create = MenuCreate.Field()
    menu_delete = MenuDelete.Field()
    menu_bulk_delete = MenuBulkDelete.Field()
    menu_update = MenuUpdate.Field()

    menu_item_create = MenuItemCreate.Field()
    menu_item_delete = MenuItemDelete.Field()
    menu_item_bulk_delete = MenuItemBulkDelete.Field()
    menu_item_update = MenuItemUpdate.Field()
    menu_item_translate = MenuItemTranslate.Field()
    menu_item_move = MenuItemMove.Field()
