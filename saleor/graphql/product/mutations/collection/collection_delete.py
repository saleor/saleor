import graphene

from .....core.permissions import ProductPermissions
from .....product import models
from ....channel import ChannelContext
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

    @classmethod
    def perform_mutation(cls, _root, info, **kwargs):
        node_id = kwargs.get("id")

        instance = cls.get_node_or_error(info, node_id, only_type=Collection)
        products = list(instance.products.prefetched_for_webhook(single_object=False))

        result = super().perform_mutation(_root, info, **kwargs)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.collection_deleted, instance)
        for product in products:
            cls.call_event(manager.product_updated, product)

        return CollectionDelete(
            collection=ChannelContext(node=result.collection, channel_slug=None)
        )
