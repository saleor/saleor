import graphene

from ...menu import models
from ..core.mutations import ModelDeleteMutation, ModelMutation


class MenuInput(graphene.InputObjectType):
    name = graphene.String(description='Name of the menu.')


class MenuItemInput(graphene.InputObjectType):
    menu = graphene.ID(description='Menu to which item belongs to.')
    name = graphene.String(description='Name of the menu item.')
    parent = graphene.ID(description='''
        ID of the parent menu. If empty, menu will be top level
        menu.''')
    url = graphene.String(description='URL of the pointed item.')
    category = graphene.ID(description='Category to which item points.')
    collection = graphene.ID(description='Collection to which item points.')
    page = graphene.ID(description='Page to which item points.')


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
        return user.has_perm('menu.edit_menu')


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
        return user.has_perm('menu.edit_menu')


class MenuDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a menu to delete.')

    class Meta:
        description = 'Deletes a menu.'
        model = models.Menu

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('menu.edit_menu')


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
        return user.has_perm('menu.edit_menu')

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
        return user.has_perm('menu.edit_menu')

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
        return user.has_perm('menu.edit_menu')
