import graphene

from .....core.permissions import ProductPermissions
from .....product import models
from .....product.tasks import update_products_discounted_prices_of_catalogues_task
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.mutations import BaseMutation
from ....core.types import CollectionError, NonNullList
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Collection, Product


class CollectionRemoveProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection from which products will be removed."
    )

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        products = NonNullList(
            graphene.ID, required=True, description="List of product IDs."
        )

    class Meta:
        description = "Remove products from a collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, collection_id, products
    ):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(
            products,
            "products",
            only_type=Product,
            qs=models.Product.objects.prefetched_for_webhook(single_object=False),
        )
        collection.products.remove(*products)
        manager = get_plugin_manager_promise(info.context).get()
        for product in products:
            cls.call_event(manager.product_updated, product)
        if collection.sale_set.exists():
            # Updated the db entries, recalculating discounts of affected products
            update_products_discounted_prices_of_catalogues_task.delay(
                product_ids=[p.pk for p in products]
            )
        return CollectionRemoveProducts(
            collection=ChannelContext(node=collection, channel_slug=None)
        )
