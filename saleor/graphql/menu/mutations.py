from dataclasses import dataclass
from typing import Dict, List, Optional, Type

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Model

from ...core.permissions import MenuPermissions, SitePermissions
from ...core.tracing import traced_atomic_transaction
from ...menu import models
from ...menu.error_codes import MenuErrorCode
from ...page import models as page_models
from ...product import models as product_models
from ..channel import ChannelContext
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import MenuError, NonNullList
from ..core.utils.reordering import perform_reordering
from ..core.validators import validate_slug_and_generate_if_needed
from ..page.types import Page
from ..plugins.dataloaders import load_plugin_manager
from ..product.types import Category, Collection
from ..site.dataloaders import get_site_promise
from .dataloaders import MenuItemsByParentMenuLoader
from .enums import NavigationType
from .types import Menu, MenuItem, MenuItemMoveInput


class MenuItemInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu item.")
    url = graphene.String(description="URL of the pointed item.")
    category = graphene.ID(
        description="Category to which item points.", name="category"
    )
    collection = graphene.ID(
        description="Collection to which item points.", name="collection"
    )
    page = graphene.ID(description="Page to which item points.", name="page")


class MenuItemCreateInput(MenuItemInput):
    name = graphene.String(description="Name of the menu item.", required=True)
    menu = graphene.ID(
        description="Menu to which item belongs.", name="menu", required=True
    )
    parent = graphene.ID(
        description="ID of the parent menu. If empty, menu will be top level menu.",
        name="parent",
    )


class MenuCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu.", required=True)
    slug = graphene.String(
        description="Slug of the menu. Will be generated if not provided.",
        required=False,
    )
    items = NonNullList(MenuItemInput, description="List of menu items.")


class MenuCreate(ModelMutation):
    class Arguments:
        input = MenuCreateInput(
            required=True, description="Fields required to create a menu."
        )

    class Meta:
        description = "Creates a new Menu."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = MenuErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        items = []
        for item in cleaned_input.get("items", []):
            category = item.get("category")
            collection = item.get("collection")
            page = item.get("page")
            url = item.get("url")
            if len([i for i in [category, collection, page, url] if i]) > 1:
                raise ValidationError(
                    {
                        "items": ValidationError(
                            "More than one item provided.",
                            code=MenuErrorCode.TOO_MANY_MENU_ITEMS,
                        )
                    }
                )

            if category:
                category = cls.get_node_or_error(
                    info, category, field="items", only_type=Category
                )
                item["category"] = category
            elif collection:
                collection = cls.get_node_or_error(
                    info, collection, field="items", only_type=Collection
                )
                item["collection"] = collection
            elif page:
                page = cls.get_node_or_error(info, page, field="items", only_type=Page)
                item["page"] = page
            elif not url:
                raise ValidationError(
                    {
                        "items": ValidationError(
                            "No menu item provided.",
                            code=MenuErrorCode.NO_MENU_ITEM_PROVIDED,
                        )
                    }
                )
            items.append(item)
        cleaned_input["items"] = items
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        items = cleaned_data.get("items", [])
        for item in items:
            instance.items.create(**item)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.menu_created, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)


class MenuInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu.")
    slug = graphene.String(description="Slug of the menu.", required=False)


class MenuUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu to update.")
        input = MenuInput(
            required=True, description="Fields required to update a menu."
        )

    class Meta:
        description = "Updates a menu."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.menu_updated, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)


class MenuDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu to delete.")

    class Meta:
        description = "Deletes a menu."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.menu_deleted, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)


def _validate_menu_item_instance(
    cleaned_input: dict, field: str, expected_model: Type[Model]
):
    """Check if the value to assign as a menu item matches the expected model."""
    item = cleaned_input.get(field)
    if item:
        if not isinstance(item, expected_model):
            msg = (
                f"Enter a valid {expected_model._meta.verbose_name} ID "
                f"(got {item._meta.verbose_name} ID)."
            )
            raise ValidationError(
                {
                    field: ValidationError(
                        msg, code=MenuErrorCode.INVALID_MENU_ITEM.value
                    )
                }
            )


class MenuItemCreate(ModelMutation):
    class Arguments:
        input = MenuItemCreateInput(
            required=True,
            description=(
                "Fields required to update a menu item. Only one of `url`, `category`, "
                "`page`, `collection` is allowed per item."
            ),
        )

    class Meta:
        description = "Creates a new menu item."
        model = models.MenuItem
        object_type = MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.menu_item_created, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        _validate_menu_item_instance(cleaned_input, "page", page_models.Page)
        _validate_menu_item_instance(
            cleaned_input, "collection", product_models.Collection
        )
        _validate_menu_item_instance(cleaned_input, "category", product_models.Category)

        items = [
            cleaned_input.get("page"),
            cleaned_input.get("collection"),
            cleaned_input.get("url"),
            cleaned_input.get("category"),
        ]
        items = [item for item in items if item is not None]
        if len(items) > 1:
            raise ValidationError(
                "More than one item provided.", code=MenuErrorCode.TOO_MANY_MENU_ITEMS
            )
        return cleaned_input


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
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.menu_item_updated, instance)


class MenuItemDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu item to delete.")

    class Meta:
        description = "Deletes a menu item."
        model = models.MenuItem
        object_type = MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.menu_item_deleted, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)


@dataclass(frozen=True)
class _MenuMoveOperation:
    menu_item: models.MenuItem
    parent_changed: bool
    new_parent: Optional[models.MenuItem]
    sort_order: int


