import graphene

from ...core.permissions import PagePermissions
from ...page import models
from ..core.mutations import BaseBulkMutation, ModelBulkDeleteMutation
from ..core.types.common import PageError


class PageBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of page IDs to delete."
        )

    class Meta:
        description = "Deletes pages."
        model = models.Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"


class PageBulkPublish(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of page IDs to (un)publish."
        )
        is_published = graphene.Boolean(
            required=True, description="Determine if pages will be published or not."
        )

    class Meta:
        description = "Publish pages."
        model = models.Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def bulk_action(cls, queryset, is_published):
        queryset.update(is_published=is_published)
