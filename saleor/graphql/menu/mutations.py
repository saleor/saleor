from collections import namedtuple
from typing import List

import graphene
from django.core.exceptions import ValidationError
from graphql_relay import from_global_id

from ...menu import models
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..page.types import Page
from ..product.types import Category, Collection
from .enums import NavigationType
from .types import Menu, MenuItem, MenuItemMoveInput


class MenuItemInput(graphene.InputObjectType):
    name = graphene.String(description='Name of the menu item.')
    url = graphene.String(description='URL of the pointed item.')
    category = graphene.ID(
        description='Category to which item points.', name='category')
    collection = graphene.ID(
        description='Collection to which item points.', name='collection')
    page = graphene.ID(
        description='Page to which item points.', name='page')


class MenuItemCreateInput(MenuItemInput):
    menu = graphene.ID(
        description='Menu to which item belongs to.', name='menu',
        required=True)
    parent = graphene.ID(
        description='''
        ID of the parent menu. If empty, menu will be top level
        menu.''',
        name='parent')


class MenuInput(graphene.InputObjectType):
    name = graphene.String(description='Name of the menu.')


class MenuCreateInput(MenuInput):
    items = graphene.List(
        MenuItemInput, description='List of menu items.')


class MenuCreate(ModelMutation):
    class Arguments:
        input = MenuCreateInput(
            required=True,
            description='Fields required to create a menu.')

    class Meta:
        description = 'Creates a new Menu'
        model = models.Menu
        permissions = ('menu.manage_menus', )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        items = []
        for item in cleaned_input.get('items', []):
            category = item.get('category')
            collection = item.get('collection')
            page = item.get('page')
            url = item.get('url')
            if len([i for i in [category, collection, page, url] if i]) > 1:
                raise ValidationError(
                    {'items': 'More than one item provided.'})

            if category:
                category = cls.get_node_or_error(
                    info, category, field='items', only_type=Category)
                item['category'] = category
            elif collection:
                collection = cls.get_node_or_error(
                    info, collection, field='items', only_type=Collection)
                item['collection'] = collection
            elif page:
                page = cls.get_node_or_error(
                    info, page, field='items', only_type=Page)
                item['page'] = page
            elif not url:
                raise ValidationError({'items': 'No menu item provided.'})
            items.append(item)

        cleaned_input['items'] = items
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        items = cleaned_data.get('items', [])
        for item in items:
            instance.items.create(**item)


class MenuUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a menu to update.')
        input = MenuInput(
            required=True,
            description='Fields required to update a menu.')

    class Meta:
        description = 'Updates a menu.'
        model = models.Menu
        permissions = ('menu.manage_menus', )


class MenuDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a menu to delete.')

    class Meta:
        description = 'Deletes a menu.'
        model = models.Menu
        permissions = ('menu.manage_menus', )


class MenuItemCreate(ModelMutation):
    class Arguments:
        input = MenuItemCreateInput(
            required=True,
            description="""Fields required to update a menu item.
            Only one of 'url', 'category', 'page', 'collection' is allowed
            per item""")

    class Meta:
        description = 'Creates a new Menu'
        model = models.MenuItem
        permissions = ('menu.manage_menus', )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        items = [
            cleaned_input.get('page'), cleaned_input.get('collection'),
            cleaned_input.get('url'), cleaned_input.get('category')]
        items = [item for item in items if item is not None]
        if len(items) > 1:
            raise ValidationError({'items': 'More than one item provided.'})
        return cleaned_input


