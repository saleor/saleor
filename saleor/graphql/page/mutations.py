import graphene

from ...page import models
from ..core.mutations import ModelMutation, ModelDeleteMutation


class PageInput(graphene.InputObjectType):
    slug = graphene.String()
    title = graphene.String()
    content = graphene.String()
    is_visible = graphene.Boolean()
    available_on = graphene.String()


class PageCreate(ModelMutation):
    class Arguments:
        input = PageInput(
            required=True, description='Fields required to create a page.')

    class Meta:
        description = 'Creates a new page.'
        model = models.Page

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('page.edit_page')


class PageUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description='ID of a page to update.')
        input = PageInput(
            required=True, description='Fields required to update a page.')

    class Meta:
        description = 'Updates an existing page.'
        model = models.Page

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('page.edit_page')


class PageDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description='ID of a page to delete.')

    class Meta:
        description = 'Deletes a page.'
        model = models.Page

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('page.edit_page')
