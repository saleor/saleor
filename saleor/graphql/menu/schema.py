import graphene

from ..core.fields import PrefetchingConnectionField
from ..descriptions import DESCRIPTIONS
from ..translations.mutations import MenuItemTranslate
from .bulk_mutations import MenuBulkDelete, MenuItemBulkDelete
from .mutations import (
    AssignNavigation, MenuCreate, MenuDelete, MenuItemCreate, MenuItemDelete,
    MenuItemMove, MenuItemUpdate, MenuUpdate)
from .resolvers import resolve_menu, resolve_menu_items, resolve_menus
from .types import Menu, MenuItem


class MenuQueries(graphene.ObjectType):
    menu = graphene.Field(
        Menu, id=graphene.Argument(graphene.ID),
        name=graphene.Argument(graphene.String, description="Menu name."),
        description='Lookup a menu by ID or name.')
    menus = PrefetchingConnectionField(
        Menu, query=graphene.String(description=DESCRIPTIONS['menu']),
        description="List of the shop\'s menus.")
    menu_item = graphene.Field(
        MenuItem, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a menu item by ID.')
    menu_items = PrefetchingConnectionField(
        MenuItem, query=graphene.String(description=DESCRIPTIONS['menu_item']),
        description='List of the shop\'s menu items.')

    def resolve_menu(self, info, **data):
        return resolve_menu(info, data.get('id'), data.get('name'))

    def resolve_menus(self, info, query=None, **_kwargs):
        return resolve_menus(info, query)

    def resolve_menu_item(self, info, **data):
        return graphene.Node.get_node_from_global_id(
            info, data.get('id'), MenuItem)

    def resolve_menu_items(self, info, query=None, **_kwargs):
        return resolve_menu_items(info, query)


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
