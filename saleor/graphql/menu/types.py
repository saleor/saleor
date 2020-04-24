import graphene
from graphene import relay

from ...menu import models
from ..core.connection import CountableDjangoObjectType
from ..translations.fields import TranslationField
from ..translations.types import MenuItemTranslation


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
    def resolve_items(root: models.Menu, _info, **_kwargs):
        if hasattr(root, "prefetched_items"):
            return root.prefetched_items  # type: ignore
        return root.items.filter(level=0)


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
    def resolve_children(root: models.MenuItem, _info, **_kwargs):
        return root.children.all()


class MenuItemMoveInput(graphene.InputObjectType):
    item_id = graphene.ID(description="The menu item ID to move.", required=True)
    parent_id = graphene.ID(
        description="ID of the parent menu. If empty, menu will be top level menu."
    )
    sort_order = graphene.Int(
        description="Sorting position of the menu item (from 0 to x)."
    )
