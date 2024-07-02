import graphene

from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.tasks import collection_product_updated_task
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.mutations import ModelDeleteMutation
from ....core.types import CollectionError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Collection

# Batch size of 25k ids, assuming their pks are at least 7 digits each
# after json serialization, weights 225kB of payload.
PRODUCTS_BATCH_SIZE = 25000


class CollectionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to delete.")

    class Meta:
        description = "Deletes a collection."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @staticmethod
    def batch_product_ids(ids):
        _length = len(ids)
        for i in range(0, _length, PRODUCTS_BATCH_SIZE):
            yield ids[i : i + PRODUCTS_BATCH_SIZE]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        instance = cls.get_node_or_error(info, id, only_type=Collection)
        product_ids = list(instance.products.values_list("id", flat=True))

        result = super().perform_mutation(_root, info, id=id)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.collection_deleted, instance)

        for ids_batch in cls.batch_product_ids(product_ids):
            collection_product_updated_task.delay(ids_batch)

        if product_ids:
            channel_ids = set(
                models.ProductChannelListing.objects.filter(
                    product_id__in=product_ids
                ).values_list("channel_id", flat=True)
            )
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

        return CollectionDelete(
            collection=ChannelContext(node=result.collection, channel_slug=None)
        )
