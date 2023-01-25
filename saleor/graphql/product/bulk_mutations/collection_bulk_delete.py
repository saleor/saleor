import graphene

from ....permission.enums import ProductPermissions
from ....product import models
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import CollectionError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Collection


class CollectionBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of collection IDs to delete."
        )

    class Meta:
        description = "Deletes collections."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def bulk_action(cls, info, queryset):
        collections_ids = queryset.values_list("id", flat=True)
        products = list(
            models.Product.objects.prefetched_for_webhook(single_object=False)
            .filter(collections__in=collections_ids)
            .distinct()
        )
        manager = get_plugin_manager_promise(info.context).get()
        for collection in queryset.iterator():
            manager.collection_deleted(collection)
        queryset.delete()

        for product in products:
            manager.product_updated(product)
