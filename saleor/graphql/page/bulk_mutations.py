import graphene

from ...page import models
from ..core.mutations import ModelBulkDeleteMutation, ModelBulkPublishMutation


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


class PageBulkPublish(ModelBulkPublishMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of page IDs to publish.')

    class Meta:
        description = 'Publish pages.'
        model = models.Page

    @classmethod
    def user_is_allowed(cls, user, _ids):
        return user.has_perm('page.manage_pages')


class PageBulkUnpublish(PageBulkPublish):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of page IDs to unpublish.')

    class Meta:
        description = 'Unpublish pages.'
        model = models.Page

    @classmethod
    def bulk_action(cls, queryset):
        queryset.update(is_published=False)
