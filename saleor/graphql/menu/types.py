import graphene
from graphene import relay

from ...menu import models
from ..core.connection import CountableDjangoObjectType
from ..page.dataloaders import PageByIdLoader
from ..product.dataloaders import CategoryByIdLoader, CollectionByIdLoader
from ..translations.fields import TranslationField
from ..translations.types import MenuItemTranslation
from .dataloaders import (
    MenuByIdLoader,
    MenuItemByIdLoader,
    MenuItemChildrenLoader,
    MenuItemsByParentMenuLoader,
)


class Menu(CountableDjangoObjectType):
    items = graphene.List(lambda: MenuItem)

    class Meta:
        description = (
            "Represents a single menu - an object that is used to help navigate "
            "through the store."
        )
        interfaces = [relay.Node]
        only_fields = ["id", "name"]
        model = models.Menu

    @staticmethod
    def resolve_items(root: models.Menu, info, **_kwargs):
        return MenuItemsByParentMenuLoader(info.context).load(root.id)


class MenuItem(CountableDjangoObjectType):
    children = graphene.List(lambda: MenuItem)
    url = graphene.String(description="URL to the menu item.")
    translation = TranslationField(MenuItemTranslation, type_name="menu item")

    class Meta:
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
    def resolve_category(root: models.MenuItem, info, **_kwargs):
        if root.category_id:
            return CategoryByIdLoader(info.context).load(root.category_id)
        return None

    @staticmethod
    def resolve_children(root: models.MenuItem, info, **_kwargs):
        return MenuItemChildrenLoader(info.context).load(root.id)

    @staticmethod
    def resolve_collection(root: models.MenuItem, info, **_kwargs):
        if root.collection_id:
            return CollectionByIdLoader(info.context).load(root.collection_id)
        return None

    @staticmethod
    def resolve_menu(root: models.MenuItem, info, **_kwargs):
        if root.menu_id:
            return MenuByIdLoader(info.context).load(root.menu_id)
        return None

    @staticmethod
    def resolve_parent(root: models.MenuItem, info, **_kwargs):
        if root.parent_id:
            return MenuItemByIdLoader(info.context).load(root.parent_id)
        return None

    @staticmethod
    def resolve_page(root: models.MenuItem, info, **kwargs):
        if root.page_id:
            return PageByIdLoader(info.context).load(root.page_id)
        return None


class MenuItemMoveInput(graphene.InputObjectType):
    item_id = graphene.ID(description="The menu item ID to move.", required=True)
    parent_id = graphene.ID(
        description="ID of the parent menu. If empty, menu will be top level menu."
    )
    sort_order = graphene.Int(
        description="Sorting position of the menu item (from 0 to x)."
    )
