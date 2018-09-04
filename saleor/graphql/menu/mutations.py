import graphene
from graphql_jwt.decorators import permission_required

from ...menu import models
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..product.types import Category, Collection
from ..page.types import Page
from .types import Menu


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
        description='Menu to which item belongs to.', name='menu')
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

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.manage_menus')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        items = []
        for item in cleaned_input.get('items', []):
            category = item.get('category')
            collection = item.get('collection')
            page = item.get('page')
            url = item.get('url')
            if len([i for i in [category, collection, page, url] if i]) > 1:
                cls.add_error(
                    errors, 'items', 'More than one item provided.')
            else:
                if category:
                    category = cls.get_node_or_error(
                        info, category, errors, 'items', only_type=Category)
                    item['category'] = category
                elif collection:
                    collection = cls.get_node_or_error(
                        info, collection, errors, 'items',
                        only_type=Collection)
                    item['collection'] = collection
                elif page:
                    page = cls.get_node_or_error(
                        info, page, errors, 'items', only_type=Page)
                    item['page'] = page
                elif not url:
                    cls.add_error(errors, 'items', 'No menu item provided.')
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

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.manage_menus')


class MenuDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a menu to delete.')

    class Meta:
        description = 'Deletes a menu.'
        model = models.Menu

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.manage_menus')


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

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.manage_menus')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        items = [
            cleaned_input.get('page'), cleaned_input.get('collection'),
            cleaned_input.get('url'), cleaned_input.get('category')]
        items = [item for item in items if item is not None]
        if len(items) > 1:
            cls.add_error(
                errors=errors,
                field='items', message='More than one item provided.')
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

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.manage_menus')

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

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.manage_menus')


class NavigationType(graphene.Enum):
    MAIN = 'main'
    SECONDARY = 'secondary'

    @property
    def description(self):
        if self == NavigationType.MAIN:
            return 'Main storefront\'s navigation.'
        return 'Secondary storefront\'s navigation.'


class AssignNavigation(BaseMutation):
    menu = graphene.Field(Menu, description='Assigned navigation menu.')

    class Arguments:
        menu = graphene.ID(
            description='ID of the menu.')
        navigation_type = NavigationType(
            description='Type of the navigation bar to assign the menu to.',
            required=True)

    class Meta:
        description = 'Assigns storefront\'s navigation menus.'

    @classmethod
    @permission_required(['menu.manage_menus', 'site.manage_settings'])
    def mutate(cls, root, info, navigation_type, menu=None):
        errors = []
        site_settings = info.context.site.settings
        if menu is not None:
            menu = cls.get_node_or_error(
                info, menu, errors=errors, field='menu')
        if not errors:
            if navigation_type == NavigationType.MAIN:
                site_settings.top_menu = menu
                site_settings.save(update_fields=['top_menu'])
            elif navigation_type == NavigationType.SECONDARY:
                site_settings.bottom_menu = menu
                site_settings.save(update_fields=['bottom_menu'])
            else:
                raise AssertionError(
                    'Unknown navigation type: %s' % navigation_type)
        return AssignNavigation(menu=menu, errors=errors)
