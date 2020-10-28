import graphene

from ..channel import ChannelContext, ChannelQsContext
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..core.fields import ChannelContextFilterConnectionField
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
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        id=graphene.Argument(graphene.ID, description="ID of the menu."),
        name=graphene.Argument(graphene.String, description="The menu's name."),
        slug=graphene.Argument(graphene.String, description="The menu's slug."),
        description="Look up a navigation menu by ID or name.",
    )
    menus = ChannelContextFilterConnectionField(
        Menu,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        sort_by=MenuSortingInput(description="Sort menus."),
        filter=MenuFilterInput(description="Filtering options for menus."),
        description="List of the storefront's menus.",
    )
    menu_item = graphene.Field(
        MenuItem,
        id=graphene.Argument(
            graphene.ID, description="ID of the menu item.", required=True
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a menu item by ID.",
    )
    menu_items = ChannelContextFilterConnectionField(
        MenuItem,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        sort_by=MenuItemSortingInput(description="Sort menus items."),
        filter=MenuItemFilterInput(description="Filtering options for menu items."),
        description="List of the storefronts's menu items.",
    )

    def resolve_menu(self, info, channel=None, **data):
        if channel is None:
            channel = get_default_channel_slug_or_graphql_error()
        return resolve_menu(
            info, channel, data.get("id"), data.get("name"), data.get("slug")
        )

    def resolve_menus(self, info, query=None, channel=None, **kwargs):
        if channel is None:
            channel = get_default_channel_slug_or_graphql_error()
        return resolve_menus(info, channel, query, **kwargs)

    def resolve_menu_item(self, info, channel=None, **data):
        if channel is None:
            channel = get_default_channel_slug_or_graphql_error()
        menu_item = graphene.Node.get_node_from_global_id(
            info, data.get("id"), MenuItem
        )
        return ChannelContext(node=menu_item, channel_slug=channel)

    def resolve_menu_items(self, info, query=None, channel=None, **kwargs):
        if channel is None:
            channel = get_default_channel_slug_or_graphql_error()
        menu_items = resolve_menu_items(info, query, **kwargs)
        return ChannelQsContext(qs=menu_items, channel_slug=channel)


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
