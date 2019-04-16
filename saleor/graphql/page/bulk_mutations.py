import graphene

from ...page import models
from ..core.mutations import BaseBulkMutation, ModelBulkDeleteMutation


class PageBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of page IDs to delete.')

    class Meta:
        description = 'Deletes pages.'
        model = models.Page

    @classmethod
    def user_is_allowed(cls, user, _ids):
        return user.has_perm('page.manage_pages')


class PageBulkPublish(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of page IDs to (un)publish.')
        is_published = graphene.Boolean(
            required=True,
            description='Determine if pages will be published or not.')

    class Meta:
        description = 'Publish pages.'
        model = models.Page

    @classmethod
    def user_is_allowed(cls, user, _ids):
        return user.has_perm('page.manage_pages')

    @classmethod
    def bulk_action(cls, queryset, is_published):
        queryset.update(is_published=is_published)
