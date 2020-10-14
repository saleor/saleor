import graphene
from graphene import relay

from ...menu import models
from ...product.models import Collection
from ..channel.types import ChannelContext, ChannelContextType
from ..core.connection import CountableDjangoObjectType
from ..page.dataloaders import PageByIdLoader
from ..product.dataloaders import CategoryByIdLoader
from ..translations.fields import TranslationField
from ..translations.types import MenuItemTranslation
from .dataloaders import (
    MenuByIdLoader,
    MenuItemByIdLoader,
    MenuItemChildrenLoader,
    MenuItemsByParentMenuLoader,
)


class Menu(ChannelContextType, CountableDjangoObjectType):
    items = graphene.List(lambda: MenuItem)

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Represents a single menu - an object that is used to help navigate "
            "through the store."
        )
        interfaces = [relay.Node]
        only_fields = ["id", "name"]
        model = models.Menu

    @staticmethod
    def resolve_items(root: ChannelContext[models.Menu], info, **_kwargs):
        menu_items = MenuItemsByParentMenuLoader(info.context).load(root.node.id)
        return menu_items.then(
            lambda menu_items: [
                ChannelContext(node=menu_item, channel_slug=root.channel_slug)
                for menu_item in menu_items
            ]
        )


class MenuItem(ChannelContextType, CountableDjangoObjectType):
    children = graphene.List(lambda: MenuItem)
    url = graphene.String(description="URL to the menu item.")
    translation = TranslationField(
        MenuItemTranslation,
        type_name="menu item",
        resolver=ChannelContextType.resolve_translation,
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context

        description = (
            "Represents a single item of the related menu. Can store categories, "
            "collection or pages."
        )
        interfaces = [relay.Node]
        only_fields = [
            "category",
            "collection",
            "id",
            "level",
            "menu",
            "name",
            "page",
            "parent",
        ]
        model = models.MenuItem

    @staticmethod
    def resolve_category(root: ChannelContext[models.MenuItem], info, **_kwargs):
        if root.node.category_id:
            return CategoryByIdLoader(info.context).load(root.node.category_id)
        return None

    @staticmethod
    def resolve_children(root: ChannelContext[models.MenuItem], info, **_kwargs):
        menus = MenuItemChildrenLoader(info.context).load(root.node.id)
        return menus.then(
            lambda menus: [
                ChannelContext(node=menu, channel_slug=None) for menu in menus
            ]
        )

    @staticmethod
    def resolve_collection(root: ChannelContext[models.MenuItem], info, **_kwargs):
        # TODO: Add dataloader
        if root.node.collection_id and root.channel_slug:
            collection = Collection.objects.filter(
                id=root.node.collection_id,
                channel_listing__channel__slug=str(root.channel_slug),
                channel_listing__channel__is_active=True,
                channel_listing__is_published=True,
            ).first()
            return (
                ChannelContext(node=collection, channel_slug=None)
                if collection
                else None
            )
        return None

    @staticmethod
    def resolve_menu(root: ChannelContext[models.MenuItem], info, **_kwargs):
        if root.node.menu_id:
            menu = MenuByIdLoader(info.context).load(root.node.menu_id)
            return menu.then(lambda menu: ChannelContext(node=menu, channel_slug=None))
        return None

    @staticmethod
    def resolve_parent(root: ChannelContext[models.MenuItem], info, **_kwargs):
        if root.node.parent_id:
            menu = MenuItemByIdLoader(info.context).load(root.node.parent_id)
            return menu.then(lambda menu: ChannelContext(node=menu, channel_slug=None))
        return None

    @staticmethod
    def resolve_page(root: ChannelContext[models.MenuItem], info, **kwargs):
        if root.node.page_id:
            return PageByIdLoader(info.context).load(root.node.page_id)
        return None


class MenuItemMoveInput(graphene.InputObjectType):
    item_id = graphene.ID(description="The menu item ID to move.", required=True)
    parent_id = graphene.ID(
        description="ID of the parent menu. If empty, menu will be top level menu."
    )
    sort_order = graphene.Int(
        description=(
            "The new relative sorting position of the item (from -inf to +inf). "
            "1 moves the item one position forward, -1 moves the item one position "
            "backward, 0 leaves the item unchanged."
        )
    )
