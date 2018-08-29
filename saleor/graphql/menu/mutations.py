import graphene
from graphql_jwt.decorators import permission_required

from ...menu import models
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from .types import Menu


class MenuInput(graphene.InputObjectType):
    name = graphene.String(description='Name of the menu.')


class MenuItemInput(graphene.InputObjectType):
    menu = graphene.ID(
        description='Menu to which item belongs to.', name='menu')
    name = graphene.String(description='Name of the menu item.')
    parent = graphene.ID(
        description='''
        ID of the parent menu. If empty, menu will be top level
        menu.''',
        name='parent')
    url = graphene.String(description='URL of the pointed item.')
    category = graphene.ID(
        description='Category to which item points.', name='category')
    collection = graphene.ID(
        description='Collection to which item points.', name='collection')
    page = graphene.ID(
        description='Page to which item points.', name='page')


class MenuCreate(ModelMutation):
    class Arguments:
        input = MenuInput(
            required=True,
            description='Fields required to create a menu.')

    class Meta:
        description = 'Creates a new Menu'
        model = models.Menu

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.manage_menus')


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
        input = MenuItemInput(
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