class MenuItemMove(BaseMutation):
    menu = graphene.Field(Menu, description="Assigned menu to move within.")

    class Arguments:
        menu = graphene.ID(required=True, description="ID of the menu.")
        moves = NonNullList(
            MenuItemMoveInput, required=True, description="The menu position data."
        )

    class Meta:
        description = "Moves items of menus."
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @staticmethod
    def clean_move(move: MenuItemMoveInput):
        """Validate if the given move could be possibly possible."""
        if move.parent_id:
            if move.item_id == move.parent_id:
                raise ValidationError(
                    {
                        "parent_id": ValidationError(
                            "Cannot assign a node to itself.",
                            code=MenuErrorCode.CANNOT_ASSIGN_NODE.value,
                        )
                    }
                )

    @staticmethod
    def clean_operation(operation: _MenuMoveOperation):
        """Validate if the given move will be actually possible."""

        if operation.new_parent is not None:
            if operation.menu_item.is_ancestor_of(operation.new_parent):
                raise ValidationError(
                    {
                        "parent_id": ValidationError(
                            (
                                "Cannot assign a node as child of "
                                "one of its descendants."
                            ),
                            code=MenuErrorCode.CANNOT_ASSIGN_NODE.value,
                        )
                    }
                )

    @classmethod
    def get_operation(
        cls,
        info,
        menu_item_to_current_parent,
        menu: models.Menu,
        move: MenuItemMoveInput,
    ) -> _MenuMoveOperation:
        menu_item = cls.get_node_or_error(
            info, move.item_id, field="item", only_type="MenuItem", qs=menu.items
        )
        new_parent, parent_changed = None, False

        # we want to check if parent has changes in relation to previous operations
        # as moves are performed sequentially
        old_parent_id = (
            menu_item_to_current_parent[menu_item.pk]
            if menu_item.pk in menu_item_to_current_parent
            else menu_item.parent_id
        )

        if move.parent_id is not None:
            parent_pk = cls.get_global_id_or_error(
                move.parent_id, only_type=MenuItem, field="parent_id"
            )
            if int(parent_pk) != old_parent_id:
                new_parent = cls.get_node_or_error(
                    info,
                    move.parent_id,
                    field="parent_id",
                    only_type=MenuItem,
                    qs=menu.items,
                )
                parent_changed = True
        elif move.parent_id is None and old_parent_id is not None:
            parent_changed = True

        return _MenuMoveOperation(
            menu_item=menu_item,
            new_parent=new_parent,
            parent_changed=parent_changed,
            sort_order=move.sort_order,
        )

    @classmethod
    def clean_moves(
        cls, info, menu: models.Menu, move_operations: List[MenuItemMoveInput]
    ) -> List[_MenuMoveOperation]:
        operations = []
        item_to_current_parent: Dict[int, Optional[models.MenuItem]] = {}
        for move in move_operations:
            cls.clean_move(move)
            operation = cls.get_operation(info, item_to_current_parent, menu, move)
            if operation.parent_changed:
                cls.clean_operation(operation)
                item_to_current_parent[operation.menu_item.id] = operation.new_parent
            operations.append(operation)
        return operations

    @staticmethod
    def perform_change_parent_operation(operation: _MenuMoveOperation):
        menu_item = operation.menu_item

        if not operation.parent_changed:
            return

        # we need to refresh item, as it might be changes in previous operations
        # and in such case the parent and level values are invalid
        menu_item.refresh_from_db()

        # parent cache need to be update in case of the item parent is changed
        # more than once
        menu_item._mptt_meta.update_mptt_cached_fields(menu_item)

        # Move the parent
        menu_item.parent = operation.new_parent
        menu_item.sort_order = None
        menu_item.save()

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        menu: str = data["menu"]
        moves: List[MenuItemMoveInput] = data["moves"]
        qs = models.Menu.objects.prefetch_related("items")
        menu = cls.get_node_or_error(info, menu, only_type=Menu, field="menu", qs=qs)

        operations = cls.clean_moves(info, menu, moves)
        manager = load_plugin_manager(info.context)
        with traced_atomic_transaction():
            for operation in operations:
                cls.perform_change_parent_operation(operation)

                menu_item = operation.menu_item

                if operation.sort_order:
                    perform_reordering(
                        menu_item.get_ordering_queryset(),
                        {menu_item.pk: operation.sort_order},
                    )

                if operation.sort_order or operation.parent_changed:
                    cls.call_event(manager.menu_item_updated, menu_item)

        menu = qs.get(pk=menu.pk)
        MenuItemsByParentMenuLoader(info.context).clear(menu.id)
        return MenuItemMove(menu=ChannelContext(node=menu, channel_slug=None))


class AssignNavigation(BaseMutation):
    menu = graphene.Field(Menu, description="Assigned navigation menu.")

    class Arguments:
        menu = graphene.ID(description="ID of the menu.")
        navigation_type = NavigationType(
            description="Type of the navigation bar to assign the menu to.",
            required=True,
        )

    class Meta:
        description = "Assigns storefront's navigation menus."
        permissions = (MenuPermissions.MANAGE_MENUS, SitePermissions.MANAGE_SETTINGS)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def perform_mutation(cls, _root, info, navigation_type, menu=None):
        site = get_site_promise(info.context).get()
        if menu is not None:
            menu = cls.get_node_or_error(info, menu, field="menu", only_type=Menu)

        if navigation_type == NavigationType.MAIN:
            site.settings.top_menu = menu
            site.settings.save(update_fields=["top_menu"])
        elif navigation_type == NavigationType.SECONDARY:
            site.settings.bottom_menu = menu
            site.settings.save(update_fields=["bottom_menu"])

        if menu is None:
            return AssignNavigation(menu=None)
        return AssignNavigation(menu=ChannelContext(node=menu, channel_slug=None))
