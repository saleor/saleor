import graphene

from .....discount.utils import get_active_promotion_rules
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.tasks import collection_product_updated_task
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.mutations import ModelDeleteMutation
from ....core.types import CollectionError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Collection


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
        # Batch size of 25k ids, assuming their pks are at least 7 digits each
        # after json serialization, weights 225kB of payload.
        BATCH_SIZE = 25000
        _length = len(ids)
        for i in range(0, _length, BATCH_SIZE):
            yield ids[i : min(i + BATCH_SIZE, _length)]

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
        rules = get_active_promotion_rules()
        rules.update(variants_dirty=True)

        return CollectionDelete(
            collection=ChannelContext(node=result.collection, channel_slug=None)
        )