class MenuItemUpdate(MenuItemCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a menu item to update.')
        input = MenuItemInput(
            required=True,
            description="""Fields required to update a menu item.
            Only one of 'url', 'category', 'page', 'collection' is allowed
            per item""")

    class Meta:
        description = 'Updates a menu item.'
        model = models.MenuItem
        permissions = ('menu.manage_menus', )

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # Only one item can be assigned per menu item
        instance.page = None
        instance.collection = None
        instance.category = None
        instance.url = None
        return super().construct_instance(instance, cleaned_data)


class MenuItemDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a menu item to delete.')

    class Meta:
        description = 'Deletes a menu item.'
        model = models.MenuItem
        permissions = ('menu.manage_menus', )


_MenuMoveOperation = namedtuple(
    '_MenuMoveOperation', ('menu_item', 'parent', 'sort_order'))


class MenuItemMove(BaseMutation):
    menu = graphene.Field(
        Menu, description='Assigned menu to move within.')

    class Arguments:
        menu = graphene.ID(
            required=True, description='ID of the menu.')
        moves = graphene.List(
            MenuItemMoveInput,
            required=True, description='The menu position data')

    class Meta:
        description = 'Moves items of menus'
        permissions = ('menu.manage_menus', )

    @staticmethod
    def clean_move(move):
        """Validate if the given move could be possibly possible."""
        if move.parent_id:
            if move.item_id == move.parent_id:
                raise ValidationError({
                    'parent': 'Cannot assign a node to itself.'})

    @staticmethod
    def clean_operation(operation: _MenuMoveOperation):
        """Validate if the given move will be actually possible."""

        if operation.parent:
            if operation.menu_item.is_ancestor_of(operation.parent):
                raise ValidationError({
                    'parent': (
                        'Cannot assign a node as child of '
                        'one of its descendants.')})

    @classmethod
    def get_operation(
            cls, info, menu_id: int, move) -> _MenuMoveOperation:
        parent_node = None

        _type, menu_item_id = from_global_id(move.item_id)  # type: str, int
        assert _type == 'MenuItem', \
            'The menu item node must be of type MenuItem.'

        menu_item = models.MenuItem.objects.get(
            pk=menu_item_id, menu_id=menu_id)

        if move.parent_id is not None:
            parent_node = cls.get_node_or_error(
                info, move.parent_id,
                field='parent_id', only_type=MenuItem)

        return _MenuMoveOperation(
            menu_item=menu_item,
            parent=parent_node,
            sort_order=move.sort_order)

    @classmethod
    def clean_moves(
            cls,
            info,
            menu_id: int,
            move_operations: List) -> List[_MenuMoveOperation]:

        operations = []
        for move in move_operations:
            cls.clean_move(move)
            operation = cls.get_operation(info, menu_id, move)
            cls.clean_operation(operation)
            operations.append(operation)
        return operations

    @staticmethod
    def perform_operation(operation: _MenuMoveOperation):
        menu_item = operation.menu_item  # type: models.MenuItem

        # Move the parent if provided
        if operation.parent:
            menu_item.move_to(operation.parent)
        # Remove the menu item's parent if was set to none (root node)
        elif menu_item.parent_id:
            menu_item.parent_id = None

        # Move the menu item
        if operation.sort_order is not None:
            menu_item.sort_order = operation.sort_order

        menu_item.save()

    @classmethod
    def perform_mutation(cls, root, info, menu, moves):
        _type, menu_id = from_global_id(menu)  # type: str, int
        assert _type == 'Menu', 'Expected a menu of type Menu'

        operations = cls.clean_moves(info, menu_id, moves)

        for operation in operations:
            cls.perform_operation(operation)

        return cls(menu=models.Menu.objects.get(pk=menu_id))


class AssignNavigation(BaseMutation):
    menu = graphene.Field(Menu, description='Assigned navigation menu.')

    class Arguments:
        menu = graphene.ID(description='ID of the menu.')
        navigation_type = NavigationType(
            description='Type of the navigation bar to assign the menu to.',
            required=True)

    class Meta:
        description = 'Assigns storefront\'s navigation menus.'
        permissions = ('menu.manage_menus', 'site.manage_settings')

    @classmethod
    def perform_mutation(cls, _root, info, navigation_type, menu=None):
        site_settings = info.context.site.settings
        if menu is not None:
            menu = cls.get_node_or_error(info, menu, field='menu')

        if navigation_type == NavigationType.MAIN:
            site_settings.top_menu = menu
            site_settings.save(update_fields=['top_menu'])
        elif navigation_type == NavigationType.SECONDARY:
            site_settings.bottom_menu = menu
            site_settings.save(update_fields=['bottom_menu'])

        return AssignNavigation(menu=menu)
